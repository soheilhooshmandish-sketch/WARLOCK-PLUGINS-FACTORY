from __future__ import annotations

import ctypes
import os
import signal
import socket
import subprocess
import sys
import time
import traceback
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
CLOUDFLARED = PROJECT_ROOT / "infrastructure" / "cloudflare" / "cloudflared.exe"
CLOUDFLARE_CONFIG = PROJECT_ROOT / "infrastructure" / "cloudflare" / "config" / "config.yml"
SUPERVISOR_LOG = RUNTIME_DIR / "supervisor.log"
SUPERVISOR_PID = RUNTIME_DIR / "supervisor.pid"
BOOTSTRAP_LOG = RUNTIME_DIR / "supervisor.bootstrap.log"


def physical_python_executable() -> Path:
    """Return the actual running Windows Python image, bypassing the venv launcher."""
    if os.name != "nt":
        return Path(sys.executable).resolve()

    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, len(buffer))
    if not length:
        return Path(sys.executable).resolve()
    return Path(buffer.value)


RUNTIME_PYTHON = physical_python_executable()


@dataclass(frozen=True)
class Service:
    name: str
    command: tuple[str, ...]
    port: int | None = None


SERVICES = (
    Service("agent", (str(RUNTIME_PYTHON), "-m", "apps.local_agent.run_agent"), 8765),
    Service(
        "gateway",
        (
            str(RUNTIME_PYTHON),
            "-m",
            "uvicorn",
            "apps.gateway.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8780",
        ),
        8780,
    ),
    Service("mcp", (str(RUNTIME_PYTHON), "-m", "apps.mcp_server.run_mcp"), 8790),
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
        None,
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


def open_log(name: str, suffix: str) -> IO[bytes]:
    path = RUNTIME_DIR / f"{name}.{suffix}.log"
    return path.open("ab", buffering=0)


def pid_path(name: str) -> Path:
    return RUNTIME_DIR / f"{name}.pid"


def remove_pid(name: str) -> None:
    try:
        pid_path(name).unlink()
    except FileNotFoundError:
        pass


def child_environment() -> dict[str, str]:
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = str(VENV_DIR)
    env["PATH"] = str(VENV_DIR / "Scripts") + os.pathsep + env.get("PATH", "")

    python_paths = [str(PROJECT_ROOT), str(VENV_SITE_PACKAGES)]
    existing = env.get("PYTHONPATH", "").strip()
    if existing:
        python_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    return env


def start_service(service: Service) -> subprocess.Popen[bytes] | None:
    if service.port is not None and is_listening(service.port):
        log(f"Service already listening: {service.name} on 127.0.0.1:{service.port}; leaving existing process untouched.")
        remove_pid(service.name)
        return None

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
            close_fds=True,
        )
    except Exception:
        stdout.close()
        stderr.close()
        raise

    pid_path(service.name).write_text(str(process.pid), encoding="ascii")
    log(f"Started service: {service.name} (PID {process.pid})")
    return process


def stop_process(process: subprocess.Popen[bytes] | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=4)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def main() -> int:
    bootstrap_log("entered main")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    SUPERVISOR_PID.write_text(str(os.getpid()), encoding="ascii")
    bootstrap_log(f"wrote supervisor pid file: {SUPERVISOR_PID}")
    os.chdir(PROJECT_ROOT)

    for required in (VENV_PYTHON, VENV_SITE_PACKAGES, RUNTIME_PYTHON, CLOUDFLARED, CLOUDFLARE_CONFIG):
        if not required.exists():
            raise RuntimeError(f"Required runtime path not found: {required}")

    os.environ["WARLOCK_AGENT_TOKEN"] = user_environment_value("WARLOCK_AGENT_TOKEN")
    os.environ["WARLOCK_CF_TEAM_DOMAIN"] = user_environment_value("WARLOCK_CF_TEAM_DOMAIN")
    os.environ["WARLOCK_CF_ACCESS_AUD"] = user_environment_value("WARLOCK_CF_ACCESS_AUD")

    log(f"Supervisor starting. PID {os.getpid()}")
    log(f"Supervisor sys.executable: {sys.executable}")
    log(f"Child runtime interpreter: {RUNTIME_PYTHON}")
    log("Required files and user environment values validated.")

    processes: dict[str, subprocess.Popen[bytes] | None] = {}
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
            time.sleep(5)
            for service in SERVICES:
                process = processes.get(service.name)

                if process is None:
                    if service.port is None:
                        try:
                            processes[service.name] = start_service(service)
                        except Exception as exc:
                            log(f"Failed to start service: {service.name} | {exc}")
                        continue

                    if not is_listening(service.port):
                        try:
                            processes[service.name] = start_service(service)
                        except Exception as exc:
                            log(f"Failed to start service: {service.name} | {exc}")
                    continue

                exit_code = process.poll()
                if exit_code is None:
                    continue

                remove_pid(service.name)
                log(f"Service exited: {service.name} (exit code {exit_code}). Error log: {service.name}.err.log")
                time.sleep(2)
                try:
                    processes[service.name] = start_service(service)
                except Exception as exc:
                    log(f"Failed to restart service: {service.name} | {exc}")
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
