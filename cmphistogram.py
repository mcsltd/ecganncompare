import sys
import json
from matplotlib import pyplot as plt
import pandas
from ecganncmp import Text

_WINDOW_TITLE = "Annotations comparing"


def main():
    filename = _parse_args(sys.argv)
    codes = _read_annotations(filename)
    _plot_histogram(codes, _WINDOW_TITLE)
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


def _plot_histogram(codes, title):
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
                         .sort_index()
    df.columns = ["Matches", "Misses"]
    _plot_bidirectional_histogram(df)
    plt.title(title + ". Records count: {0}".format(len(codes)))
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


if __name__ == "__main__":
    main()
