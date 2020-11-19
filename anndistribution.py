import os
import sys
import json
from collections import defaultdict, Counter
import argparse

from matplotlib import pyplot as plt
import pandas


class Text(object):
    CONCLUSIONS = "conclusions"
    ANNOTATOR = "annotator"
    CONCLUSION_THESAURUS = "conclusionThesaurus"
    DATABASE = "database"
    RECORD_ID = "record"


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


def main():
    folders = _get_data_folders(sys.argv).input_folders
    all_data = _read_folders(folders)
    _print_folders_names(folders)
    all_data, deviations = _remove_deviations(
        all_data, Text.CONCLUSION_THESAURUS)
    if deviations:
        _print_removed_items(deviations, Text.CONCLUSION_THESAURUS)
    data_groups = _group_by(all_data, Text.ANNOTATOR)
    data_groups = _remove_excess_groups(data_groups, _get_max_groups_count())
    # TODO: print removed groups
    _print_groups_info(data_groups)
    codes_groups = _extract_annotators_codes(data_groups)
    _plot_histogram(codes_groups.values(), codes_groups.keys())
    plt.show()


def _get_data_folders(args):
    default_data_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data")
    parser = argparse.ArgumentParser(
        description="Plot annotations destribution histograms"
    )
    parser.add_argument("input_folders", nargs="*",
                        default=[default_data_folder],
                        help="paths to input folders")
    parser.add_argument("--thesaurus", help="path to thesaurus")
    data = parser.parse_args(args[1:])
    return data


def _read_folders(folders):
    all_data = []
    for dirname in folders:
        folder_data = _read_json_folder(dirname)
        all_data += folder_data
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
    counts = defaultdict(lambda: [0 for _ in range(len(codes))])
    for column_index, folder_codes in enumerate(codes):
        for code in folder_codes:
            if code is None:
                continue
            counts[code][column_index] += 1
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


def _group_by(iterable_data, fieldname):
    groups = defaultdict(list)
    for data in iterable_data:
        groups[data[fieldname]].append(data)
    return groups


def _extract_annotators_codes(data_groups):
    code_groups = {}
    for gname in data_groups:
        dataset = data_groups[gname]
        code_groups[gname] = _to_flat(d[Text.CONCLUSIONS] for d in dataset)
    return code_groups


def _to_flat(iterable_matrix):
    return (item for row in iterable_matrix for item in row)


def _remove_deviations(dataset, fieldname):
    counts = Counter(data[fieldname] for data in dataset)
    common_value = counts.most_common()[0][0]
    good_items, others = [], []
    for data in dataset:
        if data[fieldname] == common_value:
            good_items.append(data)
        else:
            others.append(data)
    return good_items, others


def _print_folders_names(folders):
    print("Plotting annotation distribution histograms from folders: %s\n" %
          ", ".join(folders))


def _print_removed_items(items, fieldname):
    for item in items:
        message = "Removed {0}-{1} with {2} = {3}".format(
            item[Text.DATABASE], item[Text.RECORD_ID], fieldname,
            item[fieldname]
        )
        print(message)
    print("")


def _print_groups_info(data_groups):
    temp_annotator = next(iter(data_groups))
    thesaurus = data_groups[temp_annotator][0][Text.CONCLUSION_THESAURUS]
    print("Thesaurus: %s" % thesaurus)
    print("Annotation groups:\n")
    for annotator in data_groups:
        print("Annotator: " + annotator)
        data_list = data_groups[annotator]
        print("Records Count: %d" % len(data_list))
        codes_count = sum(len(d[Text.CONCLUSIONS]) for d in data_list)
        print("Conclusions count: %d\n" % codes_count)


def _remove_excess_groups(data_groups, max_count):
    if len(data_groups) < max_count:
        return data_groups
    sorted_pairs = sorted(data_groups.items(), key=(lambda p: len(p[1])),
                          reverse=True)
    return dict(sorted_pairs[:max_count])


def _get_max_groups_count():
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    return len(colors)


def _show_annotations_text(cresults, thesaurus_path):
    filename = "annotations_descritpion.txt"
    thesaurus = _parse_thesaurus(thesaurus_path)
    all_codes = set(_get_code(p) for cr in cresults for p in cr.codes)
    with codecs.open(filename, "w", encoding="utf-8") as fout:
        for code in sorted(all_codes):
            fout.write(u"{0}: {1}\n".format(code, thesaurus[code]))
    os.startfile(filename)


if __name__ == "__main__":
    main()
