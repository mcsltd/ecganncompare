# Comparing result usage example

To demonstrate the use of comparison results, the program `histogram_demo` was developed.
This program uses the [`matplotlib`](https://matplotlib.org/) and [`pandas`](https://pandas.pydata.org/) packages, which are not included in the standard Python library. 
To install them, you need to run the following command

    pip install matplotlib pandas

The program reads the `ecganncmp` result and makes 4 histograms. The histograms show distributions of
- annotations in the reference file,
- annotations in the test file,
- matched annotations,
- missed and excess annotations.

To run the program, run the following command

    python histogram_demo.py cmp_result

- `cmp_result` is a path to the `ecganncmp` output file that contains a results of comparison.

Results of `histogram_demo` shown on the following images.  

![All annotations](./images/all_annotations.png)

- The top histogram shows the distribution of reference annotations.
- The bottom histogram shows the distribution of test annotations.

![Annotations comparing](./images/annotations_comparing.png)

- The top histogram shows the distribution of matched annotations.
- The bottom histogram shows the distribution of missed and excess annotations.
