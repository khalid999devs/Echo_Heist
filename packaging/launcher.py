"""Absolute-import entry point for PyInstaller's windowed native executable."""

from echo_heist.app import main

if __name__ == "__main__":
    raise SystemExit(main())
