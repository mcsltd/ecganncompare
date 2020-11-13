import sys
from matplotlib import pyplot as plt
import pandas
import ecganncmp as eac


class Text():
    CONCLUSIONS = "conclusions"
    ANNOTATOR = "annotator"


def main():
    folders = _parse_args(sys.argv)
    all_data = _read_folders(folders)
    codes = _get_all_codes(all_data)
    annotators = _get_annotators(all_data)
    _plot_histogram(codes, annotators)
    plt.show()


def _parse_args(args):
    if len(args) < 2:
        raise RuntimeError("Not enough arguments")
    return args[1:]


def _read_folders(folders):
    all_data = []
    for dirname in folders:
        folder_data = eac.read_json_folder(dirname)
        try:
            eac.check_folder_data(folder_data)
        except eac.Error as err:
            print("Reading " + dirname + " error:")
            print(err)
        else:
            all_data.append(folder_data)
    return all_data


def _get_all_codes(all_data):
    all_codes = []
    for folder_data in all_data:
        codes = []
        for rec in folder_data:
            codes += rec[Text.CONCLUSIONS]
        all_codes.append(codes)
    return all_codes


def _get_annotators(all_data):
    return [x[0][Text.ANNOTATOR] for x in all_data]


def _plot_histogram(codes, annotators):
    title = "Annotations distributions"
    dataframe = _create_dataframe(codes).sort_index()
    dataframe.columns = annotators
    dataframe.plot(ax=plt.gca(), kind="bar", legend=True)
    plt.title(title)
    plt.gcf().canvas.set_window_title(title)


def _create_dataframe(codes):
    counts = {}
    for column_index, folder_codes in enumerate(codes):
        for code in folder_codes:
            if code is None:
                continue
            code_counts = counts.setdefault(
                code, [0 for _ in range(len(codes))])
            code_counts[column_index] += 1
    return pandas.DataFrame.from_dict(counts, orient="index")


if __name__ == "__main__":
    main()
