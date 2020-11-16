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
    if filenames is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        comparing_results = _compare_inside_folder(current_dir)
    else:
        comparing_results = [_read_annotations(fname) for fname in filenames]
    _plot_comparing_results(comparing_results)
    plt.show()


def _parse_args(args):
    if len(args) < 2:
        return None
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
    for pair in cresult.codes:
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
    plt.title(title)
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
    code_pairs = _create_code_pairs(ref_data, other_data)
    return ComparingResult(
        ref_data[0][Text.ANNOTATOR],
        other_data[0][Text.ANNOTATOR],
        code_pairs
    )


def _check_dataset(dataset):
    def _check_field_value(dataset, fieldname):
        message_template = "Files from one folder must have the same '{0}'"
        value = dataset[0][fieldname]
        if any(x[fieldname] != value for x in dataset):
            raise Error(message_template.format(fieldname))
    _check_field_value(dataset, Text.ANNOTATOR)
    _check_field_value(dataset, Text.CONCLUSION_THESAURUS)


def _create_code_pairs(ref_data, other_data):
    code_pairs = []
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
    return code_pairs


def _dataset_to_table(dataset):
    table = defaultdict(lambda: defaultdict(dict))
    for item in dataset:
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[database][record] = item
    return table


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


def _print_comparint_results(*results):
    for cresult in results:
        print("Comparing {0} with {1}".format(
            cresult.ref_annotator, cresult.test_annotator
        ))
        # TODO: print records_count
        ref_count = _count_items(cresult.codes, lambda x: x[0] is not None)
        print("Reference annotations count: %d" % ref_count)
        test_count = _count_items(cresult.codes, lambda x: x[1] is not None)
        print("Test annotations count: %d" % test_count)
        matches_count = _count_items(cresult.codes, lambda x: x[0] == x[1])
        print("Matches: %d" % matches_count)
        misses_count = _count_items(cresult.codes, lambda x: x[0] != x[1])
        print("Misses: %d" % misses_count)


def _count_items(iterable, predicate):
    return sum(1 for x in iterable if predicate(x))


if __name__ == "__main__":
    main()
