# Input files format

Input files must be in JSON format. The files contain the following data

| Name                | Type    | Description                                                    |
| ------------------- | ------- | -------------------------------------------------------------- |
| Version             | integer | Version of format                                              |
| Label               | string  | Database label                                                 |
| Date                | string  | Date and time of file creation in format dd/mm/yyyy HH:MM:SS   |
| Annotator           | string  | Name and version of annotation program                         |
| ConclusionThesaurus | string  | Label and version of conclusions thesaurus                     |
| AnnotationThesaurus | string  | Label and version of annotations thesaurus                     |
| Records             | array   | Array of objects that contains analysis result for each record |

Each object in array `Records` contains the following fields

| Name        | Type   | Description                                                                   |
| ----------- | ------ | ----------------------------------------------------------------------------- |
| Label       | string | Record label                                                                  |
| Conclusions | array  | Array of strings with text codes of conclusions that generated for the record |
| Annotations | array  | Array of objects that contains annotations for the record                     |

Each object in array `Annotations` contains the following fields

| Name  | Type   | Description                                           |
| ----- | ------ | ----------------------------------------------------- |
| Label | string | Annotation label                                      |
| Time  | string | Offset from begin of record in format HH:MM:SS.ffffff |

## Input files examples

```json
{
  "Version": 1,
  "Label": "CTS",
  "Date": "09/23/2020 12:19:05",
  "Annotator": "EcgInterpreter1.3.17311.0",
  "ConclusionThesaurus": "MCS",
  "AnnotationThesaurus": null,
  "Records": [
    {
      "Label": "CAL05000",
      "Conclusions": ["3.1.1", "5.1.9", "7.1.5", "1.1.11"],
      "Annotations": null
    },
    {
      "Label": "CAL10000",
      "Conclusions": ["3.1.1", "5.1.9", "7.1.5", "1.1.11"],
      "Annotations": null
    }
  ]
}
```

```json
{
  "Version": 1,
  "Label": "AHADB",
  "Date": "09/23/2020 11:44:17",
  "Annotator": "WFDB_10.x",
  "ConclusionThesaurus": null,
  "AnnotationThesaurus": "WFDB",
  "Records": [
    {
      "Label": "1201",
      "Conclusions": null,
      "Annotations": [
        {
          "Label": "1",
          "Time": "00:05:00.040000"
        },
        {
          "Label": "1",
          "Time": "00:05:01.132000"
        }
      ]
    }
  ]
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
| Labels           | array   | Array of arrays with two items: reference annotation and test annotation or null if one of them is missed |

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
| Thesaurus | string | Label and version of conclusions thesaurus      |
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
