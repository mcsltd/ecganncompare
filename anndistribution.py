import os
import sys
import json
from collections import defaultdict
from matplotlib import pyplot as plt
import pandas


class Text(object):
    CONCLUSIONS = "conclusions"
    ANNOTATOR = "annotator"
    CONCLUSION_THESAURUS = "conclusionThesaurus"


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


def main():
    folders = _parse_args(sys.argv)
    all_data = _read_folders(folders)
    # TODO: check thesaurus
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
        folder_data = _read_json_folder(dirname)
        try:
            _check_folder_data(folder_data)
        except Error as err:
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


def _read_json_folder(dirname):
    all_paths = (os.path.join(dirname, x) for x in os.listdir(dirname))
    all_files = [p for p in all_paths
                 if os.path.isfile(p) and p.lower().endswith(".json")]
    return _read_json_files(all_files)


def _read_json_files(filenames):
    results = []
    for fname in filenames:
        try:
            results.append(_read_json(fname))
        except ValueError:
            continue
    return results


def _read_json(filename):
    with open(filename, "rt") as fin:
        return json.load(fin)


def _check_folder_data(json_set):
    def _check_field_value(dataset, fieldname):
        message_template = "Files from one folder must have the same '{0}'"
        value = dataset[0][fieldname]
        if any(x[fieldname] != value for x in dataset):
            raise Error(message_template.format(fieldname))
    _check_field_value(json_set, Text.ANNOTATOR)
    _check_field_value(json_set, Text.CONCLUSION_THESAURUS)


def _group_by(iterable_data, fieldname):
    groups = defaultdict(list)
    for data in iterable_data:
        groups[data[fieldname]].append(data)
    return groups


def _extract_annotators_codes(folders_data):
    groups = _group_by(_to_flat(folders_data), Text.ANNOTATOR)
    for gname in groups:
        dataset = groups[gname]
        groups[gname] = _to_flat(d[Text.CONCLUSIONS] for d in dataset)
    return groups


def _to_flat(iterable_matrix):
    return (item for row in iterable_matrix for item in iterable_matrix)


if __name__ == "__main__":
    main()
