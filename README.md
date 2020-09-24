# Ecganncompare

The program is used to compare annotation files obtained as a result of processing a set of ECG records.

## Usage

Python (2.6 or later) must be installed on the user's computer to run the program.
The program accepts two JSON annotation files. The format of the input files will be described below.
The launch is carried out through the command line.
Two arguments must be passed to the file ecganncmp.py as follows

    python ecganncmp.py ref_filename test_filename

- `ref_filename` is a path to file wiht reference annotations,
- `test_filename` is a path to file with annotations, that need to be compare with reference.

As a result of the program's work, a report is generated in JSON format.
The report format will be described below.
By default, the report is output to the console window.
To output the report to a file, the `ecganncmp` program must be run as follows (in Windows OS)

    python ecganncmp.py ref_filename test_filename > output_filename

- `output_filename` is a path to file that will be contain report of annotation comparing.

## Input files format

Input files must be in JSON format. The files contain the following data

| Name                | Type   | Description                                                    |
| ------------------- | ------ | -------------------------------------------------------------- |
| Version             | int    | Version of format                                              |
| Label               | string | Database label                                                 |
| Date                | string | Date and time of file creation in format dd/mm/yyyy HH:MM:SS   |
| Sowftware           | string | Name and version of annotation program                         |
| ConclusionThesaurus | string | Label of conclusions thesaurus                                 |
| AnnotationThesaurus | string | Label of annotations thesaurus                                 |
| Records             | array  | Array of objects that contains analysis result for each record |

Each object in array `Records` contains the following fields

| Name        | Type   | Description                                                                   |
| ----------- | ------ | ----------------------------------------------------------------------------- |
| Label       | string | Record label                                                                  |
| Conclusions | array  | Array of strings with text codes of conclusions that generated for the record |
| Annotations | array  | Array of objects that contains annotations for the record                     |

Each objectin array `Annotations` contains the following fields

| Name  | Type   | Description                                           |
| ----- | ------ | ----------------------------------------------------- |
| Label | string | Annotation label                                      |
| Time  | string | Offset from begin of record in format HH:MM:SS.ffffff |
