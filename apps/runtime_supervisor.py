from __future__ import annotations

import ctypes
import json
import os
import signal
import socket
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import IO

try:
    import winreg
except ImportError:  # pragma: no cover - Windows runtime only
    winreg = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / ".warlock" / "runtime"
VENV_DIR = PROJECT_ROOT / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
VENV_SITE_PACKAGES = VENV_DIR / "Lib" / "site-packages"
RUNTIME_CHILD = PROJECT_ROOT / "apps" / "runtime_child.py"
CLOUDFLARED = PROJECT_ROOT / "infrastructure" / "cloudflare" / "cloudflared.exe"
CLOUDFLARE_CONFIG = PROJECT_ROOT / "infrastructure" / "cloudflare" / "config" / "config.yml"
SUPERVISOR_LOG = RUNTIME_DIR / "supervisor.log"
SUPERVISOR_PID = RUNTIME_DIR / "supervisor.pid"
BOOTSTRAP_LOG = RUNTIME_DIR / "supervisor.bootstrap.log"
HEALTH_FAILURE_THRESHOLD = 3
HEALTH_CHECK_INTERVAL_SECONDS = 5


if os.name == "nt":
    from ctypes import wintypes

    PROCESS_TERMINATE = 0x0001
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    SYNCHRONIZE = 0x00100000
    WAIT_TIMEOUT = 0x00000102

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    kernel32.GetModuleFileNameW.restype = wintypes.DWORD
else:
    kernel32 = None


def physical_python_executable() -> Path:
    """Return the actual running Windows Python image, bypassing the venv launcher."""
    if os.name != "nt" or kernel32 is None:
        return Path(sys.executable).resolve()

    buffer = ctypes.create_unicode_buffer(32768)
    length = kernel32.GetModuleFileNameW(None, buffer, len(buffer))
    if not length:
        return Path(sys.executable).resolve()
    return Path(buffer.value)


RUNTIME_PYTHON = physical_python_executable()


@dataclass(frozen=True)
class Service:
    name: str
    command: tuple[str, ...]
    port: int | None = None
    health_path: str | None = None
    identity_key: str | None = None
    identity_value: str | None = None
    expected_executable: Path | None = None


@dataclass
class ManagedProcess:
    pid: int
    popen: subprocess.Popen[bytes] | None = None
    adopted: bool = False

    def poll(self) -> int | None:
        if self.popen is not None:
            return self.popen.poll()
        return None if process_is_alive(self.pid) else 1


SERVICES = (
    Service(
        "agent",
        (
            str(RUNTIME_PYTHON),
            "-S",
            "-m",
            "apps.runtime_child",
            "apps.local_agent.run_agent",
        ),
        port=8765,
        health_path="/health",
        identity_key="agent",
        identity_value="Warlock Local Agent",
        expected_executable=RUNTIME_PYTHON,
    ),
    Service(
        "gateway",
        (
            str(RUNTIME_PYTHON),
            "-S",
            "-m",
            "apps.runtime_child",
            "uvicorn",
            "apps.gateway.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8780",
        ),
        port=8780,
        health_path="/health",
        identity_key="gateway",
        identity_value="warlock",
        expected_executable=RUNTIME_PYTHON,
    ),
    Service(
        "mcp",
        (
            str(RUNTIME_PYTHON),
            "-S",
            "-m",
            "apps.runtime_child",
            "apps.mcp_server.run_mcp",
        ),
        port=8790,
        health_path="/health",
        identity_key="service",
        identity_value="warlock-mcp",
        expected_executable=RUNTIME_PYTHON,
    ),
    Service(
        "tunnel",
        (
            str(CLOUDFLARED),
            "tunnel",
            "--config",
            str(CLOUDFLARE_CONFIG),
            "run",
            "warlock-agent",
        ),
        expected_executable=CLOUDFLARED,
    ),
)


def bootstrap_log(message: str) -> None:
    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with BOOTSTRAP_LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] PID {os.getpid()} | {message}\n")
    except BaseException:
        pass


def log(message: str) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with SUPERVISOR_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def user_environment_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    if winreg is not None:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                value, _ = winreg.QueryValueEx(key, name)
                value = str(value).strip()
                if value:
                    return value
        except OSError:
            pass
    raise RuntimeError(f"Required user environment variable is missing: {name}")


def is_listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except OSError:
        return False


def is_service_healthy(service: Service) -> bool:
    if service.port is None or service.health_path is None:
        return False

    url = f"http://127.0.0.1:{service.port}{service.health_path}"
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "WarlockRuntimeSupervisor/1"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=0.8) as response:
            if response.status != 200:
                return False
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
        return False

    if payload.get("status") != "healthy":
        return False
    if service.identity_key is not None:
        return payload.get(service.identity_key) == service.identity_value
    return True


