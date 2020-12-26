# Input files format

Input files must be in JSON format. The files contain the following data

| Name                | Type    | Description                                             |
| ------------------- | ------- | ------------------------------------------------------- |
| version             | integer | Version of format                                       |
| date                | string  | Date and time of file creation in UTC format            |
| annotator           | string  | Annotator's name                                        |
| database            | string  | Database name                                           |
| record              | string  | Record's name                                           |
| conclusionThesaurus | string  | Version of conclusions thesaurus                        |
| conclusions         | array   | Array of ids of conclusions that was set for the record |

## Input files examples

```json
{
  "version": 1,
  "date": "2020-10-22T10:18:35.091Z",
  "annotator": "annotator1@ecg.ru",
  "database": "Moscow Day #67",
  "record": "patient_00001",
  "conclusionThesaurus": "MCS",
  "conclusions": ["1.1.1", "3.1.5", "6.1.1"]
}
```

# Output format

Result of comparing files have a JSON format and contains the following data

| Name                | Type    | Description                                                       |
| ------------------- | ------- | ----------------------------------------------------------------- |
| type                | string  | Constant string must contains value `cmpresult`                   |
| program             | object  | Contains two string fields `name` and `version`                   |
| company             | string  | Contains company info                                             |
| date                | string  | Date and time of file creation in UTC format                      |
| refAnnotator        | string  | Annotator of reference file name                                  |
| testAnnotator       | string  | Annotator of test file name                                       |
| conclusionThesaurus | string  | Label of conclusion thesaurus in both files                       |
| reсordsCount        | integer | Count of processed records                                        |
| refAnnotations      | integer | Total count of annotations in reference file                      |
| testAnnotations     | integer | Total count of annotations in test file                           |
| sensitivity         | object  | Contains two numbers: `matchCount` and `value`                    |
| specificity         | object  | Contains two numbers: `missesCount` and `value`                   |
| records             | array   | Array of objects with info and comaprision result for each record |

Each object in array `records` contains the following fields

| Name            | Type    | Description                                                                               |
| --------------- | ------- | ----------------------------------------------------------------------------------------- |
| record          | string  | Record's name                                                                             |
| database        | string  | Database name                                                                             |
| refAnnotations  | integer | Count of annotations in reference file for this record                                    |
| testAnnotations | integer | Count of annotations in test file for this record                                         |
| matchCount      | integer | Number of matched annotations in this record                                              |
| conclusions     | array   | Array of pairs: reference annotation and test annotation or null if one of them is missed |

## Output example

```json
{
  "type": "cmpresult",
  "program": {
    "version": "1.0",
    "name": "ecganncmp"
  },
  "company": "Medical computer systems (c) 2020 - www.mks.ru",
  "date": "2020-11-10T11:46:11.121000Z",
  "refAnnotator": "test-annotator-1",
  "testAnnotator": "test-annotator-2",
  "conclusionThesaurus": "test-thesaurus",
  "recordsCount": 2,
  "refAnnotations": 4,
  "testAnnotations": 3,
  "sensitivity": {
    "matchCount": 3,
    "value": 75.0
  },
  "specificity": {
    "missesCount": 1,
    "value": 25.0
  },
  "records": [
    {
      "record": "MA1_001",
      "database": "CSE Common Standards for ECG",
      "refAnnotations": 2,
      "testAnnotations": 1,
      "matchCount": 1,
      "conclusions": [
        [302, null],
        [504, 504]
      ]
    },
    {
      "record": "MA1_002",
      "database": "CSE Common Standards for ECG",
      "refAnnotations": 2,
      "testAnnotations": 2,
      "matchCount": 2,
      "conclusions": [
        [302, 302],
        [401, 401]
      ]
    }
  ]
}
```

# Thesaurus files format

Thesaurus files are used to map annotations code or label to textual description.
These files are in JSON format and contain the following data

| Name      | Type   | Description                                             |
| --------- | ------ | ------------------------------------------------------- |
| thesaurus | string | Name and version of conclusions thesaurus               |
| language  | string | Language of textual descriptions                        |
| groups    | array  | Array of objects that contains grouped annotations data |

Each object in array `groups` contains the following fields

| Name     | Type    | Description                                                               |
| -------- | ------- | ------------------------------------------------------------------------- |
| id       | string  | Id of group                                                               |
| name     | string  | Group's name                                                              |
| multiple | boolean | Flag indicating the ability to select multiple conclusions from the group |
| reports  | array   | Array of objects with `id` and `name` of conclusion item                  |

## Files example

```json
{
  "thesaurus": "MCS",
  "language": "en",
  "groups": [
    {
      "id": "1.1",
      "name": "General Conditions",
      "multiple": true,
      "reports": [
        {
          "id": "1.1.1",
          "name": "Short record, partial analysis performed"
        },
        {
          "id": "1.1.2",
          "name": "Lead I or II absent"
        }
      ]
    },
    {
      "id": "3.1",
      "name": "Axis",
      "multiple": false,
      "reports": [
        {
          "id": "3.1.2",
          "name": "Left axis deviation"
        },
        {
          "id": "3.1.6",
          "name": "Normal axis"
        }
      ]
    }
  ]
}
```