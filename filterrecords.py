# coding=utf-8
import os
import codecs
from collections import namedtuple, OrderedDict
import json
import argparse
from distutils import file_util


class Text(object):
    CONCLUSIONS = "conclusions"
    TYPE = "type"
    CMPRESULT = "cmpresult"
    ANNOTATOR = "annotator"


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
        [os.path.abspath(x) for x in data.input_paths],
        os.path.abspath(data.output_dir)
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


def _filter_dataset(dataset):
    annotators = [
        "d.shutov@npcmr.ru", "dmitry.shutov@bk.ru", "a.popov@npcmr.ru"
    ]
    exclude_conclusions = set(range(2701, 2708))

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


if __name__ == "__main__":
    main()
