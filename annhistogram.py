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
    dataframe = _create_dataframe(codes)
    # TODO: rename columns to annotator names
    dataframe.rename(columns={0: 'reference', 1: 'test'}, inplace=True)
    dataframe.sort_index(inplace=True)
    dataframe.plot(ax=plt.axes(), kind="bar", legend=True)
    plt.title("Records count: %d" % len(codes))


def _create_dataframe(codes):
    counts = {}
    for rec_pairs in codes:
        for pair in rec_pairs:
            for i, code in enumerate(pair):
                if code is None:
                    continue
                code_counts = counts.setdefault(code, [0, 0])
                code_counts[i] += 1
    return pandas.DataFrame.from_dict(counts, orient="index")


if __name__ == "__main__":
    main()
