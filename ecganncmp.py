# coding=utf-8
import os
import json
from datetime import datetime


class Text():
    VALUE = "Value"
    RECORDS = "Records"
    LABEL = "Label"
    LABELS = "Labels"

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


class ComparingResult():
    def __init__(self, name, codes):
        self.name = name
        self.match_count = 0
        self.ref_codes_count = 0
        self.test_codes_count = 0
        self.codes = codes


class TotalResult():
    def __init__(self):
        self.total_count = 0
        self.match_count = 0
        self.ref_codes_count = 0
        self.test_codes_count = 0

    def add(self, record_result, add_total):
        self.total_count += add_total
        self.match_count += record_result.match_count
        self.ref_codes_count += record_result.ref_codes_count
        self.test_codes_count += record_result.test_codes_count


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


def main():
    ref_input, other_input = _parse_args(os.sys.argv)
    _check_input(ref_input, other_input)
    if os.path.isdir(ref_input):
        _compare_folders(ref_input, other_input)
    else:
        _compare_files(ref_input, other_input)


def _parse_args(args):
    if len(args) < 3:
        raise RuntimeError("Not enough arguments")
    return args[1], args[2]


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


def _compare_annotations(all_annotations):
    results = []
    total = TotalResult()
    for name, code_pairs in all_annotations.items():
        record_result = ComparingResult(name, code_pairs)
        for pair in code_pairs:
            if pair[0] is not None:
                record_result.ref_codes_count += 1
                if pair[0] == pair[1]:
                    record_result.match_count += 1
            if pair[1] is not None:
                record_result.test_codes_count += 1
        total.add(record_result, len(code_pairs))
        results.append(record_result)
    return results, total


def _create_report(record_results, total, thesaurus):
    data = _init_report_data()
    data[Text.CONCLUSION_THESAURUS] = thesaurus
    data["RecordsCount"] = len(record_results)
    data[Text.REF_ANNOTATIONS] = total.ref_codes_count
    data[Text.TEST_ANNOTATIONS] = total.test_codes_count
    sensitivity = float(total.match_count) / total.ref_codes_count
    data["Sensitivity"] = {
        Text.MATCH_COUNT: total.match_count,
        Text.VALUE: sensitivity * 100
    }
    excess_count = total.test_codes_count - total.match_count
    specificity = float(excess_count) / total.test_codes_count
    data["Specificity"] = {
        "ExcessAnnotations": excess_count,
        Text.VALUE: specificity * 100
    }
    records = {}
    for rec_result in record_results:
        dict_result = {}
        dict_result[Text.MATCH_COUNT] = rec_result.match_count
        dict_result[Text.REF_ANNOTATIONS] = rec_result.ref_codes_count
        dict_result[Text.TEST_ANNOTATIONS] = rec_result.test_codes_count
        dict_result[Text.LABELS] = rec_result.codes
        records[rec_result.name] = dict_result
    data[Text.RECORDS] = records
    return data


def _init_report_data():
    return {
        "Program": {
            "Name": Text.PROGRAM_NAME,
            "Version": Text.PROGRAM_VERSION
        },
        "Company": Text.COMPANY_INFO,
        "Date": datetime.utcnow().isoformat() + "Z"
    }


def _write_report(report, writable=None):
    if writable is None:
        writable = os.sys.stdout
    text = json.dumps(report, indent=2)
    writable.write(text)


def _check_input(ref_input, other_input):
    if not (os.path.exists(ref_input) and os.path.exists(other_input)):
        raise RuntimeError("Path not exists")
    same_type = (os.path.isfile(ref_input) and os.path.isfile(other_input) or
                 os.path.isdir(ref_input) and os.path.isdir(other_input))
    if not same_type:
        raise RuntimeError("Both paths must point to files or folders")


def _compare_folders(ref_input, other_input):
    raise RuntimeError("Not implemented")


def _compare_files(ref_input, other_input):
    ref_json = _read_json(ref_input)
    other_json = _read_json(other_input)
    _check_record_info(ref_json, other_json)

    codes_pairs = _merge_codes(ref_json[Text.CONCLUSIONS],
                               other_json[Text.CONCLUSIONS])
    report = _create_record_report(codes_pairs, ref_json)
    _write_report(report)


def _read_json(filename):
    with open(filename, "rt") as fin:
        return json.load(fin)


def _check_record_info(ref_input, other_input):
    def check_field(ref_input, other_input, fieldname):
        if ref_input[fieldname] != other_input[fieldname]:
            raise Error("Incompatible '{0}' values".format(fieldname))

    check_field(ref_input, other_input, Text.DATABASE)
    check_field(ref_input, other_input, Text.RECORD_ID)
    check_field(ref_input, other_input, Text.CONCLUSION_THESAURUS)


def _create_record_report(code_pairs, record_info):
    report = _init_report_data()
    report[Text.CONCLUSION_THESAURUS] = record_info[Text.CONCLUSION_THESAURUS]
    report[Text.RECORD_ID] = record_info[Text.RECORD_ID]
    report[Text.DATABASE] = record_info[Text.DATABASE]

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


if __name__ == "__main__":
    main()
