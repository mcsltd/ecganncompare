# coding=utf-8
import os
import codecs
from collections import namedtuple, OrderedDict, Counter
import json
import argparse
from distutils import file_util


class Text(object):
    CONCLUSIONS = "conclusions"
    DATABASE = "database"
    RECORD_ID = "record"
    TYPE = "type"
    CMPRESULT = "cmpresult"
    CONCLUSION_THESAURUS = "conclusionThesaurus"
    ANNOTATOR = "annotator"
    GROUPS = "groups"
    REPORTS = "reports"
    ID = "id"
    NAME = "name"


_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


InputData = namedtuple("InputData", ["paths", "output_dir"])


def main():
    input_data = _parse_args(os.sys.argv)
    try:
        _process_input(input_data)
    except Error as err:
        print("Error: {0}".format(err))


def _parse_args(args):
    default_input = os.path.join(_CURRENT_DIR, "data")
    default_output = os.path.join(_CURRENT_DIR, "result")
    parser = argparse.ArgumentParser(
        description="Plot histograms for annotations comparing"
    )
    parser.add_argument("input_paths", nargs="*", default=[default_input],
                        help="paths to input folders/files")
    parser.add_argument("--output_dir", help="path to dir for converted files",
                        default=default_output)
    data = parser.parse_args(args[1:])
    return InputData(
        data.input_paths,
        data.output_dir
    )


def _process_input(input_data):
    dataset = _read_data(input_data.paths)
    dataset = _filter_dataset(dataset)
    if not os.path.exists(input_data.output_dir):
        os.makedirs(input_data.output_dir)
    for name in dataset:
        file_util.copy_file(name, input_data.output_dir)


def _read_json_folder(dirname):
    all_paths = (os.path.join(dirname, x) for x in os.listdir(dirname))
    all_files = [p for p in all_paths
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


def _remove_deviations(dataset, fieldname):
    counts = Counter(data[fieldname] for data in dataset if fieldname in data)
    common_value = counts.most_common()
    if common_value:
        common_value = common_value[0][0]
    else:
        return dataset, []
    good_items, others = [], []
    for data in dataset:
        value = data.get(fieldname)
        if value == common_value:
            good_items.append(data)
        else:
            others.append(data)
    return good_items, others


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


def _filter_dataset(dataset):
    annotators = set(["d.shutov@npcmr.ru", "dmitry.shutov@bk.ru"])
    exclude_conclusions = set(range(2701, 2708))

    dataset = _remove_results(dataset)
    dataset, bad_json = _remove_deviations(dataset, Text.CONCLUSION_THESAURUS)
    _print_removed_items(bad_json, Text.CONCLUSION_THESAURUS)
    if not dataset:
        raise Error("Input files not found")
    new_dataset = {}
    for key in dataset:
        item = dataset[key]
        if item[Text.ANNOTATOR] not in annotators:
            continue
        if any((x in exclude_conclusions) for x in item[Text.CONCLUSIONS]):
            continue
        new_dataset[key] = item
    return new_dataset


def _remove_deviations(dataset, fieldname):
    counts = Counter(data[fieldname] for data in dataset if fieldname in data)
    common_value = counts.most_common()
    if common_value:
        common_value = common_value[0][0]
    else:
        return dataset, []
    good_items, others = [], []
    for data in dataset:
        value = data.get(fieldname)
        if value == common_value:
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


def _remove_results(dataset):
    return [d for d in dataset
            if Text.TYPE not in d or d[Text.TYPE] != Text.CMPRESULT]


if __name__ == "__main__":
    main()
