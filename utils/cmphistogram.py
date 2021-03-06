# coding=utf-8
import os
import sys
import json
from collections import namedtuple, defaultdict, Counter, OrderedDict
import argparse
import codecs
import traceback

from matplotlib import pyplot as plt
import pandas


class Text(object):
    CONCLUSIONS = "conclusions"
    RECORDS = "records"
    REF_ANNOTATOR = "refAnnotator"
    TEST_ANNOTATOR = "testAnnotator"
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


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


ComparingSet = namedtuple("ComparingSet", [
    "annotator", "matches_counts", "records_count", "annotations_count"
])


InputData = namedtuple("InputData", ["paths", "thesaurus"])


_MAX_ANNOTATORS_COUNT = 5
_MIN_ANNOTATORS_COUNT = 2
_LANGUAGE_RUS = "ru"


def main():
    input_data = _parse_args(sys.argv)
    try:
        cmpsets = _read_comparing_sets(input_data)
        _plot_comparing_sets(cmpsets, input_data.thesaurus)
        plt.show()
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
    parser = argparse.ArgumentParser(
        description="Plot histograms for annotations comparing"
    )
    parser.add_argument("input_paths", nargs="*",
                        default=[_get_default_input_dir()],
                        help="paths to input files/folders")
    parser.add_argument("--thesaurus", help="path to thesaurus")
    data = parser.parse_args(args[1:])
    return InputData(
        data.input_paths,
        data.thesaurus
    )


def _read_json_folder(dirname):
    all_paths = (os.path.join(dirname, x) for x in os.listdir(dirname))
    all_files = [p for p in all_paths
                 if os.path.isfile(p) and p.lower().endswith(".json")]
    results = []
    for fname in all_files:
        try:
            results.append(_read_json(fname))
        except ValueError:
            continue
    return results


def _read_json(filename):
    with codecs.open(filename, "r", encoding="utf-8") as fin:
        return json.load(fin, object_pairs_hook=OrderedDict)


def _group_by(iterable_data, fieldname):
    groups = defaultdict(list)
    for data in iterable_data:
        groups[data[fieldname]].append(data)
    return dict(groups)


def _create_comparing_sets(datatables):
    cmpsets = []
    for annr in datatables:
        dtable = datatables[annr]
        matches_counts = {}
        for other_annr in datatables:
            if annr == other_annr:
                continue
            counts = _count_matches(dtable, datatables[other_annr])
            if counts:
                matches_counts[other_annr] = counts
        records_count = _get_records_count(dtable)
        ann_count = _get_annotations_count(dtable)
        cmpsets.append(ComparingSet(
            annr, matches_counts, records_count, ann_count))
    return cmpsets


def _dataset_to_table(dataset):
    table = defaultdict(dict)
    for item in dataset:
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[database][record] = item[Text.CONCLUSIONS]
    return dict(table)


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


def _print_removed_items(items, fieldname):
    for item in items:
        message = "Removed {0}-{1} with {2} = {3}".format(
            item[Text.DATABASE], item[Text.RECORD_ID], fieldname,
            item[fieldname]
        )
        print(message)
    print("")


def _get_default_input_dir():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data")


def _parse_thesaurus(filename):
    data = _read_json(filename)
    result = OrderedDict()
    for group in data[Text.GROUPS]:
        for ann in group[Text.REPORTS]:
            result[ann[Text.ID]] = ann[Text.NAME]
    return result, data[Text.LANGUAGE].lower()


def _remove_results(dataset):
    return [d for d in dataset
            if Text.TYPE not in d or d[Text.TYPE] != Text.CMPRESULT]


def _count_matches(dtable, other_dtable):
    counts = defaultdict(int)
    for db_name in dtable:
        for rec_name in dtable[db_name]:
            try:
                other_data = other_dtable[db_name][rec_name]
            except KeyError:
                continue
            other_codes_set = set(other_data)
            for code in dtable[db_name][rec_name]:
                if code in other_codes_set:
                    counts[code] += 1
    return counts


def _plot_comparing_sets(comparing_sets, thesaurus_path=None):
    thesaurus, lang = None, None
    if thesaurus_path is not None:
        thesaurus, lang = _parse_thesaurus(thesaurus_path)
    max_x = _get_max_matches_count(comparing_sets) + 2
    annr_labels = _get_legend_labels(comparing_sets, lang)
    for cmpset in comparing_sets:
        dframe = _create_dataframe(cmpset, annr_labels, thesaurus)
        fig, axes = _plot_dataframe_barh(dframe, thesaurus is not None)
        _set_titles(cmpset, fig, axes, lang)
        plt.xlim(xmax=max_x)
    return thesaurus, lang


