# coding=utf-8
import os
import json
from datetime import datetime
from collections import OrderedDict, defaultdict, Counter, namedtuple
import argparse


class Text(object):
    PROGRAM_NAME = "ecganncmp"
    PROGRAM_VERSION = "1.0"
    COMPANY_INFO = "Medical computer systems (c) {0} - www.mks.ru".format(
        datetime.now().year
    )
    DATABASE = "database"
    RECORD_ID = "record"
    CONCLUSION_THESAURUS = "conclusionThesaurus"
    CONCLUSIONS = "conclusions"
    REF_ANNOTATIONS = "refAnnotations"
    TEST_ANNOTATIONS = "testAnnotations"
    MATCH_COUNT = "matchCount"
    REF_ANNOTATOR = "refAnnotator"
    TEST_ANNOTATOR = "testAnnotator"
    ANNOTATOR = "annotator"
    RECORDS_COUNT = "recordsCount"
    VALUE = "value"
    RECORDS = "records"
    SENSITIVITY = "sensitivity"
    SPECIFICITY = "specificity"
    MISSES_COUNT = "missesCount"
    TYPE = "type"
    CMPRESULT = "cmpresult"


class TotalResult(object):
    def __init__(self):
        self.total_count = 0
        self.match_count = 0
        self.ref_codes_count = 0
        self.test_codes_count = 0


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


InputData = namedtuple("InputData", ["ref_path", "test_path", "dirname"])


def main():
    try:
        input_data = _parse_args(os.sys.argv)
        cmpresult = _handle_input_data(input_data)
        _write_report(cmpresult)
    except Error as exc:
        print("Error: {0}\n".format(exc))


def _handle_input_data(input_data):
    if input_data.dirname is not None:
        cmpresult = _compare_inside_folder(input_data.dirname)
        _write_results_to_files(input_data.dirname, *cmpresult)
        return cmpresult
    _check_input(input_data.ref_path, input_data.test_path)
    if os.path.isdir(input_data.ref_path):
        return _compare_folders(input_data.ref_path, input_data.test_path)
    return _compare_filesets([input_data.ref_path], [input_data.test_path])


def _check_folder_data(json_set):
    def _check_field_value(dataset, fieldname):
        message_template = "Files from one folder must have the same '{0}'"
        value = dataset[0][fieldname]
        if any(x[fieldname] != value for x in dataset):
            raise Error(message_template.format(fieldname))
    _check_field_value(json_set, Text.ANNOTATOR)
    _check_field_value(json_set, Text.CONCLUSION_THESAURUS)


def _read_json_folder(dirname):
    all_files = _get_all_jsons(dirname)
    return _read_json_files(all_files)


def _read_json_files(filenames):
    results = []
    for filename in filenames:
        try:
            results.append(_read_json(filename))
        except ValueError:
            continue
    return results


def _parse_args(args):
    default_data_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data")

    parser = argparse.ArgumentParser(description="Annotations comparing")
    parser.add_argument("path", nargs="?", default=default_data_folder,
                        help="Path to folder with all files or reference "
                             "file/folder")
    parser.add_argument("test_path", nargs="?",
                        help="Path to test file/folder")
    data = parser.parse_args(args[1:])
    if data.test_path is None:
        return InputData(None, None, data.path)
    return InputData(data.path, data.test_path, None)


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


def _report_header():
    return OrderedDict([
        (Text.TYPE, "cmpresult"),
        ("program", {
            "name": Text.PROGRAM_NAME,
            "version": Text.PROGRAM_VERSION
        }),
        ("company", Text.COMPANY_INFO),
        ("date", datetime.utcnow().isoformat() + "Z")
    ])


def _write_report(report, writable=None):
    if writable is None:
        writable = os.sys.stdout
    text = json.dumps(report, indent=2)
    writable.write(text + "\n")
    return text


def _check_input(*input_paths):
    def _for_all_paths(predicate):
        return all(predicate(p) for p in input_paths)

    if not _for_all_paths(os.path.exists):
        raise Error("Path not exists")

    if not (_for_all_paths(os.path.isfile) or _for_all_paths(os.path.isdir)):
        raise Error("Both paths must point either to files or folders.")


def _compare_folders(ref_input, other_input):
    ref_files = _get_all_jsons(ref_input)
    other_files = _get_all_jsons(other_input)
    return _compare_filesets(ref_files, other_files)


def _compare_filesets(ref_fileset, other_fileset):
    ref_data = _read_json_files(ref_fileset)
    other_data = _read_json_files(other_fileset)
    return _compare_datasets(ref_data, other_data)


def _compare_datasets(ref_data, other_data):
    _check_folder_data(ref_data)
    _check_folder_data(other_data)
    return _create_report(ref_data, other_data)


def _read_json(filename):
    with open(filename, "rt") as fin:
        return json.load(fin)


