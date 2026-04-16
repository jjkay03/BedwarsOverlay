import sys

def _check_deps() -> None:
    missing = []
    for pkg in ("customtkinter", "requests"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(
            "Missing dependencies:\n"
            f"  {', '.join(missing)}\n\n"
            "Install with:\n"
            f"  pip install {' '.join(missing)}"
        )
        sys.exit(1)

def main() -> None:
    _check_deps()
    from modules import App
    App().mainloop()

if __name__ == "__main__":
    main()
