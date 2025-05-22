"""
Thin wrapper that forwards to sotd.cli when that module exists.
"""


def main() -> None:
    from importlib import import_module

    try:
        import_module("sotd.cli").main()
    except ModuleNotFoundError:
        print("CLI not implemented yet. Use individual scripts or Make targets.")


if __name__ == "__main__":
    main()
