"""Stable entrypoint for PyInstaller; runtime code lives in the installed package."""

from navigation_lab.app import main

if __name__ == "__main__":
    raise SystemExit(main())
