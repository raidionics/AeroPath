import os
from argparse import ArgumentParser

from src.gui import WebUI


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--cwd",
        type=str,
        default="/home/user/app/",
        help="Set current working directory (path to app.py).",
    )
    parser.add_argument(
        "--share",
        type=int,
        default=0,
        help="Whether to enable the app to be accessible online"
        "-> setups a public link which requires internet access.",
    )
    args = parser.parse_args()

    print("Current working directory:", args.cwd)

    if not os.path.exists(args.cwd):
        raise ValueError("Chosen 'cwd' is not a valid path!")
    if args.share not in [0, 1]:
        raise ValueError(
            "The 'share' argument can only be set to 0 or 1, but was:",
            args.share,
        )

    print("Current cwd:", args.cwd)

    # initialize and run app
    print("Launching demo...")
    app = WebUI(cwd=args.cwd, share=args.share)
    app.run()


if __name__ == "__main__":
    main()