def _read_comparing_set(cmpresult_path):
    data = _read_json(cmpresult_path)
    code_pairs = _to_flat(d for d in data[Text.RECORDS])
    code_pairs = list(code_pairs)
    match_counts = defaultdict(
        int, Counter(p[0] for p in code_pairs if p[0] == p[1]))
    ann_count = sum(1 for p in code_pairs if p[0] is not None)
    return ComparingSet(
        annotator=data[Text.REF_ANNOTATOR],
        matches_counts={data[Text.TEST_ANNOTATOR], match_counts},
        records_count=len(data[Text.RECORDS]),
        annotations_count=ann_count
    )


def _read_comparing_sets(input_data):
    results = []
    all_jsons = []
    # TODO: check input_path is filename or dirs list
    for path in input_data.paths:
        if os.path.isfile(path):
            results.append(_read_comparing_set(path))
        else:
            all_jsons += _read_json_folder(path)
    if not all_jsons:
        return results
    all_jsons = _remove_results(all_jsons)
    all_jsons, bad_json = _remove_deviations(
        all_jsons, Text.CONCLUSION_THESAURUS)
    _print_removed_items(bad_json, Text.CONCLUSION_THESAURUS)
    groups = _group_by(all_jsons, Text.ANNOTATOR)
    if len(groups) > _MAX_ANNOTATORS_COUNT:
        # TODO: select annotators by size of records intersection
        groups = sorted(groups.items(), key=(lambda pair: len(pair[1])),
                        reverse=True)
        ignored_annotators = (p[0] for p in groups[_MAX_ANNOTATORS_COUNT:])
        _print_ignored_annotators(ignored_annotators)
        groups = dict(groups[:_MAX_ANNOTATORS_COUNT])
    elif len(groups) < 2:
        message_format = (
            "Cannot less than %d annotators. Prepare a folders or "
            "explicitly specify result files."
        )
        raise Error(message_format % _MIN_ANNOTATORS_COUNT)
    dtables = _create_datatables(groups)
    results += _create_comparing_sets(dtables)
    return [r for r in results if r.matches_counts]


def _get_max_matches_count(cmpsets):
    max_count = 0
    for cmpset in cmpsets:
        for annr in cmpset.matches_counts:
            max_count = max(max_count, *cmpset.matches_counts[annr].values())
    return max_count


def _get_window_title(lang=None):
    if lang == _LANGUAGE_RUS:
        return u"Сравнение аннотаторов"
    return "Annotators comparison"


def _get_figure_title(cmpset, lang=None):
    if lang == _LANGUAGE_RUS:
        title_format =\
            u"Число заключений, совпавших с аннотатором {0} (на {1} записях)"
    else:
        title_format = (
            "Number of conclusions that matched annotator {0} "
            "(for {1} records)"
        )
    return title_format.format(cmpset.annotator, cmpset.records_count)


def _print_ignored_annotators(annotators):
    message =\
        "Cannot compare more than %d annotators, the next will be ignored:"
    print(message % _MAX_ANNOTATORS_COUNT)
    print(", ".join(annotators))


def _create_dataframe(cmpset, annr_labels, thesaurus=None):
    dframe = pandas.DataFrame.from_dict(cmpset.matches_counts)
    dframe.columns = [annr_labels[c] for c in dframe.columns]
    if not thesaurus:
        return dframe.sort_index()
    dframe = dframe.loc[(k for k in thesaurus.keys() if k in dframe.index)]
    dframe.index = [thesaurus[k] for k in dframe.index]
    return dframe


def _plot_dataframe_barh(dframe, wide_yticks):
    fig = plt.figure()
    axes = plt.gca()
    # NOTE: barh() plor bars in reverse order
    dframe[::-1].plot.barh(ax=axes)
    if wide_yticks:
        plt.subplots_adjust(left=0.4, bottom=0.05, right=0.99, top=0.95)
    return fig, axes


def _set_titles(cmpset, fig, axes, lang=None):
    fig.canvas.set_window_title(_get_window_title(lang))
    axes.set_title(_get_figure_title(cmpset, lang))


def _get_legend_labels(cmpsets, lang=None):
    annr_labels = {}
    total_ann_count = sum(x.annotations_count for x in cmpsets)
    if lang == _LANGUAGE_RUS:
        message = u"{0} ({1} заключений из {2})"
    else:
        message = "{0} ({1} conclusions from {2})"

    for cmpset in cmpsets:
        annr_labels[cmpset.annotator] = message.format(
            cmpset.annotator, cmpset.annotations_count, total_ann_count
        )
    return annr_labels


def _create_datatables(datagroups):
    return dict((annr, _dataset_to_table(datagroups[annr]))
                for annr in datagroups)


def _get_records_count(datatable):
    return sum(len(datatable[db]) for db in datatable)


def _get_annotations_count(datatable):
    return sum(len(datatable[db][rec])
               for db in datatable for rec in datatable[db])


if __name__ == "__main__":
    main()
