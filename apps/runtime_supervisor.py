from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import IO

try:
    import winreg
except ImportError:  # pragma: no cover - Windows runtime only
    winreg = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / ".warlock" / "runtime"
PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
CLOUDFLARED = PROJECT_ROOT / "infrastructure" / "cloudflare" / "cloudflared.exe"
CLOUDFLARE_CONFIG = PROJECT_ROOT / "infrastructure" / "cloudflare" / "config" / "config.yml"
SUPERVISOR_LOG = RUNTIME_DIR / "supervisor.log"
SUPERVISOR_PID = RUNTIME_DIR / "supervisor.pid"


@dataclass(frozen=True)
class Service:
    name: str
    command: tuple[str, ...]
    port: int | None = None


SERVICES = (
    Service("agent", (str(PYTHON), "-m", "apps.local_agent.run_agent"), 8765),
    Service(
        "gateway",
        (
            str(PYTHON),
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
    Service("mcp", (str(PYTHON), "-m", "apps.mcp_server.run_mcp"), 8790),
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


def start_service(service: Service) -> subprocess.Popen[bytes] | None:
    if service.port is not None and is_listening(service.port):
        log(f"Service already listening: {service.name} on 127.0.0.1:{service.port}; leaving existing process untouched.")
        remove_pid(service.name)
        return None

    stdout = open_log(service.name, "out")
    stderr = open_log(service.name, "err")
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        log(f"Starting service: {service.name}")
        process = subprocess.Popen(
            service.command,
            cwd=PROJECT_ROOT,
            env=os.environ.copy(),
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
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    SUPERVISOR_PID.write_text(str(os.getpid()), encoding="ascii")
    os.chdir(PROJECT_ROOT)

    for required in (PYTHON, CLOUDFLARED, CLOUDFLARE_CONFIG):
        if not required.is_file():
            raise RuntimeError(f"Required file not found: {required}")

    os.environ["WARLOCK_AGENT_TOKEN"] = user_environment_value("WARLOCK_AGENT_TOKEN")
    os.environ["WARLOCK_CF_TEAM_DOMAIN"] = user_environment_value("WARLOCK_CF_TEAM_DOMAIN")
    os.environ["WARLOCK_CF_ACCESS_AUD"] = user_environment_value("WARLOCK_CF_ACCESS_AUD")

    log(f"Supervisor starting. PID {os.getpid()}")
    log("Required files and user environment values validated.")

    processes: dict[str, subprocess.Popen[bytes] | None] = {}
    stopping = False

    def request_stop(*_: object) -> None:
        nonlocal stopping
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
        for service in SERVICES:
            stop_process(processes.get(service.name))
            remove_pid(service.name)
        try:
            SUPERVISOR_PID.unlink()
        except FileNotFoundError:
            pass
        log("Supervisor stopped.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        try:
            log(f"Supervisor fatal error: {exc}")
        finally:
            try:
                SUPERVISOR_PID.unlink()
            except FileNotFoundError:
                pass
        raise
