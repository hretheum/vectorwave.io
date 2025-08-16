import os
import sys


def main() -> None:
    print(os.path.basename(sys.argv[0]))


if __name__ == "__main__":
    main()
