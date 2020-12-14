# coding=utf-8
import os
import sys
import json
from collections import defaultdict, Counter, OrderedDict, namedtuple
import argparse

from matplotlib import pyplot as plt
import pandas


class Text(object):
    CONCLUSIONS = "conclusions"
    ANNOTATOR = "annotator"
    CONCLUSION_THESAURUS = "conclusionThesaurus"
    DATABASE = "database"
    RECORD_ID = "record"
    GROUPS = "groups"
    REPORTS = "reports"
    ID = "id"
    NAME = "name"
    TYPE = "type"
    CMPRESULT = "cmpresult"
    LANGUAGE = "language"
    THESAURUS_LABEL = "thesaurus"


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


DatagroupInfo = namedtuple("DatagroupInfo", [
    "annotator", "records_count", "annotations_count", "thesaurus"
])


Thesaurus = namedtuple("Thesaurus", ["label", "lang", "items", "groups"])


InputData = namedtuple("InputData", ["paths", "thesaurus"])


def main():
    data = _parse_args(sys.argv)
    _print_folders_names(data.paths)
    all_data = _read_folders(data.paths)
    all_data = _remove_results(all_data)
    all_data, deviations = _remove_deviations(
        all_data, Text.CONCLUSION_THESAURUS)
    if deviations:
        _print_removed_items(deviations, Text.CONCLUSION_THESAURUS)
    if not all_data:
        raise Error("Input files not found")
    data_groups = _group_by(all_data, Text.ANNOTATOR)
    data_groups = _remove_excess_groups(data_groups, _get_max_groups_count())
    # TODO: print removed groups
    groups_info = _get_datagroups_info(data_groups)
    _print_groups_info(groups_info)
    codes_groups = _extract_annotators_codes(data_groups)
    _plot_histogram(codes_groups, groups_info, data.thesaurus)
    plt.show()


def _parse_args(args):
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
    return InputData(
        data.input_folders,
        data.thesaurus
    )


def _read_folders(folders):
    all_data = []
    path_not_found_fmt = "Warning! Path {0} not found."
    ignored_file_fmt = (
        "Warning! This program works only with data folders. File {0} will "
        "be ignored."
    )
    for path in folders:
        if not os.path.exists(path):
            print(path_not_found_fmt.format(path))
        elif os.path.isfile(path):
            print(ignored_file_fmt.format(path))
        else:
            all_data += _read_json_folder(path)
    return all_data


def _plot_histogram(codes_groups, datagroups_info, thesaurus_path=None):
    dataframe = _create_dataframe(codes_groups)
    if thesaurus_path is None:
        dataframe.sort_index(inplace=True)
        thesaurus = _create_thesaurus()
        _plot_dataframe(dataframe)
        _add_info_to_plot(dataframe.columns, datagroups_info, thesaurus.lang)
        return
    thesaurus = _parse_thesaurus(thesaurus_path)
    dataframes = _split_dataframe(dataframe, thesaurus)
    if len(dataframes) > plt.rcParams["figure.max_open_warning"]:
        plt.rcParams.update({'figure.max_open_warning': 0})
    for name in dataframes:
        frame = dataframes[name]
        plt.figure()
        _plot_dataframe(frame)
        _wide_ylabels_padding()
        _add_info_to_plot(frame.columns, datagroups_info, thesaurus.lang)


def _create_dataframe(codes_groups):
    group_count = len(codes_groups)
    counts = defaultdict(lambda: [0 for _ in range(group_count)])
    for column_index, gname in enumerate(codes_groups):
        for code in codes_groups[gname]:
            if code is None:
                continue
            counts[code][column_index] += 1
    return pandas.DataFrame.from_dict(counts, columns=codes_groups.keys(),
                                      orient="index")


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
        return json.load(fin, object_pairs_hook=OrderedDict)


def _group_by(iterable_data, fieldname):
    groups = defaultdict(list)
    for data in iterable_data:
        groups[data[fieldname]].append(data)
    return groups


def _extract_annotators_codes(data_groups):
    code_groups = {}
    for gname in data_groups:
        dataset = data_groups[gname]
        codes = _to_flat(d[Text.CONCLUSIONS] for d in dataset)
        code_groups[gname] = list(codes)
    return code_groups


def _to_flat(iterable_matrix):
    return (item for row in iterable_matrix for item in row)


