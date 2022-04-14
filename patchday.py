#!/usr/bin/env python3
from pathlib import Path
import os, subprocess, sys


RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(30, 38)


def Warn(x):
    return (COLOR_SEQ % (RED)) + x + RESET_SEQ

def Info(x, col=GREEN):
    return (COLOR_SEQ % (col)) + x + RESET_SEQ


def output_callback_check_yes(completed_process):
    out = completed_process.stdout.strip()
    yes = "yes"
    if out != yes:
        cmd = " ".join(completed_process.args)
        print(Warn(f'Die Ausgabe von `{cmd}` war nicht "{yes}", sondern "{out}"!'))


def run(cmd, cwd=None, output_callback=None, quiet=False):
    if not quiet:
        print(Info("\n{}$".format(cwd or ""), BLUE), Info(" ".join(cmd), BLUE))

    try:
        completed = subprocess.run(cmd, cwd=cwd, check=True, capture_output=(output_callback is not None), text=True)
    except OSError as e:
        print(Warn(e.strerror))
    except KeyboardInterrupt:
        print("(got Ctrl+C)")

    if output_callback:
        output_callback(completed)


def in_virtualenv():
    # See http://stackoverflow.com/questions/1871549/python-determine-if-running-inside-virtualenv
    return hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix


if __name__ == "__main__":
    if not in_virtualenv():
        # Should not run `pip` if the virtualenv is not active.
        print(Warn("\nNo virtualenv seems to be active.\n"))
        sys.exit()

    print("\nGit repository not updated automatically, please fetch and merge manually.")
    run(["pip", "install", "-q", "-r", "requirements.txt"])
    # run(["python", "bookmaker.py", "--pdf"])

    # # Make sure that we didn't forget any `__init__.py` files in the `tests/`
    # # directories. The test runner might miss tests otherwise. (TODO: Does it?)
    # for root, dirs, files in os.walk("."):
    #     if "tests" in dirs:
    #         path = Path(root + "/tests/__init__.py")
    #         if not path.exists():
    #             print(Warn(f"\nDATEI __init__.py FEHLT in {path.parent}"))
    #         # else:
    #         #     print(f"{path.parent} – OK")
    #     for excl in [".git", ".svn", "node_modules"]:
    #         if excl in dirs:
    #             dirs.remove(excl)

    # Make sure that the clock is properly synchronized.
    run(["timedatectl", "show", "--property", "CanNTP",          "--value"], output_callback=output_callback_check_yes, quiet=True)
    run(["timedatectl", "show", "--property", "NTP",             "--value"], output_callback=output_callback_check_yes, quiet=True)
    run(["timedatectl", "show", "--property", "NTPSynchronized", "--value"], output_callback=output_callback_check_yes, quiet=True)

    # Run all tests:
    # python -Wall -Werror manage.py test --keepdb --failfast
    print("All done.\n")
