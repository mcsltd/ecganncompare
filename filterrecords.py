# coding=utf-8
import os
import codecs
from collections import namedtuple, OrderedDict
import json
import argparse
from distutils import file_util
import traceback


class Text(object):
    CONCLUSIONS = "conclusions"
    TYPE = "type"
    CMPRESULT = "cmpresult"
    ANNOTATOR = "annotator"
    GROUPS = "groups"
    REPORTS = "reports"
    ID = "id"
    NAME = "name"
    DATABASE = "database"
    INCLUDE = "include"
    EXCLUDE = "exclude"


_FILE_CONTAINING_DIR = os.path.dirname(os.path.abspath(__file__))
_CURRENT_WORKING_DIR = os.curdir


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


class FilterRule(object):
    def __init__(self, dbs, annotators, ids):
        self.__dbs = FilterRule.__to_lower_str_set(dbs)
        self.__annotators = FilterRule.__to_lower_str_set(annotators)
        self.__ids = FilterRule.__to_lower_str_set(ids)

    def match_all(self, annotation_data):
        return all(self.__check(annotation_data))

    def match_any(self, annotation_data):
        return any(self.__check(annotation_data))

    def __check(self, annotation_data):
        dbase = annotation_data[Text.DATABASE].lower()
        annotator = annotation_data[Text.ANNOTATOR].lower()
        conclusions = [x.lower() for x in annotation_data[Text.CONCLUSIONS]]
        return [
            FilterRule.__empty_or_contains(self.__dbs, dbase),
            FilterRule.__empty_or_contains(self.__annotators, annotator),
            FilterRule.__empty_or_contains_any(self.__ids, conclusions)
        ]

    @staticmethod
    def create(rule_settings, thesaurus_groups=None):
        return FilterRule(
            rule_settings.get(Text.DATABASE, []),
            rule_settings.get(Text.ANNOTATOR, []),
            FilterRule.__get_conclusions_id(rule_settings, thesaurus_groups)
        )

    @staticmethod
    def __to_lower_str_set(items):
        return set(str(x).lower() for x in items)

    @staticmethod
    def __empty_or_contains(items_set, key):
        return (not items_set) or (key in items_set)

    @staticmethod
    def __empty_or_contains_any(items_set, keys):
        return (not items_set) or any(x in items_set for x in keys)

    @staticmethod
    def __get_conclusions_id(rule_settings, thesaurus_groups=None):
        if Text.CONCLUSIONS not in rule_settings:
            return []
        conclusions_settings = rule_settings[Text.CONCLUSIONS]
        ids = []
        ids += conclusions_settings.get(Text.ID, [])
        groups = conclusions_settings.get(Text.GROUPS)
        if groups is None:
            return ids
        elif thesaurus_groups is None:
            raise Error("Unable to filter items by group because no thesaurus "
                        "is defined")
        for gid in groups:
            ids += thesaurus_groups[gid]
        return ids


FilterRule.EMPTY = FilterRule([], [], [])


class RecordFilter(object):
    def __init__(self, include_rules, exclude_rules):
        self.__include = include_rules
        self.__exclude = exclude_rules

    def pass_record(self, annotation_data):
        return self.__include.match_all(annotation_data) and\
            (not self.__exclude.match_any(annotation_data))

    @staticmethod
    def read(settings_path, thesaurus_path=None):
        settings = _read_json(settings_path)
        ths_groups = None
        if thesaurus_path is not None:
            ths_groups = _parse_thesaurus(thesaurus_path)
        return RecordFilter(
            RecordFilter.__create_rules(settings, Text.INCLUDE, ths_groups),
            RecordFilter.__create_rules(settings, Text.EXCLUDE, ths_groups)
        )

    @staticmethod
    def __create_rules(settings, key, thesaurus_groups=None):
        rules_settings = settings.get(key)
        if rules_settings is None:
            return FilterRule.EMPTY
        return FilterRule.create(rules_settings, thesaurus_groups)


InputData = namedtuple("InputData", [
    "paths", "settings_path", "output_dir", "thesaurus_path"
])


def main():
    try:
        input_data = _parse_args(os.sys.argv)
        _process_input(input_data)
    except Error as err:
        print("Error: {0}".format(err))
    except Exception as exc:
        log_filename = "errors-log.txt"
        message = "Fatal error! {0}: {1}. See details in file '{2}'."
        print(message.format(type(exc).__name__, exc, log_filename))
        with open(log_filename, "wt") as log:
            log.write(traceback.format_exc())


def _parse_args(args):
    default_input = "data"
    default_input = os.path.join(_FILE_CONTAINING_DIR, default_input)
    default_output = "filter_records_result"
    default_output = os.path.join(_CURRENT_WORKING_DIR, default_output)

    parser = argparse.ArgumentParser(
        description="Filter json-annotation files"
    )
    parser.add_argument("input_paths", nargs="*", default=[default_input],
                        help="paths to input folders/files")
    parser.add_argument("--settings", required=True,
                        help="path to JSON-file with filter settings")
    parser.add_argument("--output_dir", help="path to dir for converted files",
                        default=default_output)
    parser.add_argument("--thesaurus", help="path to thesaurus")
    data = parser.parse_args(args[1:])
    thesaurus = data.thesaurus
    if thesaurus is not None:
        thesaurus = os.path.abspath(thesaurus)
    return InputData(
        [os.path.abspath(x) for x in data.input_paths],
        os.path.abspath(data.settings),
        os.path.abspath(data.output_dir),
        thesaurus
    )


def _process_input(input_data):
    records_filter = RecordFilter.read(
        input_data.settings_path, input_data.thesaurus_path)
    dataset = _filter_dataset(_read_data(input_data.paths), records_filter)
    if not os.path.exists(input_data.output_dir):
        os.makedirs(input_data.output_dir)
    for name in dataset:
        file_util.copy_file(name, input_data.output_dir)


def _read_json_folder(dirname):
    all_paths = (os.path.join(dirname, x) for x in os.listdir(dirname))
    all_files = [os.path.abspath(p) for p in all_paths
                 if os.path.isfile(p) and p.lower().endswith(".json")]
    results = {}
    for fname in all_files:
        try:
            results[fname] = _read_json(fname)
        except ValueError:
            continue
    return results


def _read_json(filename):
    with codecs.open(filename, "r", encoding="utf-8") as fin:
        return json.load(fin, object_pairs_hook=OrderedDict)


def _read_data(input_paths):
    all_jsons = {}
    path_not_found_fmt = "Warning! Path {0} not found."
    for path in input_paths:
        if not os.path.exists(path):
            print(path_not_found_fmt.format(path))
        elif os.path.isfile(path):
            all_jsons[path] = _read_json(path)
        else:
            all_jsons.update(_read_json_folder(path))
    return all_jsons


def _filter_dataset(dataset, record_filter):
    dataset = _remove_results(dataset)
    if not dataset:
        raise Error("Input files not found")
    return dict((k, dataset[k]) for k in dataset
                if record_filter.pass_record(dataset[k]))


def _remove_results(dataset):
    return dict([
        (x, dataset[x]) for x in dataset
        if Text.TYPE not in dataset[x] or
        dataset[x][Text.TYPE] != Text.CMPRESULT
    ])


def _parse_thesaurus(filename):
    data = _read_json(filename)
    groups = {}
    for group in data[Text.GROUPS]:
        group_items = []
        for ann in group[Text.REPORTS]:
            group_items.append(ann[Text.ID])
        group_id = group[Text.ID]
        groups[group_id] = set(group_items)
    return groups


if __name__ == "__main__":
    main()
