import sys
import json
from collections import namedtuple
from matplotlib import pyplot as plt
import pandas
from ecganncmp import Text


ComparingInfo = namedtuple("ComparingInfo",
                           ["ref_annotator", "test_annotator"])


def main():
    filename = _parse_args(sys.argv)
    codes, info = _read_annotations(filename)
    _plot_histogram(codes, info)
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
    info = ComparingInfo(
        ref_annotator=data[Text.REF_ANNOTATOR],
        test_annotator=data[Text.TEST_ANNOTATOR]
    )
    return codes, info


def _plot_histogram(codes, info):
    dataframe = _create_dataframe(codes)
    conlumn_names = {0: info.ref_annotator, 1: info.test_annotator}
    dataframe.rename(columns=conlumn_names, inplace=True)
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
