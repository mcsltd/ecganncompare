# coding=utf-8
import os
import sys
import json
from collections import defaultdict, Counter, OrderedDict, namedtuple
import argparse
import traceback

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
    input_data = _parse_args(sys.argv)
    try:
        _process_input(input_data)
    except Error as err:
        print("Error: {0}".format(err))
    except Exception as exc:
        gettrace = getattr(os.sys, 'gettrace', None)
        if gettrace():
            raise
        log_filename = "errors-log.txt"
        message = "Fatal error! {0}: {1}. See details in file '{2}'."
        print(message.format(type(exc).__name__, exc, log_filename))
        with open(log_filename, "wt") as log:
            log.write(traceback.format_exc())


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


def _plot_histogram(codes_groups, datagroups_info, records_count, thesaurus_path=None):
    dataframe = _create_dataframe(codes_groups)
    if thesaurus_path is not None:
        thesaurus = _parse_thesaurus(thesaurus_path)
    else:
        thesaurus = _create_thesaurus()
        dataframe.sort_index(inplace=True)
    _plot_common_histogram(dataframe, thesaurus)
    _add_titles(
        _get_common_histogram_title(records_count, thesaurus.lang),
        _get_window_title(thesaurus.lang)
    )
    if not thesaurus.items:
        plt.figure()
        _plot_dataframe(dataframe)
        _add_info_to_plot(
            dataframe.columns, datagroups_info, records_count, thesaurus.lang)
        return
    max_count = dataframe.to_numpy().max()
    dataframes = _split_dataframe(dataframe, thesaurus)
    df_groups = _group_dataframes(dataframes)
    if len(df_groups) > plt.rcParams["figure.max_open_warning"]:
        plt.rcParams.update({'figure.max_open_warning': 0})
    for group in df_groups:
        plt.figure()
        for i, name in enumerate(group):
            plt.subplot(len(group), 1, i + 1)
            frame = group[name]
            _plot_dataframe(frame)
            _wide_ylabels_padding()
            _add_info_to_plot(
                frame.columns, datagroups_info, records_count, thesaurus.lang)
            plt.title(name)
            plt.xlim(xmax=(max_count + 2))


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
        data[Text.LANGUAGE].lower(),
        items,
        groups
    )


def _remove_results(dataset):
    return [d for d in dataset
            if Text.TYPE not in d or d[Text.TYPE] != Text.CMPRESULT]


def _split_dataframe(df, thesaurus):
    subframes = OrderedDict()
    for group in thesaurus.groups:
        name = "{0}-{1}".format(min(group), max(group))
        frame = df.loc[(k for k in group if k in df.index)]
        frame = frame.loc[:, frame.sum() > 0]
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
    records = defaultdict(set)
    for annotator in data_groups:
        annotator_data = data_groups[annotator]
        codes_count = 0
        for data_item in annotator_data:
            codes_count += len(data_item[Text.CONCLUSIONS])
            records[data_item[Text.DATABASE]].add(data_item[Text.RECORD_ID])
        infos[annotator] = DatagroupInfo(
            annotator,
            len(annotator_data),
            codes_count,
            annotator_data[0][Text.CONCLUSION_THESAURUS]
        )
    records_count = sum(len(records[db]) for db in records)
    return infos, records_count


def _get_title_tail(records_count, lang=None):
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


def _add_info_to_plot(columns, datagroups_info, records_count, lang):
    title = _get_title(lang) + ". " + _get_title_tail(records_count, lang)
    plt.suptitle(title)
    plt.gcf().canvas.set_window_title(_get_window_title(lang))
    legend_labels = _get_legend_labels(columns, lang, datagroups_info)
    plt.legend(legend_labels)


def _wide_ylabels_padding():
    plt.subplots_adjust(left=0.4, bottom=0.05, right=0.99, top=0.95)


def _process_input(data):
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
    groups_info, records_count = _get_datagroups_info(data_groups)
    _print_groups_info(groups_info)
    codes_groups = _extract_annotators_codes(data_groups)
    _plot_histogram(codes_groups, groups_info, records_count, data.thesaurus)
    plt.show()


def _group_dataframes(dataframes, max_sum_group_size=10):
    # Remade groups order as in thesaurus
    groups = [OrderedDict()]
    for name in dataframes:
        last_group = groups[-1]
        items_len_sum = sum(len(last_group[n]) for n in last_group)
        if items_len_sum >= max_sum_group_size:
            last_group = OrderedDict()
            groups.append(last_group)
        last_group[name] = dataframes[name]
    return groups


def _plot_common_histogram(dataframe, thesaurus):
    dataframe = dataframe.sum(axis=1)
    if thesaurus.items:
        sorted_index = (k for k in thesaurus.items if k in dataframe.index)
        dataframe = dataframe.loc[sorted_index]
        dataframe.index = [thesaurus.items[k] for k in dataframe.index]
    plt.figure()
    _plot_dataframe(dataframe)
    if thesaurus.items:
        _wide_ylabels_padding()


def _add_titles(figure_title, window_title):
    plt.suptitle(figure_title)
    plt.gcf().canvas.set_window_title(window_title)


def _get_common_histogram_title(records_count, lang):
    head = (
        "The total number of uses of conclusions (distribution of "
        "conclusions). "
    )
    if lang == "ru":
        head =\
            u"Общее число использования заключений (распределение заключений). "
    return head + _get_title_tail(records_count, lang)


if __name__ == "__main__":
    main()
