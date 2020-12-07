# coding=utf-8
import os
import sys
import json
from collections import namedtuple, defaultdict, Counter, OrderedDict
import argparse
import codecs
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
    

class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


ComparingSet = namedtuple("ComparingSet", [
    "annotator", "matches_counts", "records_count"
])


InputData = namedtuple("InputData", ["paths", "thesaurus"])


_WINDOW_TITLE = "Annotations comparing"
_MAX_HISTOGRAM_COUNT = 10
_MAX_ANNOTATORS_IN_SET = 5
_LANGUAGE_RUS = "ru"


def main():
    input_data = _parse_args(sys.argv)
    cmpsets = _read_comparing_sets(input_data)
    # TODO: get ignored annotators
    _plot_comparing_sets(cmpsets, input_data.thesaurus)
    plt.show()


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


def _get_title(ref_annotator, test_annotator):
    return "Comparing {0} and {1} annotations".format(
        ref_annotator, test_annotator
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
    return groups


def _create_comparing_sets(groups):
    cmpgroups = sorted(groups.items(), reverse=True,
                       key=(lambda pair: len(pair[1])))
    cmpgroups = [(gn, _dataset_to_table(ds))
                 for gn, ds in cmpgroups[:_MAX_ANNOTATORS_IN_SET]]
    cmpsets = []
    for annr, dtable in cmpgroups:
        matches_counts = {}
        for other_annr, other_dtable in cmpgroups:
            if annr == other_annr:
                continue
            counts = _count_matches(dtable, other_dtable)
            if counts:
                matches_counts[other_annr] = counts
        cmpsets.append(ComparingSet(
            annr, matches_counts, len(groups[annr])))
    return cmpsets


def _dataset_to_table(dataset):
    table = defaultdict(dict)
    for item in dataset:
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[database][record] = item
    return dict(table)


def _print_comparing_results(results, header=None):
    if header is not None:
        print(header)
    for cresult in results:
        print("Comparing {0} with {1}".format(
            cresult.annotator, ", ".join(cresult.test_annotators)
        ))
        print("Records count: %d" % cresult.records_count)
        ref_count = _count_items(cresult.codes, lambda x: x[0] is not None)
        print("Reference annotations count: %d" % ref_count)
        test_count = _count_items(cresult.codes, lambda x: x[1] is not None)
        print("Test annotations count: %d" % test_count)
        matches_count = _count_items(cresult.codes, lambda x: x[0] == x[1])
        print("Matches: %d" % matches_count)
        misses_count = _count_items(cresult.codes, lambda x: x[0] != x[1])
        print("Misses: %d\n" % misses_count)


def _count_items(iterable, predicate):
    return sum(1 for x in iterable if predicate(x))


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
    return result


def _remove_results(dataset):
    return [d for d in dataset
            if Text.TYPE not in d or d[Text.TYPE] != Text.CMPRESULT]


def _print_bad_results(cresults):
    message_format = "Cannot compare {0} with {1}, common records not found"
    for cr in cresults:
        print(message_format.format(cr.ref_annotator, cr.test_annotator))
    print("")


def _print_info(results, bad_results, excess_results):
    _print_comparing_results(results)
    if bad_results:
        _print_bad_results(bad_results)
    if not excess_results:
        return
    header = (
        "Cannot show more than {0} histograms, the following annotator "
        "pairs not showed: "
    )
    _print_comparing_results(
        excess_results, header.format(_MAX_HISTOGRAM_COUNT))


def _count_matches(dtable, other_dtable):
    counts = defaultdict(int)
    for db_name in dtable:
        for rec_name in dtable[db_name]:
            try:
                other_data = other_dtable[db_name][rec_name]
            except KeyError:
                continue
            other_codes_set = set(other_data[Text.CONCLUSIONS])
            for code in dtable[db_name][rec_name][Text.CONCLUSIONS]:
                if code in other_codes_set:
                    counts[code] += 1
    return counts


def _plot_comparing_sets(comparing_sets, thesaurus_path=None):
    # TODO: same scale for all figures
    # TODO: titles, text instead of codes
    thesaurus = None
    if thesaurus_path is not None:
        thesaurus = _parse_thesaurus(thesaurus_path)
    max_x = _get_max_matches_count(comparing_sets) + 2
    for cmpset in comparing_sets:
        _plot_cmpset_histogram(cmpset, thesaurus, xmax=max_x)


def _read_comparing_set(cmpresult_path):
    data = _read_json(cmpresult_path)
    code_pairs = _to_flat(d[Text.CONCLUSIONS] for d in data[Text.RECORDS])
    match_counts = defaultdict(
        int, Counter(p[0] for p in code_pairs if p[0] == p[1]))
    return ComparingSet(
        annotator=data[Text.REF_ANNOTATOR],
        matches_counts={data[Text.TEST_ANNOTATOR], match_counts},
        records_count=len(data[Text.RECORDS])
    )


def _read_folder_datagroups(dirname):
    all_jsons = _read_json_folder(dirname)
    all_jsons = _remove_results(all_jsons)
    all_jsons, bad_json = _remove_deviations(
        all_jsons, Text.CONCLUSION_THESAURUS)
    _print_removed_items(bad_json, Text.CONCLUSION_THESAURUS)
    return _group_by(all_jsons, Text.ANNOTATOR)
    # TODO: move check into another function
    # if len(groups) < 2:
    #     message_format = (
    #         "Cannot compare files in folder {0}. Prepare a folder or "
    #         "explicitly specify result files."
    #     )
    #     raise Error(message_format.format(dirname))


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
    results += _create_comparing_sets(groups)
    return results


def _plot_cmpset_histogram(cmpset, thesaurus=None, lang=None, xmax=None):
    dframe = pandas.DataFrame.from_dict(cmpset.matches_counts)
    if not thesaurus:
        dframe.sort_index(inplace=True)
    else:
        dframe = dframe.loc[(k for k in thesaurus.keys() if k in dframe.index)]
        dframe.index = [thesaurus[k] for k in dframe.index]
    fig = plt.figure()
    fig.canvas.set_window_title(_get_window_title(lang))
    axes = plt.gca()
    # NOTE: barh() plor bars in reverse order
    dframe[::-1].plot.barh(ax=axes)
    plt.title(_get_figure_title(cmpset, lang))

    if thesaurus is not None:
        plt.subplots_adjust(left=0.4, bottom=0.05, right=0.99, top=0.95)
        axes.tick_params(axis="y", labelsize=8)
    if xmax is not None:
        plt.xlim(xmax=xmax)


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
        title_format = u"Количество заключений, совпавших с аннотатором {0}"
    else:
        title_format = "Number of conclusions that matched annotator {0}"
    return title_format.format(cmpset.annotator)


if __name__ == "__main__":
    main()
