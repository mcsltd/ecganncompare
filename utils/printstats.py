# coding=utf-8
import os
import codecs
from collections import OrderedDict, Counter, namedtuple, defaultdict
import json
import argparse
from operator import itemgetter
import sys
import locale
import traceback


class Text(object):
    CONCLUSIONS = "conclusions"
    DATABASE = "database"
    RECORD_ID = "record"
    TYPE = "type"
    CMPRESULT = "cmpresult"
    ANNOTATOR = "annotator"
    GROUPS = "groups"
    REPORTS = "reports"
    ID = "id"
    NAME = "name"


class Error(Exception):
    def __init__(self, message):
        super(Error, self).__init__(message)


InputData = namedtuple("InputData", ["paths", "thesaurus"])


def main():
    input_data = _parse_args(os.sys.argv)
    try:
        _process_input(input_data)
    except Error as err:
        print("Error: {0}".format(err))
    except Exception as exc:
        gettrace = getattr(os.sys, 'gettrace', None)
        if gettrace():
            raise
        log_filename = "errors-log.txt"
        message = "Fatal error! {0}: {1}. See details in file '{2}'."
        print(message.format(type(exc).__name__, exc, log_filename))
        with open(log_filename, "wt") as log:
            log.write(traceback.format_exc())


def _parse_args(args):
    parser = argparse.ArgumentParser(
        description="Plot histograms for annotations comparing"
    )
    parser.add_argument("input_paths", nargs="*",
                        default=[_get_default_input_dir()],
                        help="paths to input folders")
    parser.add_argument("--thesaurus", help="path to thesaurus")
    data = parser.parse_args(args[1:])
    return InputData(
        data.input_paths,
        data.thesaurus
    )


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
        return json.load(fin, object_pairs_hook=OrderedDict)


def _get_default_input_dir():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data")


def _remove_results(dataset):
    return [d for d in dataset
            if Text.TYPE not in d or d[Text.TYPE] != Text.CMPRESULT]


def _read_data(input_paths):
    all_jsons = []
    path_not_found_fmt = "Warning! Path {0} not found."
    ignored_file_fmt = (
        "Warning! This program works only with data folders. File {0} will "
        "be ignored."
    )
    for path in input_paths:
        if not os.path.exists(path):
            print(path_not_found_fmt.format(path))
        elif os.path.isfile(path):
            print(ignored_file_fmt.format(path))
        else:
            all_jsons += _read_json_folder(path)
    return all_jsons


def _process_input(input_data):
    dataset = _read_data(input_data.paths)
    dataset = _remove_results(dataset)
    thesaurus = None
    if input_data.thesaurus is not None:
        thesaurus = _parse_thesaurus(input_data.thesaurus)
    _print_dataset(dataset, thesaurus)


def _to_flat(iterable_matrix):
    return (item for row in iterable_matrix for item in row)


def _dataset_to_table(dataset):
    table = defaultdict(dict)
    for item in dataset:
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[database][record] = item[Text.CONCLUSIONS]
    return dict(table)


def _create_datatables(datagroups):
    return dict((annr, _dataset_to_table(datagroups[annr]))
                for annr in datagroups)


def _group_by_field(iterable_data, fieldname):
    return _group_by(iterable_data, itemgetter(fieldname))


def _group_by(items, key):
    groups = defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    return dict(groups)


def _print_dataset(dataset, thesaurus=None):
    old_stdout = sys.stdout
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
    print(u"Число записей: {0}".format(_count_records(dataset)))
    conclusions = list(_to_flat(x[Text.CONCLUSIONS] for x in dataset))
    print(u"Число поставленных заключений: {0}".format(len(conclusions)))
    indent = u"  "

    if thesaurus is not None:
        thesaurus_keys = list(thesaurus.keys())

    print("")
    conc_counts = Counter(conclusions)
    if thesaurus is not None:
        conc_counts = OrderedDict((k, conc_counts[k]) for k in thesaurus_keys
                                  if k in conc_counts)
    print(u"Счетчики использования заключений (всего использовано {0}): ".format(len(conc_counts)))
    for key in conc_counts:
        print("{0}{1}: {2}".format(indent, key, conc_counts[key]))
    print("")

    print(u"Поставленные заключения:")
    groups = _group_by_field(dataset, Text.ANNOTATOR)
    tables = _create_datatables(groups)
    for annr in tables:
        print(annr)
        for db in tables[annr]:
            for rec in tables[annr][db]:
                codes = tables[annr][db][rec]
                if thesaurus is None:
                    conclusions_text = u", ".join(codes)
                else:
                    new_indent = 2 * indent
                    codes.sort(key=thesaurus_keys.index)
                    conclusions_text = (u",\n" + new_indent).join(
                        thesaurus[c] for c in codes
                    )
                    conclusions_text = u"\n" + new_indent + conclusions_text
                print(u"{0}{1}, {2}: {3}.".format(
                    indent, db, rec, conclusions_text
                ))
    sys.stdout = old_stdout


def _parse_thesaurus(filename):
    data = _read_json(filename)
    result = OrderedDict()
    for group in data[Text.GROUPS]:
        for ann in group[Text.REPORTS]:
            result[ann[Text.ID]] = ann[Text.NAME]
    return result


def _count_records(dataset):
    records = defaultdict(set)
    for data_item in dataset:
        records[data_item[Text.DATABASE]].add(data_item[Text.RECORD_ID])
    return sum(len(records[db]) for db in records)


if __name__ == "__main__":
    main()
