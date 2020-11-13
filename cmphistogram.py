import os
import sys
import json
from collections import namedtuple, defaultdict
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


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


ComparingResult = namedtuple("ComparingResult",
                             ["ref_annotator", "test_annotator", "codes"])

_WINDOW_TITLE = "Annotations comparing"


def main():
    filenames = _parse_args(sys.argv)
    comparing_results = [_read_annotations(fname) for fname in filenames]
    _plot_comparing_results(comparing_results)
    plt.show()


def _parse_args(args):
    if len(args) < 2:
        raise RuntimeError("Not enough arguments")
    return args[1:]


def _read_annotations(filename):
    with open(filename, "rt") as fin:
        data = json.load(fin)
    codes = []
    for rec_data in data[Text.RECORDS]:
        codes.append(rec_data[Text.CONCLUSIONS])
    result = ComparingResult(
        ref_annotator=data[Text.REF_ANNOTATOR],
        test_annotator=data[Text.TEST_ANNOTATOR],
        codes=codes
    )
    return result


def _plot_histogram(cresult):
    counts = defaultdict(lambda: [0, 0])
    for rec_pairs in cresult.codes:
        for pair in rec_pairs:
            code = _get_code(pair)
            code_counts = counts[code]
            if pair[0] == pair[1]:
                code_counts[0] += 1
            else:
                code_counts[1] += 1
    df = pandas.DataFrame.from_dict(counts, orient="index").sort_index()
    df.columns = ["Matches", "Misses"]
    _plot_bidirectional_histogram(df)
    title = _get_title(cresult.ref_annotator, cresult.test_annotator)
    plt.title(title + ". Records count: {0}".format(len(cresult.codes)))
    plt.gcf().canvas.set_window_title(_WINDOW_TITLE)


def _get_code(pair):
    return pair[0] if pair[0] is not None else pair[1]


def _plot_bidirectional_histogram(dataframe):
    directions_count = 2
    default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for i, cname in enumerate(dataframe.columns[:directions_count]):
        column = dataframe[cname]
        if i == directions_count - 1:
            column = column * (-1)
        column.plot(ax=plt.gca(), kind="bar", legend=True,
                    color=default_colors[i])
    plt.axhline(c="k")
    locs, _ = plt.yticks()
    plt.yticks(locs, [abs(loc) for loc in locs])


def _get_title(ref_annotator, test_annotator):
    return "Comparing {0} and {1} annotations".format(
        ref_annotator, test_annotator
    )


def _plot_comparing_results(cresults):
    for cr in cresults:
        plt.figure()
        _plot_histogram(cr)


def _compare_inside_folder(dirname):
    all_jsons = _read_json_folder(dirname)
    groups = _group_by(all_jsons, Text.ANNOTATOR)
    if len(groups) < 2:
        message_format = (
            "Cannot compare files in folder {0}. Prepare a folder or "
            "explicitly specify result files."
        )
        raise Error(message_format.format(dirname))
    ref_data, other_data = _select_comparing_groups(groups)
    return [_compare_datasets(ref_data, other_data)]


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
    with open(filename, "rt") as fin:
        return json.load(fin)


def _group_by(iterable_data, fieldname):
    groups = defaultdict(list)
    for data in iterable_data:
        groups[data[fieldname]].append(data)
    return groups


def _select_comparing_groups(groups):
    # TODO: select ref_data by date (older)
    if len(groups) == 2:
        return tuple(groups.values())
    raise Error(
        "Comparison of more than two annotators is not supported"
    )


def _compare_datasets(ref_data, other_data):
    _check_dataset(ref_data)
    _check_dataset(other_data)
    record_reports = _create_reports(ref_data, other_data)
    return _create_general_report(record_reports)


def _check_dataset(dataset):
    def _check_field_value(dataset, fieldname):
        message_template = "Files from one folder must have the same '{0}'"
        value = dataset[0][fieldname]
        if any(x[fieldname] != value for x in dataset):
            raise Error(message_template.format(fieldname))
    _check_field_value(dataset, Text.ANNOTATOR)
    _check_field_value(dataset, Text.CONCLUSION_THESAURUS)


def _create_reports(ref_data, other_data):
    reports = []
    other_data = _dataset_to_table(other_data)
    for ref_item in ref_data:
        ths = ref_item[Text.CONCLUSION_THESAURUS]
        db = ref_item[Text.DATABASE]
        name = ref_item[Text.RECORD_ID]
        try:
            other_item = other_data[ths][db][name]
        except KeyError:
            continue
        code_pairs = _merge_codes(ref_item[Text.CONCLUSIONS],
                                  other_item[Text.CONCLUSIONS])
        new_report = _create_record_report(code_pairs, ref_item, other_item)
        reports.append(new_report)
    return reports


def _dataset_to_table(dataset):
    table = defaultdict(lambda: defaultdict(dict))
    for item in dataset:
        # TODO: must be only one thesaurus
        thesaurus = item[Text.CONCLUSION_THESAURUS]
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[thesaurus][database][record] = item
    return table


if __name__ == "__main__":
    main()
