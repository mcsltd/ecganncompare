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


def main():
    data = _parse_args(sys.argv)
    all_data = _read_folders(data.input_folders)
    _print_folders_names(data.input_folders)
    all_data = _remove_results(all_data)
    all_data, deviations = _remove_deviations(
        all_data, Text.CONCLUSION_THESAURUS)
    if deviations:
        _print_removed_items(deviations, Text.CONCLUSION_THESAURUS)
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
    return data


def _read_folders(folders):
    all_data = []
    for dirname in folders:
        folder_data = _read_json_folder(dirname)
        all_data += folder_data
    return all_data


def _plot_histogram(codes_groups, datagroups_info, thesaurus_path=None):
    dataframe = _create_dataframe(codes_groups)
    if thesaurus_path is None:
        dataframe.sort_index(inplace=True)
        thesaurus = _create_thesaurus("unknown")
    else:
        thesaurus = _parse_thesaurus(thesaurus_path)
        dataframe = _prepare_dataframe(dataframe, thesaurus.items)
    # NOTE: barh() plor bars in reverse order
    dataframe[::-1].plot.barh(ax=plt.gca(), width=0.75, legend=False)
    title = (_get_title(thesaurus.lang) + ". " +
             _get_title_tail(datagroups_info, thesaurus.lang))
    plt.title(title)
    plt.gcf().canvas.set_window_title(_get_window_title(thesaurus.lang))
    legend_labels = _get_legend_labels(
        dataframe.columns, thesaurus.lang, datagroups_info)
    plt.legend(legend_labels)
    if thesaurus_path is not None:
        plt.subplots_adjust(left=0.4, bottom=0.05, right=0.99, top=0.95)
        _set_y_fontsize(plt.gca(), 8)


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


def _set_y_fontsize(axes, value):
    axes.tick_params(axis="y", labelsize=value)


def _prepare_dataframe(df, thesaurus):
    df = df.loc[(k for k in thesaurus if k in df.index)]
    df.index = [thesaurus[k] for k in df.index]
    return df


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


def _create_thesaurus(label, lang=None, items=None, groups=None):
    if items is None:
        items = {}
    if groups is None:
        groups = {}
    return Thesaurus(label, lang, items, groups)


def _plot_dataframe(dataframe, wide_ylabels):
    # NOTE: barh() plor bars in reverse order
    plt.figure()
    dataframe[::-1].plot.barh(ax=plt.gca(), width=0.75, legend=False)
    if wide_ylabels is not None:
        plt.subplots_adjust(left=0.4, bottom=0.05, right=0.99, top=0.95)
        _set_y_fontsize(plt.gca(), 8)


if __name__ == "__main__":
    main()
