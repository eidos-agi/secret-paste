from __future__ import annotations

import argparse
import getpass
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Sequence


DEFAULT_PROMPT = "Paste secret: "


def read_secret_from_terminal(prompt: str = DEFAULT_PROMPT) -> str:
    return getpass.getpass(prompt)


def read_secret_from_gui(prompt: str = DEFAULT_PROMPT) -> str:
    script = """
on run argv
  set promptText to item 1 of argv
  try
    set dialogResult to display dialog promptText default answer "" with hidden answer buttons {"Cancel", "OK"} default button "OK" cancel button "Cancel" with title "secret-paste"
    return text returned of dialogResult
  on error number -128
    error "Secret entry canceled."
  end try
end run
"""
    completed = subprocess.run(
        ["osascript", "-e", script, prompt],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit("Secret entry canceled or GUI prompt failed.")
    return completed.stdout


def read_secret(prompt: str = DEFAULT_PROMPT, *, gui: bool = True) -> str:
    secret = read_secret_from_gui(prompt) if gui else read_secret_from_terminal(prompt)
    if not secret:
        raise SystemExit("No secret received.")
    return secret.rstrip("\r\n")


def run_with_secret(args: argparse.Namespace) -> int:
    if not args.command:
        raise SystemExit("Missing command after --.")

    secret = read_secret(args.prompt, gui=not args.terminal)
    env = os.environ.copy()
    env[args.env] = secret

    if args.confirm:
        print(f"Running command with {args.env} set in child environment only.", file=sys.stderr)

    completed = subprocess.run(args.command, env=env, check=False)
    return completed.returncode


def write_secret(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser()
    if path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing file: {path}")

    secret = read_secret(args.prompt, gui=not args.terminal)
    path.parent.mkdir(parents=True, exist_ok=True)

    flags = os.O_WRONLY | os.O_CREAT
    if args.force:
        flags |= os.O_TRUNC
    else:
        flags |= os.O_EXCL

    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(secret)
            if args.trailing_newline:
                handle.write("\n")
    except Exception:
        try:
            path.unlink()
        finally:
            raise

    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    print(f"Wrote secret to {path} with mode 0600.", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="secret-paste",
        description="Prompt locally for a secret without echoing it.",
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Run a command with the pasted secret set as an environment variable.",
    )
    run_parser.add_argument(
        "--env",
        required=True,
        help="Environment variable name to set for the child command.",
    )
    run_parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Prompt text shown before reading the secret.",
    )
    run_parser.add_argument(
        "--terminal",
        action="store_true",
        help="Use hidden terminal input instead of the default macOS GUI dialog.",
    )
    run_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Print a non-secret confirmation before running the command.",
    )
    run_parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after --.")
    run_parser.set_defaults(func=run_with_secret)

    write_parser = subparsers.add_parser(
        "write",
        help="Write the pasted secret to a 0600 file.",
    )
    write_parser.add_argument("--path", required=True, help="Destination file path.")
    write_parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Prompt text shown before reading the secret.",
    )
    write_parser.add_argument(
        "--terminal",
        action="store_true",
        help="Use hidden terminal input instead of the default macOS GUI dialog.",
    )
    write_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination file if it already exists.",
    )
    write_parser.add_argument(
        "--trailing-newline",
        action="store_true",
        help="Append a newline to the file.",
    )
    write_parser.set_defaults(func=write_secret)

    return parser


def normalize_remainder(argv: Sequence[str]) -> list[str]:
    normalized = list(argv)
    if "--" in normalized:
        normalized.remove("--")
    return normalized


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(normalize_remainder(sys.argv[1:] if argv is None else argv))
    return int(parsed.func(parsed))


if __name__ == "__main__":
    raise SystemExit(main())
