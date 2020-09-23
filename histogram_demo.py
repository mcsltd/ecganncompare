from matplotlib import pyplot as plt
import sys
import json
import pandas
from collections import Counter


class ComparingResult():
    def __init__(self):
        self.sensitivity = 0.0
        self.specificity = 0.0
        self.codes = []


def main():
    input_filename = _get_filename(sys.argv)
    cmp_result = _read_cmp_result(input_filename)
    _plot_hist(cmp_result)
    plt.show()


def _get_filename(args):
    return args[1]


def _read_cmp_result(input_filename):
    with open(input_filename, "rt") as fin:
        content = json.load(fin)
    result = ComparingResult()
    result.sensitivity = content["Sensitivity"]["Value"]
    result.specificity = content["Specificity"]["Value"]
    for rec in content["Records"].values():
        for pair in rec["Codes"]:
            result.codes.append(pair)
    return result


def _plot_hist(cmp_result):
    fig, axes = plt.subplots(nrows=2, ncols=1)
    fig.canvas.set_window_title('All annotations')

    ref_codes = (x[0] for x in cmp_result.codes if x[0] is not None)
    _plot_items_hist(ref_codes, axes[0])
    axes[0].set_title("Ref annotations")

    test_codes = (x[1] for x in cmp_result.codes if x[1] is not None)
    _plot_items_hist(test_codes, axes[1])
    axes[1].set_title("Test annotations")

    fig, axes = plt.subplots(nrows=2, ncols=1)
    fig.canvas.set_window_title('Annotations comparing')

    matches = (x[1] for x in cmp_result.codes if x[0] == x[1])
    _plot_items_hist(matches, axes[0])
    axes[0].set_title("Matches")

    no_matches = (x[0] if x[0] is not None else x[1]
                  for x in cmp_result.codes if x[0] != x[1])
    _plot_items_hist(no_matches, axes[1])
    axes[1].set_title("Misses")


def _plot_items_hist(items, axes):
    counts = Counter(items)
    dataframe = pandas.DataFrame.from_dict(counts, orient="index")
    dataframe.sort_index(inplace=True, key=_code_to_numeric)
    dataframe.plot(ax=axes, kind="bar", legend=False)


def _code_to_numeric(text_codes):
    result = []
    for x in text_codes:
        code = int("".join(c for c in x if c != "."))
        result.append(code)
    return result


if __name__ == "__main__":
    main()
