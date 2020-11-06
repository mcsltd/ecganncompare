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
    temp = _create_dataframe(codes, ['reference', 'test'])
    hist_data = [[], []]
    for i, column in enumerate(hist_data):
        for rec_codes in codes:
            column += (p[i] for p in rec_codes if p[i] is not None)

    # TODO: annotator name is label
    _plot_items_hist(hist_data[0], plt.axes(), "blue", "Reference")
    _plot_items_hist(hist_data[1], plt.axes(), "red", "Test")
    plt.legend()
    plt.title("Records count: %d" % len(codes))


def _plot_items_hist(items, axes, color, label):
    counts = Counter(items)
    dataframe = pandas.DataFrame.from_dict(counts, orient="index",
                                           columns=[label])
    dataframe.sort_index(inplace=True)
    dataframe.plot(ax=axes, kind="bar", legend=False, color=color)


def _create_dataframe(codes, columns_names):
    hist_data = [[], []]
    for i, column in enumerate(hist_data):
        for rec_codes in codes:
            column += (p[i] for p in rec_codes if p[i] is not None)
    counters = [Counter(col) for col in hist_data]
    code_set = set(counters[0].viewkeys()).union(counters[1].viewkeys())
    united_counts = dict((code, [counters[0][code], counters[1][code]])
                         for code in code_set)
    return pandas.DataFrame.from_dict(united_counts, orient="index",
                                      columns=columns_names)


if __name__ == "__main__":
    main()
