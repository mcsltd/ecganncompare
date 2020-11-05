import sys
from matplotlib import pyplot as plt


def main():
    filename = _parse_args(sys.argv)
    codes = _read_annotations(filename)
    _plot_histogram(codes)
    plt.show()


if __name__ == "__main__":
    main()
