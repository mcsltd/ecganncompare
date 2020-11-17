# coding=utf-8
import os
import json
from datetime import datetime
from collections import OrderedDict, defaultdict


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


class TotalResult():
    def __init__(self):
        self.total_count = 0
        self.match_count = 0
        self.ref_codes_count = 0
        self.test_codes_count = 0


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


def main():
    try:
        ref_input, other_input = _parse_args(os.sys.argv)
        if ref_input is None:
            _compare_inside_folder(os.path.dirname(os.path.abspath(__file__)))
        else:
            _check_input(ref_input, other_input)
            if os.path.isdir(ref_input):
                _compare_folders(ref_input, other_input)
            else:
                _compare_filesets([ref_input], [other_input])
    except Error as exc:
        print("Error: {0}\n".format(exc))
        os.system("pause")


def _check_folder_data(json_set):
    def _check_field_value(dataset, fieldname):
        message_template = "Files from one folder must have the same '{0}'"
        value = dataset[0][fieldname]
        if any(x[fieldname] != value for x in dataset):
            raise Error(message_template.format(fieldname))
    _check_field_value(json_set, Text.ANNOTATOR)
    _check_field_value(json_set, Text.CONCLUSION_THESAURUS)


def _read_json_folder(dirname):
    all_files = _get_all_files(dirname, ".json")
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
    if len(args) < 3:
        return None, None
    return tuple(args[:2])


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


def _check_input(ref_input, other_input):
    if not (os.path.exists(ref_input) and os.path.exists(other_input)):
        raise Error("Path not exists")
    same_type = (os.path.isfile(ref_input) and os.path.isfile(other_input) or
                 os.path.isdir(ref_input) and os.path.isdir(other_input))
    if not same_type:
        raise Error("Both paths must point either to files or folders.")


def _compare_folders(ref_input, other_input):
    ref_files = _read_json_folder(ref_input)
    other_files = _read_json_folder(other_input)
    return _compare_datasets(ref_files, other_files)


def _compare_filesets(ref_fileset, other_fileset):
    ref_data = _read_json_files(ref_fileset)
    other_data = _read_json_files(other_fileset)
    return _compare_datasets(ref_data, other_data)


def _compare_datasets(ref_data, other_data):
    _check_folder_data(ref_data)
    _check_folder_data(other_data)
    record_reports = _create_reports(ref_data, other_data)
    general_report = _create_general_report(record_reports)
    text = _write_report(general_report)
    return text


def _read_json(filename):
    with open(filename, "rt") as fin:
        return json.load(fin)


def _create_record_report(code_pairs, ref_data, other_data):
    report = OrderedDict()
    report[Text.RECORD_ID] = ref_data[Text.RECORD_ID]
    report[Text.DATABASE] = ref_data[Text.DATABASE]
    report[Text.CONCLUSION_THESAURUS] = ref_data[Text.CONCLUSION_THESAURUS]
    report[Text.REF_ANNOTATOR] = ref_data[Text.ANNOTATOR]
    report[Text.TEST_ANNOTATOR] = other_data[Text.ANNOTATOR]

    ref_codes_count = 0
    match_count = 0
    test_codes_count = 0
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


def _create_reports(ref_data, other_data):
    reports = []
    other_data = _dataset_to_table(other_data)
    for ref_item in ref_data:
        db = ref_item[Text.DATABASE]
        name = ref_item[Text.RECORD_ID]
        try:
            other_item = other_data[db][name]
        except KeyError:
            continue
        code_pairs = _merge_codes(ref_item[Text.CONCLUSIONS],
                                  other_item[Text.CONCLUSIONS])
        new_report = _create_record_report(code_pairs, ref_item, other_item)
        reports.append(new_report)
    return reports


def _dataset_to_table(dataset):
    table = defaultdict(dict)
    for item in dataset:
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[database][record] = item
    return table


def _create_general_report(records_reports):
    report = _report_header()
    report[Text.REF_ANNOTATOR] = records_reports[0][Text.REF_ANNOTATOR]
    report[Text.TEST_ANNOTATOR] = records_reports[0][Text.TEST_ANNOTATOR]
    report[Text.CONCLUSION_THESAURUS] = records_reports[0][Text.CONCLUSION_THESAURUS]
    report[Text.RECORDS_COUNT] = len(records_reports)

    total = TotalResult()
    for item in records_reports:
        total.match_count += item[Text.MATCH_COUNT]
        total.ref_codes_count += item[Text.REF_ANNOTATIONS]
        total.test_codes_count += item[Text.TEST_ANNOTATIONS]
        total.total_count += len(item[Text.CONCLUSIONS])
        del item[Text.TEST_ANNOTATOR]
        del item[Text.REF_ANNOTATOR]
        del item[Text.CONCLUSION_THESAURUS]

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
    report[Text.RECORDS] = records_reports
    return report


def _get_all_files(dirname, ext=""):
    all_paths = (os.path.join(dirname, x) for x in os.listdir(dirname))
    return [p for p in all_paths if os.path.isfile(p) and p.endswith(ext)]


def _compare_inside_folder(dirname):
    report_filename = os.path.join(dirname, "cmp_result.txt")
    if os.path.exists(report_filename):
        os.remove(report_filename)
    all_jsons = _read_json_folder(dirname)
    groups = _group_by(all_jsons, Text.ANNOTATOR)
    if len(groups) < 2:
        message_format = (
            "Cannot compare files in folder {0}. Prepare a folder or "
            "explicitly specify two folders."
        )
        raise Error(message_format.format(dirname))
    ref_data, other_data = _select_comparing_groups(groups)
    report = _compare_datasets(ref_data, other_data)
    with open(report_filename, "wt") as fout:
        fout.write(report)
    os.system("pause")


def _group_by(dataset, fieldname):
    groups = defaultdict(list)
    for data in dataset:
        groups[data[fieldname]].append(data)
    return groups


def _select_comparing_groups(groups):
    # TODO: select ref_data by date (older)
    if len(groups) == 2:
        return tuple(groups.values())
    raise Error(
        "Comparison of more than two annotators is not supported")


def _create_report(ref_data, other_data):
    report = _report_header()
    report[Text.REF_ANNOTATOR] = ref_data[0][Text.ANNOTATOR]
    report[Text.TEST_ANNOTATOR] = other_data[0][Text.ANNOTATOR]
    report[Text.CONCLUSION_THESAURUS] = ref_data[0][Text.CONCLUSION_THESAURUS]
    report[Text.RECORDS_COUNT] = len(ref_data)

    records_count = 0
    other_data = _dataset_to_table(other_data)
    total = TotalResult()
    for item in ref_data:
        total.match_count += item[Text.MATCH_COUNT]
        total.ref_codes_count += item[Text.REF_ANNOTATIONS]
        total.test_codes_count += item[Text.TEST_ANNOTATIONS]
        total.total_count += len(item[Text.CONCLUSIONS])
        del item[Text.TEST_ANNOTATOR]
        del item[Text.REF_ANNOTATOR]
        del item[Text.CONCLUSION_THESAURUS]

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
    report[Text.RECORDS] = records_reports
    return report


if __name__ == "__main__":
    main()
