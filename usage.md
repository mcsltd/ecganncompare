# Comparing result usage example

To demonstrate the use of comparison results, the programs `anndistribution` and `cmphistogram` was developed.
These programs uses `ecganncmp` module and packages [`matplotlib`](https://matplotlib.org/) and [`pandas`](https://pandas.pydata.org/).
The last two are not included in the standard Python library. 
To install them, you need to run the following command

    pip install matplotlib pandas

The program `anndistribution` reads folders with annotation files. 
All files in one folder should be made by the same annotator. 
All files should be made with the same thesaurus.
The program makes histogram that contains distributions annotations for each annotator.

To run the program, run the following command

    python anndistribution.py folder_path1 folder_path2

- `folder_path1` and `folder_path2` is a paths to folders with annotation files.
- more folder paths can be passed.

Results of `anndistribution` shown on the following image.  

![Annotations distribution](./images/annotations_distribution.png)

- The graph legend contains the name of the annotator and the corresponding color of the bars.

The program `cmphistogram` reads the `ecganncmp` result and makes histogram that contains distributions of annotations matches and misses.

To run the program, run the following command

    python cmphistogram.py cmp_result1 cmp_result2

- `cmp_result1` and `cmp_result2` are paths to files with `ecganncmp` result
- more filepaths can be passed.

Results of `cmphistogram` shown on the following image.

![Annotations comparing](./images/annotations_comparing.png)

- The graph legend describe colors of the bars (matches and misses).