def open_log(name: str, suffix: str) -> IO[bytes]:
    path = RUNTIME_DIR / f"{name}.{suffix}.log"
    return path.open("ab", buffering=0)


def pid_path(name: str) -> Path:
    return RUNTIME_DIR / f"{name}.pid"


def read_pid(name: str) -> int | None:
    try:
        value = pid_path(name).read_text(encoding="ascii").strip()
        pid = int(value)
        return pid if pid > 0 else None
    except (FileNotFoundError, OSError, ValueError):
        return None


def remove_pid(name: str) -> None:
    try:
        pid_path(name).unlink()
    except FileNotFoundError:
        pass


def process_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False

    if os.name != "nt" or kernel32 is None:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return False
    try:
        return kernel32.WaitForSingleObject(handle, 0) == WAIT_TIMEOUT
    finally:
        kernel32.CloseHandle(handle)


def process_image_path(pid: int) -> Path | None:
    if pid <= 0:
        return None

    if os.name != "nt" or kernel32 is None:
        try:
            return Path(f"/proc/{pid}/exe").resolve()
        except OSError:
            return None

    access = PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE
    handle = kernel32.OpenProcess(access, False, pid)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        success = kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size))
        if not success:
            return None
        return Path(buffer.value)
    finally:
        kernel32.CloseHandle(handle)


def terminate_pid(pid: int) -> None:
    if pid <= 0 or not process_is_alive(pid):
        return

    if os.name != "nt" or kernel32 is None:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        return

    handle = kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
    if not handle:
        return
    try:
        kernel32.TerminateProcess(handle, 1)
        kernel32.WaitForSingleObject(handle, 4000)
    finally:
        kernel32.CloseHandle(handle)


def path_matches(left: Path | None, right: Path | None) -> bool:
    if left is None or right is None:
        return False
    try:
        left_text = str(left.resolve())
    except OSError:
        left_text = str(left)
    try:
        right_text = str(right.resolve())
    except OSError:
        right_text = str(right)
    if os.name == "nt":
        return left_text.casefold() == right_text.casefold()
    return left_text == right_text


def adopt_existing_process(service: Service) -> ManagedProcess | None:
    pid = read_pid(service.name)
    if pid is None or not process_is_alive(pid):
        if pid is not None:
            remove_pid(service.name)
        return None

    if service.expected_executable is not None:
        actual = process_image_path(pid)
        if not path_matches(actual, service.expected_executable):
            log(
                f"Refusing stale PID ownership for {service.name}: PID {pid} executable "
                f"{actual or 'unknown'} does not match {service.expected_executable}."
            )
            remove_pid(service.name)
            return None

    if service.port is not None and not is_service_healthy(service):
        return None

    log(f"Adopted existing Warlock service: {service.name} (PID {pid})")
    return ManagedProcess(pid=pid, popen=None, adopted=True)


def child_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(VENV_DIR)
    env["PATH"] = str(VENV_DIR / "Scripts") + os.pathsep + env.get("PATH", "")
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    python_paths = [str(PROJECT_ROOT)]
    existing = env.get("PYTHONPATH", "").strip()
    if existing:
        python_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    return env


def start_service(service: Service) -> ManagedProcess:
    adopted = adopt_existing_process(service)
    if adopted is not None:
        return adopted

    if service.port is not None:
        if is_service_healthy(service):
            raise RuntimeError(
                f"Healthy Warlock listener exists on 127.0.0.1:{service.port} but no valid owned PID is available"
            )
        if is_listening(service.port):
            raise RuntimeError(
                f"Port 127.0.0.1:{service.port} is occupied but failed Warlock identity/health checks"
            )

    stdout = open_log(service.name, "out")
    stderr = open_log(service.name, "err")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        log(f"Starting service: {service.name} | executable={service.command[0]}")
        process = subprocess.Popen(
            service.command,
            cwd=PROJECT_ROOT,
            env=child_environment(),
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=creationflags,
        )
    except Exception:
        stdout.close()
        stderr.close()
        raise

    pid_path(service.name).write_text(str(process.pid), encoding="ascii")
    log(f"Started service: {service.name} (PID {process.pid})")
    return ManagedProcess(pid=process.pid, popen=process, adopted=False)


def stop_process(process: ManagedProcess | None) -> None:
    if process is None or process.poll() is not None:
        return

    if process.popen is not None:
        try:
            process.popen.terminate()
            process.popen.wait(timeout=4)
            return
        except Exception:
            try:
                process.popen.kill()
                return
            except Exception:
                pass

    terminate_pid(process.pid)


def restart_service(service: Service, process: ManagedProcess | None) -> ManagedProcess:
    stop_process(process)
    remove_pid(service.name)
    time.sleep(1)
    return start_service(service)


