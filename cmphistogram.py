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


ComparingResult = namedtuple("ComparingResult", [
    "ref_annotator", "test_annotator", "codes", "records_count"
])


ComparingSet = namedtuple("ComparingSet", [
    "annotator", "matches_counts", "records_count"
])


InputData = namedtuple("InputData", ["paths", "thesaurus"])


_WINDOW_TITLE = "Annotations comparing"
_MAX_HISTOGRAM_COUNT = 10


def main():
    input_data = _parse_args(sys.argv)
    cmpresults = _read_comparing_results(input_data)
    cmpresults, bad_results = _split_good_results(cmpresults)
    cmpresults, not_showed_results = _plot_comparing_results(
        cmpresults, input_data.thesaurus)
    _print_info(cmpresults, bad_results, not_showed_results)
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


def _read_comparing_result(filename):
    with open(filename, "rt") as fin:
        data = json.load(fin)
    codes = list(_to_flat(d[Text.CONCLUSIONS] for d in data[Text.RECORDS]))
    result = ComparingResult(
        ref_annotator=data[Text.REF_ANNOTATOR],
        test_annotator=data[Text.TEST_ANNOTATOR],
        codes=codes,
        records_count=len(data[Text.RECORDS])
    )
    return result


def _plot_histogram(cresult, thesaurus=None):
    counts = defaultdict(int)
    for pair in cresult.codes:
        code = _get_code(pair)
        if pair[0] == pair[1]:
            counts[code] += 1
    frame = pandas.DataFrame.from_dict(counts, orient="index")
    frame.columns = ["Matches"]
    if thesaurus is None:
        frame.sort_index(inplace=True)
    else:
        frame = frame.loc[(k for k in thesaurus if k in frame.index)]
        frame.index = [thesaurus[k] for k in frame.index]
    # NOTE: barh() plor bars in reverse order
    frame[::-1].plot.barh(ax=plt.gca(), legend=True)
    if thesaurus is not None:
        plt.subplots_adjust(left=0.4, bottom=0.05, right=0.99, top=0.95)
        plt.tick_params(axis="y", labelsize=8)
    title = _get_title(cresult.ref_annotator, cresult.test_annotator)
    plt.title(title + (". Records count: %d" % cresult.records_count))
    plt.gcf().canvas.set_window_title(_WINDOW_TITLE)


def _get_code(row):
    return next(x for x in row if x is not None)


def _get_title(ref_annotator, test_annotator):
    return "Comparing {0} and {1} annotations".format(
        ref_annotator, test_annotator
    )


def _plot_comparing_results(cresults, thesaurus_path=None):
    not_showed = []
    if len(cresults) > _MAX_HISTOGRAM_COUNT:
        cresults = list(sorted(cresults, key=(lambda x: len(x.codes)),
                               reverse=True))
        not_showed = cresults[_MAX_HISTOGRAM_COUNT:]
        cresults = cresults[:_MAX_HISTOGRAM_COUNT]
    thesaurus = None
    if thesaurus_path is not None:
        thesaurus = _parse_thesaurus(thesaurus_path)
    for cr in cresults:
        plt.figure()
        _plot_histogram(cr, thesaurus)
    return cresults, not_showed


def _compare_inside_folder(dirname):
    all_jsons = _read_json_folder(dirname)
    all_jsons = _remove_results(all_jsons)
    all_jsons, bad_json = _remove_deviations(all_jsons,
                                             Text.CONCLUSION_THESAURUS)
    _print_removed_items(bad_json, Text.CONCLUSION_THESAURUS)
    groups = _group_by(all_jsons, Text.ANNOTATOR)
    if len(groups) < 2:
        message_format = (
            "Cannot compare files in folder {0}. Prepare a folder or "
            "explicitly specify result files."
        )
        raise Error(message_format.format(dirname))
    comparing_pairs = _select_comparing_pairs(groups)
    return [_compare_datasets(p[0], p[1]) for p in comparing_pairs]


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
        return json.load(fin)


