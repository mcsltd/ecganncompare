import sys
from matplotlib import pyplot as plt
import json
from ecganncmp import Text


def main():
    filename = _parse_args(sys.argv)
    codes = _read_annotations(filename)
    _plot_histogram(codes)
    plt.show()


def _parse_args(args):
    if len(args) < 2:
        raise RuntimeError("Not enough arguments")
    return args[1]


def _read_annotations(filename):
    with open(filename, "rt") as fin:
        data = json.load(fin)
    codes = []
    for rec_data in data[Text.RECORDS]:
        codes.append(rec_data[Text.CONCLUSIONS])
    return codes


def _plot_histogram(codes):
    hist_data = [[], []]
    for i, column in enumerate(hist_data):
        for rec_codes in codes:
            column += (p[i] for p in rec_codes if p[i] is not None)
    # TODO: show annotators id
    plt.hist(hist_data, density=True, histtype='bar', label=["reference", "test"])
    plt.title("Records count: %d" % len(codes))
    plt.legend()


if __name__ == "__main__":
    main()
