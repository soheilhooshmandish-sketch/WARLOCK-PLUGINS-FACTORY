from pathlib import Path
import subprocess


WORKSPACE = Path(__file__).resolve().parents[2]

ALLOWED_COMMANDS = {
    "python_version": ["python", "--version"],
    "git_status": ["git", "status", "--short"],
    "git_branch": ["git", "branch", "--show-current"],
}


def run_allowed(command_name: str) -> str:
    if command_name not in ALLOWED_COMMANDS:
        raise PermissionError(f"Command not allowed: {command_name}")

    result = subprocess.run(
        ALLOWED_COMMANDS[command_name],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False,
    )

    output = (result.stdout + result.stderr).strip()

    return output


if __name__ == "__main__":
    print("Warlock Command Gateway")
    print("=" * 50)

    for command_name in ALLOWED_COMMANDS:
        print(f"\n[{command_name}]")
        try:
            print(run_allowed(command_name))
        except Exception as exc:
            print(f"ERROR: {exc}")

    print("\n" + "=" * 50)
    print("Gateway test completed.")