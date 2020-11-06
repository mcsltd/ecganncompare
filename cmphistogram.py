import sys
import json
from collections import namedtuple
from matplotlib import pyplot as plt
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


def _plot_histograms(codes, info):
    raise NotImplementedError()


if __name__ == "__main__":
    main()