def _dataset_to_table(dataset):
    table = defaultdict(dict)
    for item in dataset:
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[database][record] = item
    return dict(table)


def _get_all_jsons(dirname):
    all_paths = (os.path.join(dirname, x) for x in os.listdir(dirname))
    return [p for p in all_paths if os.path.isfile(p) and p.endswith(".json")]


def _compare_inside_folder(dirname):
    all_jsons = _read_json_folder(dirname)
    all_jsons = _remove_results(all_jsons)
    all_jsons, _ = _remove_deviations(all_jsons, Text.CONCLUSION_THESAURUS)
    groups = _group_by(all_jsons, Text.ANNOTATOR)
    if len(groups) < 2:
        message_format = (
            "Cannot compare files in folder {0}. Prepare a folder or "
            "explicitly specify two folders."
        )
        raise Error(message_format.format(dirname))
    data_pairs = _select_comparing_pairs(groups)
    return [_compare_datasets(ref_data, other_data)
            for ref_data, other_data in data_pairs]


def _group_by(dataset, fieldname):
    groups = defaultdict(list)
    for data in dataset:
        groups[data[fieldname]].append(data)
    return groups


def _select_comparing_groups(groups):
    # TODO: select ref_data by date (older)
    result = groups.values()
    if len(groups) > 2:
        result = sorted(result, key=len, reverse=True)[:2]
        os.sys.stderr.write(
            "Warning! Comparison of more than two annotators is not "
            "supported!\n"
        )
    return tuple(result)


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


def _create_report(ref_data, other_data):
    report = _report_header()
    report[Text.REF_ANNOTATOR] = ref_data[0][Text.ANNOTATOR]
    report[Text.TEST_ANNOTATOR] = other_data[0][Text.ANNOTATOR]
    report[Text.CONCLUSION_THESAURUS] = ref_data[0][Text.CONCLUSION_THESAURUS]

    other_data = _dataset_to_table(other_data)
    total = TotalResult()
    records = []
    for ref_item in ref_data:
        # TODO: handle pairs with no common records
        db = ref_item[Text.DATABASE]
        rec_id = ref_item[Text.RECORD_ID]
        try:
            other_item = other_data[db][rec_id]
        except KeyError:
            continue
        record_result = _compare_record_annotations(ref_item, other_item)
        total.match_count += record_result[Text.MATCH_COUNT]
        total.ref_codes_count += record_result[Text.REF_ANNOTATIONS]
        total.test_codes_count += record_result[Text.TEST_ANNOTATIONS]
        total.total_count += len(record_result[Text.CONCLUSIONS])
        records.append(record_result)

    report[Text.RECORDS_COUNT] = len(records)
    report[Text.REF_ANNOTATIONS] = total.ref_codes_count
    report[Text.TEST_ANNOTATIONS] = total.test_codes_count
    sensitivity = float(total.match_count) / total.ref_codes_count
    report[Text.SENSITIVITY] = {
        Text.MATCH_COUNT: total.match_count,
        Text.VALUE: sensitivity * 100
    }
    excess_count = total.test_codes_count - total.match_count
    specificity = float(excess_count) / total.test_codes_count
    report[Text.SPECIFICITY] = {
        Text.MISSES_COUNT: excess_count,
        Text.VALUE: specificity * 100
    }
    report[Text.RECORDS] = records
    return report


def _compare_record_annotations(ref_data, other_data):
    report = OrderedDict()
    report[Text.RECORD_ID] = ref_data[Text.RECORD_ID]
    report[Text.DATABASE] = ref_data[Text.DATABASE]

    ref_codes_count = 0
    match_count = 0
    test_codes_count = 0
    code_pairs = _merge_codes(ref_data[Text.CONCLUSIONS],
                              other_data[Text.CONCLUSIONS])
    for pair in code_pairs:
        if pair[0] is not None:
            ref_codes_count += 1
            if pair[0] == pair[1]:
                match_count += 1
        if pair[1] is not None:
            test_codes_count += 1
    report[Text.REF_ANNOTATIONS] = ref_codes_count
    report[Text.TEST_ANNOTATIONS] = test_codes_count
    report[Text.MATCH_COUNT] = match_count
    report[Text.CONCLUSIONS] = code_pairs
    return report


def _write_results_to_files(dirname, *results):
    for cmpres in results:
        filename = "{0}-{1}.json".format(
            cmpres[Text.TEST_ANNOTATOR], cmpres[Text.REF_ANNOTATOR])
        filename = os.path.join(dirname, filename)
        with open(filename, "w") as fout:
            _write_report(cmpres, fout)


def _remove_results(dataset):
    return [d for d in dataset
            if Text.TYPE not in d or d[Text.TYPE] != Text.CMPRESULT]


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


if __name__ == "__main__":
    main()