def main() -> int:
    bootstrap_log("entered main")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    SUPERVISOR_PID.write_text(str(os.getpid()), encoding="ascii")
    bootstrap_log(f"wrote supervisor pid file: {SUPERVISOR_PID}")
    os.chdir(PROJECT_ROOT)

    for required in (VENV_PYTHON, VENV_SITE_PACKAGES, RUNTIME_CHILD, RUNTIME_PYTHON, CLOUDFLARED, CLOUDFLARE_CONFIG):
        if not required.exists():
            raise RuntimeError(f"Required runtime path not found: {required}")

    os.environ["WARLOCK_AGENT_TOKEN"] = user_environment_value("WARLOCK_AGENT_TOKEN")
    os.environ["WARLOCK_CF_TEAM_DOMAIN"] = user_environment_value("WARLOCK_CF_TEAM_DOMAIN")
    os.environ["WARLOCK_CF_ACCESS_AUD"] = user_environment_value("WARLOCK_CF_ACCESS_AUD")

    log(f"Supervisor starting. PID {os.getpid()}")
    log(f"Supervisor sys.executable: {sys.executable}")
    log(f"Child runtime interpreter: {RUNTIME_PYTHON}")
    log(f"Child bootstrap: {RUNTIME_CHILD}")
    log("Required files and user environment values validated.")

    processes: dict[str, ManagedProcess | None] = {}
    health_failures: dict[str, int] = {service.name: 0 for service in SERVICES}
    stopping = False

    def request_stop(*_: object) -> None:
        nonlocal stopping
        bootstrap_log("stop signal received")
        stopping = True

    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None), getattr(signal, "SIGBREAK", None)):
        if sig is not None:
            try:
                signal.signal(sig, request_stop)
            except (OSError, ValueError):
                pass

    try:
        for service in SERVICES:
            try:
                processes[service.name] = start_service(service)
            except Exception as exc:
                log(f"Failed to start service: {service.name} | {exc}")
                processes[service.name] = None
            time.sleep(1)

        while not stopping:
            time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
            for service in SERVICES:
                process = processes.get(service.name)

                if process is None:
                    if service.port is not None and is_listening(service.port) and not is_service_healthy(service):
                        health_failures[service.name] += 1
                        if health_failures[service.name] == 1 or health_failures[service.name] % 6 == 0:
                            log(
                                f"Health conflict: {service.name} port {service.port} is listening "
                                "but does not identify as the expected Warlock service."
                            )
                        continue

                    health_failures[service.name] = 0
                    try:
                        processes[service.name] = start_service(service)
                    except Exception as exc:
                        log(f"Failed to start service: {service.name} | {exc}")
                    continue

                exit_code = process.poll()
                if exit_code is not None:
                    remove_pid(service.name)
                    health_failures[service.name] = 0
                    log(f"Service exited: {service.name} (exit code {exit_code}). Error log: {service.name}.err.log")
                    time.sleep(1)
                    try:
                        processes[service.name] = start_service(service)
                    except Exception as exc:
                        log(f"Failed to restart service: {service.name} | {exc}")
                        processes[service.name] = None
                    continue

                if service.port is None:
                    continue

                if is_service_healthy(service):
                    health_failures[service.name] = 0
                    continue

                health_failures[service.name] += 1
                failures = health_failures[service.name]
                if failures == 1:
                    log(f"Service health check failed: {service.name}; waiting before restart.")
                if failures < HEALTH_FAILURE_THRESHOLD:
                    continue

                log(
                    f"Service unhealthy for {failures} consecutive checks: {service.name}; restarting owned process."
                )
                health_failures[service.name] = 0
                try:
                    processes[service.name] = restart_service(service, process)
                except Exception as exc:
                    log(f"Failed to recover service: {service.name} | {exc}")
                    processes[service.name] = None
    finally:
        bootstrap_log("entering shutdown cleanup")
        for service in SERVICES:
            stop_process(processes.get(service.name))
            remove_pid(service.name)
        try:
            SUPERVISOR_PID.unlink()
        except FileNotFoundError:
            pass
        log("Supervisor stopped.")

    return 0


def run() -> int:
    bootstrap_log(f"module run invoked | executable={sys.executable} | physical={RUNTIME_PYTHON} | cwd={Path.cwd()}")
    try:
        return main()
    except BaseException as exc:
        bootstrap_log(f"fatal {type(exc).__name__}: {exc}")
        try:
            log(f"Supervisor fatal error: {type(exc).__name__}: {exc}")
        except BaseException:
            pass
        try:
            SUPERVISOR_PID.unlink()
        except FileNotFoundError:
            pass
        except BaseException:
            pass
        if sys.stderr is not None:
            traceback.print_exc()
        raise


if __name__ == "__main__":
    bootstrap_log("__main__ reached")
    raise SystemExit(run())