def _remove_deviations(dataset, fieldname):
    counts = Counter(data[fieldname] for data in dataset if fieldname in data)
    common_value = counts.most_common()
    if common_value:
        common_value = common_value[0][0]
    else:
        return dataset, []
    good_items, others = [], []
    for data in dataset:
        value = data.get(fieldname)
        if value == common_value:
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


def _print_groups_info(datagroups_info):
    temp_annr = next(iter(datagroups_info))
    print("Thesaurus: " + datagroups_info[temp_annr].thesaurus)
    print("Annotation groups:\n")
    for annotator in datagroups_info:
        info = datagroups_info[annotator]
        print("Annotator: " + annotator)
        print("Records Count: %d" % info.records_count)
        print("Conclusions count: %d\n" % info.annotations_count)


def _remove_excess_groups(data_groups, max_count):
    if len(data_groups) < max_count:
        return data_groups
    sorted_pairs = sorted(data_groups.items(), key=(lambda p: len(p[1])),
                          reverse=True)
    return dict(sorted_pairs[:max_count])


def _get_max_groups_count():
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    return len(colors)


def _parse_thesaurus(filename):
    data = _read_json(filename)
    items = OrderedDict()
    groups = []
    for group in data[Text.GROUPS]:
        group_items = []
        for ann in group[Text.REPORTS]:
            items[ann[Text.ID]] = ann[Text.NAME]
            group_items.append(ann[Text.ID])
        groups.append(group_items)
    return _create_thesaurus(
        data[Text.THESAURUS_LABEL],
        data[Text.LANGUAGE],
        items,
        groups
    )


def _remove_results(dataset):
    return [d for d in dataset
            if Text.TYPE not in d or d[Text.TYPE] != Text.CMPRESULT]


def _split_dataframe(df, thesaurus):
    subframes = {}
    for group in thesaurus.groups:
        name = "{0}-{1}".format(group[0], group[-1])
        frame = df.loc[(k for k in group if k in df.index)]
        if frame.empty:
            continue
        frame.index = [thesaurus.items[k] for k in frame.index]
        subframes[name] = frame
    return subframes


def _get_title(lang=None):
    if lang == "ru":
        return (
            u"Число использования заключения аннотатором (распределение "
            u"заключений)"
        )
    return (
        "Counts of uses of conclusions by annotator (conclusions "
        "distribution)"
    )


def _get_window_title(lang=None):
    if lang == "ru":
        return u"Распределение заключений"
    return "Conclusions distribution"


def _get_datagroups_info(data_groups):
    infos = {}
    for annotator in data_groups:
        annotator_data = data_groups[annotator]
        codes_count = sum(len(d[Text.CONCLUSIONS]) for d in annotator_data)
        infos[annotator] = DatagroupInfo(
            annotator,
            len(annotator_data),
            codes_count,
            annotator_data[0][Text.CONCLUSION_THESAURUS]
        )
    return infos


def _get_title_tail(datagroups_info, lang=None):
    records_count = max(d.records_count for d in datagroups_info.values())
    template = None
    if lang == "ru":
        template = u"{0} записей"
    else:
        template = "{0} records"
    return template.format(records_count)


def _get_legend_label_format(lang):
    if lang == "ru":
        return u"{0} ({1} заключений из {2})"
    return "{0} ({1} conclusions from {2})"


def _get_legend_labels(annotators, lang, datagroups_info):
    template = _get_legend_label_format(lang)
    total_count = sum(d.annotations_count for d in datagroups_info.values())
    labels = []
    for annr in annotators:
        info = datagroups_info[annr]
        labels.append(template.format(
            annr, info.annotations_count, total_count))
    return labels


def _create_thesaurus(label="", lang=None, items=None, groups=None):
    if items is None:
        items = {}
    if groups is None:
        groups = {}
    return Thesaurus(label, lang, items, groups)


def _plot_dataframe(dataframe):
    # NOTE: barh() plor bars in reverse order
    dataframe[::-1].plot.barh(ax=plt.gca(), width=0.75, legend=False)


def _add_info_to_plot(columns, datagroups_info, lang):
    title = _get_title(lang) + ". " + _get_title_tail(datagroups_info, lang)
    plt.title(title)
    plt.gcf().canvas.set_window_title(_get_window_title(lang))
    legend_labels = _get_legend_labels(columns, lang, datagroups_info)
    plt.legend(legend_labels)


def _wide_ylabels_padding():
    plt.subplots_adjust(left=0.4, bottom=0.05, right=0.99, top=0.95)


if __name__ == "__main__":
    main()
