from src.gui import WebUI


def main():
    print("Launching demo...")

    # cwd = "/Users/andreped/workspace/AeroPath/"  # local testing -> macOS
    cwd = "/home/user/app/"  # production -> docker

    class_name = "tumor"

    # initialize and run app
    app = WebUI(class_name=class_name, cwd=cwd)
    app.run()


if __name__ == "__main__":
    main()
