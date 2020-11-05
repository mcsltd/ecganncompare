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

| Name                | Type    | Description                                                                                               |
| ------------------- | ------- | --------------------------------------------------------------------------------------------------------- |
| Program             | object  | Contains two string fields `Name` and `Version`                                                           |
| Company             | string  | Contains company info                                                                                     |
| Date                | string  | Date and time of file creation in format dd/mm/yyyy HH:MM:SS                                              |
| ConclusionThesaurus | string  | Label of conclusion thesaurus in both files                                                               |
| RecordsCount        | integer | Number of compared records                                                                                |
| RefAnnotations      | integer | Total count of annotations in reference file                                                              |
| TestAnnotations     | integer | Total count of annotations in test file                                                                   |
| Sensitivity         | object  | Contains data for sensitivity calculation                                                                 |
| Specificity         | object  | Contains data for specificity calculation                                                                 |
| Records             | object  | An object whose fields are the names of the records and values are the comparison results for each record |

Object `Sensitivity` contains the following fields

| Name       | Type    | Description                   |
| ---------- | ------- | ----------------------------- |
| MatchCount | integer | Number of matched annotations |
| Value      | number  | Real value of sensitivity     |

Object `Specificity` contains the following fields

| Name              | Type    | Description                 |
| ----------------- | ------- | --------------------------- |
| ExcessAnnotations | integer | Number of excess annotaions |
| Value             | number  | Real value of specificity   |

Each value in object `Records` contains the following fields

| Name            | Type    | Description                                                                                               |
| --------------- | ------- | --------------------------------------------------------------------------------------------------------- |
| MatchCount      | integer | Number of matched annotations in this record                                                              |
| RefAnnotations  | integer | Number of annotations for this record in reference file                                                   |
| TestAnnotations | integer | Number of annotations for this record in test file                                                        |
| Labels          | array   | Array of arrays with two items: reference annotation and test annotation or null if one of them is missed |

## Output example

```json
{
  "Program": {
    "Name": "ecganncmp",
    "Version": "1.0"
  },
  "Company": "Medical computer systems (c) 2020 - www.mks.ru",
  "Date": "23/09/2020 14:38:52",
  "ConclusionThesaurus": "MCS",
  "RecordsCount": 340,
  "RefAnnotations": 1193,
  "TestAnnotations": 1416,
  "Sensitivity": {
    "MatchCount": 719,
    "Value": 60.26823134953898
  },
  "Specificity": {
    "ExcessAnnotations": 697,
    "Value": 49.22316384180791
  },
  "Records": {
    "40 Maksimova L A  79__Exam_1_0": {
      "MatchCount": 4,
      "RefAnnotations": 5,
      "TestAnnotations": 4,
      "Labels": [
        ["13.1.10", "13.1.10"],
        ["13.1.11", "13.1.11"],
        ["3.1.6", "3.1.6"],
        ["7.1.5", "7.1.5"],
        ["9.1.8", null]
      ]
    }
  }
}
```

# Thesaurus files format

Thesaurus files are used to map annotations code or label to textual description.
These files are in JSON format and contain the following data

| Name      | Type   | Description                                     |
| --------- | ------ | ----------------------------------------------- |
| Thesaurus | string | Version of conclusions thesaurus                |
| Language  | string | Language of textual descriptions                |
| Items     | array  | Array of objects that contains annotations data |

Each object in array `Items` contains the following fields

| Name        | Type   | Description                                                       |
| ----------- | ------ | ----------------------------------------------------------------- |
| Label       | string | Id of annotation                                                  |
| Description | string | A textual description of the annotation in the specified language |

## Files example

```json
{
  "Thesaurus": "WFDB",
  "Language": "en",
  "Items": [
    {
      "Label": "0",
      "Description": "not-QRS (not a getann/putann code)"
    },
    {
      "Label": "1",
      "Description": "normal beat"
    },
    {
      "Label": "2",
      "Description": "left bundle branch block beat"
    },
    {
      "Label": "3",
      "Description": "right bundle branch block beat"
    }
  ]
}
```
