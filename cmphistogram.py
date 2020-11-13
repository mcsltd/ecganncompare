import sys
import json
from collections import namedtuple, defaultdict
from matplotlib import pyplot as plt
import pandas


class Text(object):
    CONCLUSIONS = "conclusions"
    RECORDS = "records"
    REF_ANNOTATOR = "refAnnotator"
    TEST_ANNOTATOR = "testAnnotator"


ComparingResult = namedtuple("ComparingResult",
                             ["ref_annotator", "test_annotator", "codes"])

_WINDOW_TITLE = "Annotations comparing"


def main():
    filenames = _parse_args(sys.argv)
    for fname in filenames:
        result = _read_annotations(fname)
        plt.figure()
        _plot_histogram(result)
    plt.show()


def _parse_args(args):
    if len(args) < 2:
        raise RuntimeError("Not enough arguments")
    return args[1:]


def _read_annotations(filename):
    with open(filename, "rt") as fin:
        data = json.load(fin)
    codes = []
    for rec_data in data[Text.RECORDS]:
        codes.append(rec_data[Text.CONCLUSIONS])
    result = ComparingResult(
        ref_annotator=data[Text.REF_ANNOTATOR],
        test_annotator=data[Text.TEST_ANNOTATOR],
        codes=codes
    )
    return result


def _plot_histogram(cresult):
    counts = defaultdict(lambda: [0, 0])
    for rec_pairs in cresult.codes:
        for pair in rec_pairs:
            code = _get_code(pair)
            code_counts = counts[code]
            if pair[0] == pair[1]:
                code_counts[0] += 1
            else:
                code_counts[1] += 1
    df = pandas.DataFrame.from_dict(counts, orient="index").sort_index()
    df.columns = ["Matches", "Misses"]
    _plot_bidirectional_histogram(df)
    title = _get_title(cresult.ref_annotator, cresult.test_annotator)
    plt.title(title + ". Records count: {0}".format(len(cresult.codes)))
    plt.gcf().canvas.set_window_title(_WINDOW_TITLE)


def _get_code(pair):
    return pair[0] if pair[0] is not None else pair[1]


def _plot_bidirectional_histogram(dataframe):
    directions_count = 2
    default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i, cname in enumerate(dataframe.columns[:directions_count]):
        column = dataframe[cname]
        if i == directions_count - 1:
            column = column * (-1)
        column.plot(ax=plt.gca(), kind="bar", legend=True,
                    color=default_colors[i])
    plt.axhline(c="k")
    locs, _ = plt.yticks()
    plt.yticks(locs, [abs(loc) for loc in locs])


def _get_title(ref_annotator, test_annotator):
    return "Comparing {0} and {1} annotations".format(
        ref_annotator, test_annotator
    )


if __name__ == "__main__":
    main()
