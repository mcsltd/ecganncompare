import os
import codecs
from collections import OrderedDict, defaultdict, Counter, namedtuple
import json
import pandas


class Text(object):
    CONCLUSIONS = "conclusions"
    DATABASE = "database"
    RECORD_ID = "record"
    TYPE = "type"
    CMPRESULT = "cmpresult"
    CONCLUSION_THESAURUS = "conclusionThesaurus"
    ANNOTATOR = "annotator"


InputData = namedtuple("InputData", ["paths", "thesaurus"])


MatchStats = namedtuple("MatchStats", ["se", "sp", "ppv", "pnv", "acc"])


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


def _print_removed_items(items, fieldname):
    for item in items:
        message = "Removed {0}-{1} with {2} = {3}".format(
            item[Text.DATABASE], item[Text.RECORD_ID], fieldname,
            item[fieldname]
        )
        print(message)
    print("")


def _get_default_input_dir():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data")


def _remove_results(dataset):
    return [d for d in dataset
            if Text.TYPE not in d or d[Text.TYPE] != Text.CMPRESULT]


def _create_datatables(datagroups):
    return dict((annr, _dataset_to_table(datagroups[annr]))
                for annr in datagroups)


def _group_by(iterable_data, fieldname):
    groups = defaultdict(list)
    for data in iterable_data:
        groups[data[fieldname]].append(data)
    return groups


def _calculate_match_stats(dtable, other_table, total_ann_count):
    tp, fp, fn = 0, 0, 0
    for db in dtable:
        if db not in other_table:
            continue
        for rec in dtable[db]:
            if rec not in other_table[db]:
                continue
            anns = set(dtable[db][rec])
            other_anns = set(other_table[db][rec])

            matches = anns.intersection(other_anns)
            tp += len(matches)
            fn += len(anns.difference(matches))
            fp += len(other_anns.difference(matches))
    tn = total_ann_count - (tp + fp + fn)
    return MatchStats(
        se=(tp / float(tp + fn)),
        sp=(tn / float(fp + tn)),
        ppv=(tp / float(tp + fp)),
        pnv=(tn / float(tn + fn)),
        acc=(float(tp + tn) / total_ann_count)
    )


def _match_stats_to_str(match_stats):
    template = "Se={0:.2%}, Sp={1:.2%}, PPV={2:.2%},\nPNV={3:.2%}, Acc={4:.2%}"
    return template.format(*match_stats)


def _count_unique_anns(datatables):
    annotations = set()
    for annr in datatables:
        for db in datatables[annr]:
            for rec in datatables[annr][db]:
                data = datatables[annr][db][rec]
                annotations.update(data)
    return len(annotations)


def _create_stats_dataframe(datatables, total_ann_count):
    annotators = list(datatables.keys())
    cells = []
    for i, annr in enumerate(annotators):
        cells.append([])
        dtable = datatables[annr]
        for j, other_annr in enumerate(annotators):
            if i == j:
                cells[i].append("-")
                continue
            stats = _calculate_match_stats(
                dtable, datatables[other_annr], total_ann_count)
            cells[i].append(_match_stats_to_str(stats))
    dframe = pandas.DataFrame(cells)
    dframe.index = annotators
    dframe.columns = annotators
    return dframe


def _read_data(input_paths):
    all_jsons = []
    # TODO: check input_path is filename or dirs list
    warning_fmt = (
        "Warning! This program works only with data folders. File {0} will "
        "be ignored."
    )
    for path in input_paths:
        if os.path.isfile(path):
            print(warning_fmt.format(path))
        else:
            all_jsons += _read_json_folder(path)
    return all_jsons


def _group_data(all_jsons):
    all_jsons = _remove_results(all_jsons)
    all_jsons, bad_json = _remove_deviations(
        all_jsons, Text.CONCLUSION_THESAURUS)
    _print_removed_items(bad_json, Text.CONCLUSION_THESAURUS)
    return _group_by(all_jsons, Text.ANNOTATOR)
