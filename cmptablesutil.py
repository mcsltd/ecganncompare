import os
import codecs
from collections import OrderedDict, defaultdict, Counter, namedtuple
import json
import argparse
from operator import itemgetter
import pandas


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
    THESAURUS_LABEL = "thesaurus"
    LANGUAGE = "language"
    ANNOTATORS = "annotators"
    CONCLUSIONS_ANNOTATORS = "conclusionsAnnotators"
    RECORDS = "records"


InputData = namedtuple("InputData", ["paths", "thesaurus"])


MatchStats = namedtuple("MatchStats", ["Se", "Sp", "PPV", "PNV", "Acc"])


Thesaurus = namedtuple("Thesaurus", ["label", "lang", "items"])


_MIN_ANNOTATORS_COUNT = 2
_TABLE_OUT_FILENAME = "stats.xlsx"
_CMP_SJON_FILENAME = "conclusions-annotators.json"


def main():
    input_data = _parse_args(os.sys.argv)
    dataset = _read_data(input_data.paths)
    groups, thesaurus_label = _group_data(dataset)
    if input_data.thesaurus is None:
        thesaurus = _create_thesaurus(thesaurus_label)
    else:
        thesaurus = _parse_thesaurus(input_data.thesaurus)
    _check_groups(groups)
    tables = _create_datatables(groups)
    _write_stats_table(tables, _TABLE_OUT_FILENAME, thesaurus.items)
    _write_cmp_json(tables, _CMP_SJON_FILENAME, thesaurus)


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


def _group_by_field(iterable_data, fieldname):
    return _group_by(iterable_data, itemgetter(fieldname))


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
    counts_sum = sum([tp, fp, fn])
    if counts_sum == 0:
        return None
    tn = total_ann_count - counts_sum
    return MatchStats(
        Se=(tp / float(tp + fn)),
        Sp=(tn / float(fp + tn)),
        PPV=(tp / float(tp + fp)),
        PNV=(tn / float(tn + fn)),
        Acc=(float(tp + tn) / total_ann_count)
    )


def _count_unique_anns(datatables):
    annotations = set()
    for annr in datatables:
        for db in datatables[annr]:
            for rec in datatables[annr][db]:
                data = datatables[annr][db][rec]
                annotations.update(data)
    return len(annotations)


def _create_stats_dataframe(datatables, total_ann_count):
    fields_names = MatchStats._fields
    bad_values_row = ["x"] * len(fields_names)
    annotators = list(datatables.keys())
    frames = []
    for i, annr in enumerate(annotators):
        dtable = datatables[annr]
        subtable = []
        for j, other_annr in enumerate(annotators):
            if i == j:
                subtable.append(bad_values_row)
                continue
            stats = _calculate_match_stats(
                dtable, datatables[other_annr], total_ann_count)
            if stats is None:
                subtable.append(bad_values_row)
            else:
                stats = ("{0:.2%}".format(x) for x in stats)
                subtable.append(list(stats))
        subframe = pandas.DataFrame(subtable).transpose()
        subframe.index = fields_names
        frames.append(subframe)
    dframe = pandas.concat(frames, keys=annotators)
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
    thesaurus = all_jsons[0][Text.CONCLUSION_THESAURUS]
    return _group_by_field(all_jsons, Text.ANNOTATOR), thesaurus


def _check_groups(groups):
    if len(groups) >= _MIN_ANNOTATORS_COUNT:
        return True
    message_format = (
        "Cannot less than %d annotators. Prepare a folders or "
        "explicitly specify result files."
    )
    raise RuntimeError(message_format % _MIN_ANNOTATORS_COUNT)


def _parse_thesaurus(filename):
    data = _read_json(filename)
    items = OrderedDict()
    for group in data[Text.GROUPS]:
        for ann in group[Text.REPORTS]:
            items[ann[Text.ID]] = ann[Text.NAME]
    return _create_thesaurus(
        data[Text.THESAURUS_LABEL],
        data[Text.LANGUAGE],
        items
    )


def _write_stats_table(tables, filename, thesaurus_items):
    if thesaurus_items:
        total_ann_count = len(thesaurus_items)
    else:
        total_ann_count = _count_unique_anns(tables)
    writer = pandas.ExcelWriter(filename)
    _create_stats_dataframe(tables, total_ann_count).to_excel(writer)
    _format_writer(writer)
    writer.save()


def _reshape_tables(tables):
    new_tables = defaultdict(lambda: defaultdict(dict))
    for annr in tables:
        for db in tables[annr]:
            for rec in tables[annr][db]:
                ann_list = tables[annr][db][rec]
                new_tables[db][rec][annr] = set(ann_list)
    for db in new_tables:
        for rec in new_tables[db]:
            new_tables[db][rec] = dict(new_tables[db][rec])
        new_tables[db] = dict(new_tables[db])
    return new_tables


def _write_cmp_json(tables, filename, thesaurus):
    thesaurus_keys = list(thesaurus.items.keys())
    report = OrderedDict()
    report[Text.ANNOTATORS] = sorted(tables.keys())
    tables = _reshape_tables(tables)
    records_data = []
    for db_name in tables:
        for rec in tables[db_name]:
            rec_data = OrderedDict()
            rec_data[Text.DATABASE] = db_name
            rec_data[Text.RECORD_ID] = rec
            groups = _group_annotators_by_items(tables[db_name][rec])
            rec_data[Text.CONCLUSIONS_ANNOTATORS] = OrderedDict(sorted(
                groups.items(),
                key=lambda p: thesaurus_keys.index(p[0]))
            )
            records_data.append(rec_data)
    report[Text.THESAURUS_LABEL] = thesaurus.label
    report[Text.RECORDS] = records_data
    with open(filename, "w") as fout:
        json.dump(report, fout, indent=4)


def _create_thesaurus(label, lang=None, items=None):
    if items is None:
        items = {}
    return Thesaurus(label, lang, items)


def _group_by(items, key):
    groups = defaultdict(list)
    for item in items:
        groups[key(item)].append(item)
    return dict(groups)


def _group_annotators_by_items(ann_groups):
    groups = defaultdict(list)
    for annr in ann_groups:
        for ann_id in ann_groups[annr]:
            groups[ann_id].append(annr)
    for ann_id in groups:
        groups[ann_id].sort()
    return dict(groups)


def _format_writer(writer):
    book = writer.book
    sheet = writer.sheets.values()[0]

    rotated_header = book.add_format({"rotation": 90})
    sheet.set_row(0, None, rotated_header)  # TODO: fix
    
    return writer


if __name__ == "__main__":
    main()
