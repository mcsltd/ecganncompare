import sys
import json
from collections import Counter
from matplotlib import pyplot as plt
import numpy as np
import pandas
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
    heights = [[], []]
    bins = [[], []]
    heights[0], bins[0] = np.histogram(hist_data[0])
    heights[1], bins[1] = np.histogram(hist_data[1])
    width = (bins[0][1] - bins[0][0]) / 3

    plt.bar(bins[0][:-1], heights[0], width=width, label="reference")
    plt.bar(bins[1][:-1] + width, heights[1], width=width, label="test")
    plt.legend()
    plt.title("Records count: %d" % len(codes))


def _plot_items_hist(items, axes):
    counts = Counter(items)
    dataframe = pandas.DataFrame.from_dict(counts, orient="index")
    dataframe.sort_index(inplace=True, key=_code_to_numeric)
    dataframe.plot(ax=axes, kind="bar", legend=False)


if __name__ == "__main__":
    main()
