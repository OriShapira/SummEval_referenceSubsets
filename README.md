# SummEval_referenceSubsets
Code for the analysis of using different subsets of reference summaries for the evaluation of summaries, based on DUC 2001/2002 data, using ROUGE as the automatic evaluation package.
The code and results here are supplementary to the paper: *TODO: To be updated after acceptance*.

## Data
The data used for the analyses are the DUC 2001 and DUC 2002 multi-document summarization data since these datasets are the only ones containing different length reference (model) summaries of each document cluster, along with human assessment of the system summaries submitted for the shared tasks.
This data can be retrieved (free of charge) by contacting [NIST](http://www-nlpir.nist.gov/projects/duc/data.html) and recieving access.

## Installation and Setup
These scripts are based on the original [ROUGE](http://www.aclweb.org/anthology/W04-1013) Perl script by Chin-Yew Lin, and uses the pyrouge Python package as a wrapper.
1.  `pip install pyrouge`
2.  Install Perl onto your system, e.g. from [StrawberryPerl](http://strawberryperl.com/), and make sure Perl is in your system's Path variable.
3.  Download [ROUGE 1.5.5](https://github.com/andersjo/pyrouge/tree/master/tools/ROUGE-1.5.5)
4.  Point pyrouge to the directory where ROUGE 1.5.5 is located by running `python <pathToScript-pyrouge_set_rouge_path> <pathToFolderOf_ROUGE-1.5.5`. The `pyrouge_set_rouge_path` script should be in the Python scripts directory of pyrouge.
5.  For further fixes and alterations that you may need if any problems come up, see [this](https://stackoverflow.com/questions/47045436/how-to-install-the-python-package-pyrouge-on-microsoft-windows) great explanation. Although this answer is supposedly for Windows, some of the important stuff is relevant also for Mac and Linux.
6.  Download the code from this repository anywhere on your system.
7.  Prepare the data directories (reference and system summaries in separate folders). Convert them to SEE format (see script below) to accelerate the ROUGE calculations, or signal the INPUT_FORMAT variable in calculateRouge.py (see below). You may also use the DUC data already in SEE format.
8.  There are some small changes we made to the Rouge155.py script. Copy and replace it in the pyrouge Python directory.
9.  Run the code as described below.

## Code
The code here is divided to three parts.
### Scores Extraction
The code in folder *code_score_extraction* extracts the human assessed and ROUGE scores of system summaries.

*  To get **ROUGE scores** for system summaries against reference summaries, edit the INPUTS list and INPUT_FORMAT variable in calculateRouge.py according to your requirments, and run:
`python calculateRouge.py`.
An input is in the form of: (comparisonType, modelSummariesFolderPath, systemSummariesFolderPath, outputCSVfilepath, ducVersion <2001|2002>, stopWordsMode).

*  To get the **human assessed scores** for system summaries (for DUC 2001 and 2002), edit the INPUTS list in calculateHumanAssessment.py according to your requirments, and run:
`python calculateHumanAssessment.py`.
An input is in the form of: (ducVersion <2001|2002>, HumanAssessmentTableFilepath, outputCSVpath).

*  To get **ROUGE scores between reference summaries**, edit the INPUTS list in calculateRouge_modelComparisons.py according to your requirments, and run:
`python calculateRouge_modelComparisons.py`.
An input is in the form of: (modelSummariesFolderPath, outputCSVFolder, comparisonType, stopWordsMode).

### Correlation Calculation
The code in folder *code_correlation_calculation* calculates correlations between ROUGE scores and human assessed scores of systems.
The input data here should be in the format output from the first two scripts in the previous section.

*  To get **correlations between ROUGE and human assessed** system scores, edit the INPUTS list in calculateCorrelations.py according to your requirments, and run:
`python calculateCorrelations.py`.
An input is in the form of: (humanAssessmentScoresTableFilepath, RougeScoresTableFilepath, outputCSVFolder).

*  To get the **correlation differences** between the standard method of evaluation and the different methods experimented on, edit the FROM_DATA_FOLDER, TO_DATA_INFO and OUTPUT_FOLDER variables in calculateCorrelationDifferences.py according to your requirments, and run:
`python calculateCorrelationDifferences.py`.

*  To get **pairwise correlations** between ROUGE and human assesses system scores, edit the INPUTS list in calculateCorrelationsPairwise.py according to your requirments, and run:
`python calculateCorrelationsPairwise.py`.
An input is in the form of: (humanAssessmentScoresTableFilepath, RougeScoresTableFilepath, outputCSVFolder).
Here scores are correlated pairwise, and not as a single list of scores. For example, for systems A, B and C, with ROUGE and human scores r_A, h_A, r_B, h_B, r_C, h_C, the lists compared are <r_A-r_B, r_A-r_C, r_B-r_C | h_A-h_B, h_A-h_C, h_B-h_C> instead of <r_A, r_B, r_C | h_A, h_B, h_C> as in the first script in this section.


### Data Manipulation
The code in folder *code_data_manipulation* is for rearranging the data for different needs that may come up when calculating ROUGE scores.

*  The summaries to input to the ROUGE script should be in [SEE format](http://www1.cs.columbia.edu/nlp/tides/SEEManual.pdf), which is provided in the DUC data. To **convert the SEE files** to text file with one sentence per line, edit the workFolders list in ConvertSEE2txt.py, and run:
`python ConvertSEE2txt.py`
An input is in the form of: (input_folder, output_folder).

*  To **convert text files** with one sentence per line, to SEE format files, edit the INPUT_FOLDER and OUTPUT_FOLDER variables in ConvertTxt2SEE.py, and run:
`python ConvertTxt2SEE.py`

*  Sometimes you may want to use only specific reference summaries when calculating ROUGE in a way that the calculateRouge.py script cannot do straightforwardly. For example, if you'd like to use a certain number of random reference summaries of different lengths, you need to prepare a separate folder from which calculateRouge.py will read them. To **prepare subsets of reference summaries beforehand**, edit the MODELS_FOLDER_PATH, MODELS_FOLDER_PATH_DEST and SUBSET_TYPE variables according to your requirements, and run:
`python copySubsetOfModels.python`
The subset types possible are ONE_PER_AUTHOR or ONE_PER_LENGTH.

## Results
The results are are the outputs of the scripts above when run on the DUC 2001 and 2002 data. A few tables are sampled in the paper.
The ROUGE scores and correlations are divided into *stop-words removed* and *stop-words remaining* folders.
For more information on how human assessed scores and correlations were calculated, see the supplementary material PDF.
*TODO: Include the supplementary material PDF for explanations after acceptance*

*  Human Scores
    *  As ouput by `calculateHumanAssessment.py`
    *  Each system's overall (over all input text clusters) human assessed score for each summary length.

*  ROUGE Scores
    *  As output by `calculateRouge.py`
    *  Each system's overall ROUGE scores for different ROUGE variants for each summary length.
    *  Calculated for different configurations of reference summary sets.
    
*  Correlations
    *  As output by `calculateCorrelations.py`
    *  The ROUGE to human assessed system scores correlations for each reference summary configuration.
    
*  Correlation Differences
    *  As output by `calculateCorrelationDifferences.py`
    *  The differences in correlations from the standard approach.
