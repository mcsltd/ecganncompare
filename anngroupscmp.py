import os
import codecs
from collections import OrderedDict, defaultdict, Counter
import json


class Text(object):
    CONCLUSIONS = "conclusions"
    DATABASE = "database"
    RECORD_ID = "record"


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


def _dataset_to_table(dataset):
    table = defaultdict(dict)
    for item in dataset:
        database = item[Text.DATABASE]
        record = item[Text.RECORD_ID]
        table[database][record] = item[Text.CONCLUSIONS]
    return dict(table)


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