def _group_by(iterable_data, fieldname):
    groups = defaultdict(list)
    for data in iterable_data:
        groups[data[fieldname]].append(data)
    return groups


def _select_comparing_pairs(groups):
    # TODO: select ref_data by date (older)
    groups_count = len(groups)
    if groups_count == 2:
        return [tuple(groups.values())]
    pairs = []
    names = list(groups.keys())
    for i, gname in enumerate(names):
        ref_data = groups[gname]
        for other_name in names[i + 1:]:
            pairs.append((ref_data, groups[other_name]))
    return pairs


def _create_comparing_sets(groups):
    MAX_ANNOTATORS_IN_SET = 5
    groups = sorted(groups.items(), reverse=True,
                    key=(lambda pair: len(pair[1])))
    cmpgroups = [(gn, _dataset_to_table(ds))
                 for gn, ds in groups[:MAX_ANNOTATORS_IN_SET]]
    cmpsets = []
    for annr, dtable in cmpgroups:
        matches_counts = {}
        for other_annr, other_dtable in cmpgroups:
            if annr == other_annr:
                continue
            matches_counts[other_annr] = _count_mathes(dtable, other_dtable)
        cmpsets.append(ComparingSet(
            annr, matches_counts, len(groups[annr])))
    return cmpsets


def _compare_datasets(ref_data, other_data):
    _check_dataset(ref_data)
    _check_dataset(other_data)
    code_pairs, records_count = _create_code_pairs(ref_data, other_data)
    return ComparingResult(
        ref_data[0][Text.ANNOTATOR],
        other_data[0][Text.ANNOTATOR],
        code_pairs,
        records_count
    )


def _check_dataset(dataset):
    def _check_field_value(dataset, fieldname):
        message_template = "Files from one folder must have the same '{0}'"
        value = dataset[0][fieldname]
        if any(x[fieldname] != value for x in dataset):
            raise Error(message_template.format(fieldname))
    _check_field_value(dataset, Text.ANNOTATOR)
    _check_field_value(dataset, Text.CONCLUSION_THESAURUS)


gdef _create_code_pairs(ref_data, other_data):
    code_pairs = []
    records_count = 0
    other_data = _dataset_to_table(other_data)
    for ref_item in ref_data:
        db = ref_item[Text.DATABASE]
        name = ref_item[Text.RECORD_ID]
        try:
            other_item = other_data[db][name]
        except KeyError:
            continue
        code_pairs += _merge_codes(ref_item[Text.CONCLUSIONS],
                                   other_item[Text.CONCLUSIONS])
        records_count += 1
    return code_pairs, records_count


def _dataset_to_table(dataset):
    table = defaultdict(dict)
    for item in dataset:
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[database][record] = item
    return dict(table)


def _merge_codes(codes, other_codes):
    codes = sorted(codes)
    other_codes = set(other_codes)
    code_pairs = []
    for code in codes:
        if code in other_codes:
            code_pairs.append((code, code))
        else:
            code_pairs.append((code, None))
    other_codes.difference_update(codes)
    for code in other_codes:
        code_pairs.append((None, code))
    return code_pairs


def _print_comparing_results(results, header=None):
    if header is not None:
        print(header)
    for cresult in results:
        print("Comparing {0} with {1}".format(
            cresult.ref_annotator, cresult.test_annotator
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


def _split_good_results(cresults):
    good, bad = [], []
    for cr in cresults:
        if cr.records_count == 0:
            bad.append(cr)
        else:
            good.append(cr)
    return good, bad


def _print_bad_results(cresults):
    message_format = "Cannot compare {0} with {1}, common records not found"
    for cr in cresults:
        print(message_format.format(cr.ref_annotator, cr.test_annotator))
    print("")


def _read_comparing_results(input_data):
    results = []
    for path in input_data.paths:
        if os.path.isfile(path):
            results.append(_read_comparing_result(path))
        else:
            results += _compare_inside_folder(path)
    return results


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


if __name__ == "__main__":
    main()
