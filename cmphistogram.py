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
    title = "Annotations comparing"
    counts = {}
    for rec_pairs in codes:
        for pair in rec_pairs:
            code = _get_code(pair)
            code_counts = counts.setdefault(code, [0, 0])
            if pair[0] == pair[1]:
                code_counts[0] += 1
            else:
                code_counts[1] += 1
    df = pandas.DataFrame.from_dict(counts, orient="index")\
                         .sort_index()\
                         .rename(columns={0: "Matches", 1: "Misses"})
    df.plot(ax=plt.gca(), kind="bar", legend=True)


def _get_code(pair):
    return pair[0] if pair[0] is not None else pair[1]


if __name__ == "__main__":
    main()
