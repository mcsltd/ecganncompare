import sys
from collections import namedtuple
from matplotlib import pyplot as plt
import pandas
import ecganncmp as eac


ComparingInfo = namedtuple("ComparingInfo",
                           ["ref_annotator", "test_annotator"])


def main():
    folders = _parse_args(sys.argv)
    codes, annotators = _read_annotations(folders)
    _plot_histogram(codes, annotators)
    plt.show()


def _parse_args(args):
    if len(args) < 2:
        raise RuntimeError("Not enough arguments")
    return args[1:]


def _read_annotations(folders):
    data = []
    annotators = []
    for dirname in folders:
        folder_data = eac.read_json_folder(dirname)
        try:
            eac.check_folder_data(folder_data)
        except eac.Error as err:
            print("Reading " + dirname " error:")
            print(err)
        else:
            codes = []
            for rec in folder_data:
                codes += rec[eac.Text.CONCLUSIONS]
            data.append(codes)
            annotators.append(folder_data[0][eac.Text.ANNOTATOR])
    return data, annotators


def _plot_histogram(codes, info):
    title = "Annotations distribution"
    dataframe = _create_dataframe(codes)
    conlumn_names = {0: info.ref_annotator, 1: info.test_annotator}
    dataframe.rename(columns=conlumn_names, inplace=True)
    dataframe.sort_index(inplace=True)
    dataframe.plot(ax=plt.gca(), kind="bar", legend=True)
    plt.title(title + ". Records count: %d" % len(codes))
    plt.gcf().canvas.set_window_title(title)


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
