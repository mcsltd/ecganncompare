# Comparing result usage example

To demonstrate the use of comparison results, the programs `anndistribution` and `cmphistogram` was developed.
These programs uses `ecganncmp` module and packages [`matplotlib`](https://matplotlib.org/) and [`pandas`](https://pandas.pydata.org/).
The last two are not included in the standard Python library. 
To install them, you need to run the following command

    pip install matplotlib pandas

## AnnDistribution

The program [`anndistribution`](../utils/anndistribution.py) reads folders with annotation files. 
Data is grouped by thesaurus. The largest group is selected for display, the rest are ignored.
The program makes a histogram containing the distribution of conclusions for each annotator, and also makes a common histogram, without dividing by annotators.

To run the program, run the following command

    python anndistribution.py folder_path1 folder_path2

- `folder_path1` and `folder_path2` is a paths to folders with annotation files;
- one or more folder paths can be passed;
- paths of input folders may not be specified, then the program will try to find input files in the `data` folder, if it is in the same folder with the program file.

Results of `anndistribution` shown on the following images.  

![Common histogram](./images/common_histogram.png)

![Conclusions distribution](./images/conclusions_distribution.png)

- The graph legend contains the name of the annotator and the corresponding color of the bars.

Program `anndistribution` has an optional command line argument `thesaurus` that allows you to specify the path to the thesaurus file. 
If you specified a thesaurus file, the text values of conclusion codes will be displayed on the histogram, the bars will be grouped and ordered.

To use it, run the program as follows

    python anndistribution.py --thesaurus=path_to_thesaurus input_folder_path

- `path_to_thesaurus` is a path to thesaurus file. Thesaurus format is described in [`formats.md`](./formats.md);
- `input_folder_path` using has been described above.

Results of using `anndistribution` with `thesaurus` argument shown on the following images.

![Common histogram with thesaurus](./images/common_histogram_thesaurus.png)

![Grouped histogram bars](./images/grouped_distribution.png)
    

## CmpHistogram

The program [`cmphistogram`](../utils/cmphistogram.py) reads the `ecganncmp` results or folders with annotation files. For each annotator in the dataset, the program makes a histogram that contains the distributions of the conclusions matches of the other annotators with the selected annotator.  
_For better view, the program compares **no more than five** annotators._

To run the program, run the following command

    python cmphistogram.py input_path1 input_path2

- `input_path1` and `input_path1` are paths to file with `ecganncmp` result or to folder annotation files;
- one or more paths can be passed;
- if input paths not passed, `cmphistogram` try to find input data jast like a `anndistribution`.

Results of `cmphistogram` shown on the following image.

![Matches distribution](./images/cmphistogram.png)

- The graph legend describe colors of the bars: annotator name and conclusion numbers.

Program `cmphistogram` has an optional command line argument `thesaurus` that allows you to specify the path to the thesaurus file.

Both programs can be run without parameters, then the input data search will be performed in the folder `data` in the current folder. 
If you specified a thesaurus file, the text values of conclusion codes will be displayed on the histogram and the bars will be ordered.

To use it, run the program as follows

    python cmphistogram.py --thesaurus=path_to_thesaurus input_folder_path

- `path_to_thesaurus` is a path to thesaurus file. Thesaurus format is described in [`formats.md`](./formats.md);
- `input_folder_path` using has been described above.

Results of using `cmphistogram` with `thesaurus` argument shown on the following images.

![Matches distribution with thesaurus](./images/cmphistogram_thesaurus.png)
