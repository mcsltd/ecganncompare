# coding=utf-8
import os
import codecs
from collections import namedtuple, OrderedDict, defaultdict
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


_FILE_CONTAINING_DIR = os.path.dirname(os.path.abspath(__file__))
_CURRENT_WORKING_DIR = os.curdir


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


class FilterRules(object):
    def __init__(self, dbs, annotators, ids):
        self.__dbs = FilterRules.__to_lower_str_set(dbs)
        self.__annotators = FilterRules.__to_lower_str_set(annotators)
        self.__ids = FilterRules.__to_lower_str_set(ids)

    def match_all(self, annotation_data):
        return all(self.__check(annotation_data))

    def match_any(self, annotation_data):
        return any(self.__check(annotation_data))

    def __check(self, annotation_data):
        dbase = annotation_data[Text.DATABASE]
        annotator = annotation_data[Text.ANNOTATOR]
        conclusions = annotation_data[Text.CONCLUSIONS]
        return [
            FilterRules.__empty_or_contains(self.__dbs, dbase),
            FilterRules.__empty_or_contains(self.__annotators, annotator),
            FilterRules.__empty_or_contains_any(self.__ids, conclusions)
        ]

    @staticmethod
    def create(rule_settings, thesaurus_groups=None):
        return FilterRules(
            rule_settings.get(Text.DATABASE, []),
            rule_settings.get(Text.ANNOTATOR, []),
            FilterRules.__get_conclusions_id(rule_settings, thesaurus_groups)
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


class RecordsFilter(object):
    def __init__(self, include_rules, exclude_rules):
        self.__include = include_rules
        self.__exclude = exclude_rules

    def pass_record(self, annotation_data):
        return self.__include.match_all(annotation_data) and\
            (not self.__exclude.match_any(annotation_data))


InputData = namedtuple("InputData", ["paths", "output_dir", "thesaurus_path"])


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
    # TODO: remade with current working directory
    default_output = "filter_records_result"
    default_output = os.path.join(_CURRENT_WORKING_DIR, default_output)

    parser = argparse.ArgumentParser(
        description="Filter json-annotation files"
    )
    parser.add_argument("input_paths", nargs="*", default=[default_input],
                        help="paths to input folders/files")
    parser.add_argument("--output_dir", help="path to dir for converted files",
                        default=default_output)
    parser.add_argument("--thesaurus", help="path to thesaurus")
    data = parser.parse_args(args[1:])
    return InputData(
        [os.path.abspath(x) for x in data.input_paths],
        os.path.abspath(data.output_dir),
        data.thesaurus
    )


def _process_input(input_data):
    dataset = _read_data(input_data.paths)
    thesaurus = None
    if input_data.thesaurus_path is not None:
        thesaurus = _parse_thesaurus(input_data.thesaurus_path)
    dataset = _filter_dataset(dataset, thesaurus)
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


def _filter_dataset(dataset, thesaurus=None):
    annotators = [
        "d.shutov@npcmr.ru", "dmitry.shutov@bk.ru", "a.popov@npcmr.ru",
        "amebah@mail.ru"
    ]
    exclude_group_name = "02.07"
    exclude_conclusions = thesaurus[exclude_group_name]

    annotators = set(a.lower() for a in annotators)
    dataset = _remove_results(dataset)
    if not dataset:
        raise Error("Input files not found")
    new_dataset = {}
    for key in dataset:
        item = dataset[key]
        if item[Text.ANNOTATOR].lower() not in annotators:
            continue
        if any((x in exclude_conclusions) for x in item[Text.CONCLUSIONS]):
            continue
        new_dataset[key] = item
    return new_dataset


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
