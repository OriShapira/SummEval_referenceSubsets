'''
This script is for calculating the correlations between the human and ROUGE scores of system summaries.
It does so by correlating the score differences between all pairs of systems.
For example: system A,B,C keep score differences (A-B),(A-C),(B-C), for human as well as ROUGE assessments.
The appropriate human csv and ROUGE csvs should be specified.
These were output by the scripts "calculateHumanAssessment.py" and "calculateRouge.py".
The script can run over several inputs as specified in the INPUTS list.

Change the INPUTS variable for your inputs.

To run: python calculateCorrelationsPairwise.py
Outputs: a folder with CSVs for correlations
'''
import scipy.stats
import os

# THE INPUTS TO RUN IN A LOOP - CHANGE YOUR INPUTS HERE:
# the inputs to run on in the format "(humanAssessmentScoresTableFilepath, RougeScoresTableFilepath, outputCSVFolder)":
INPUTS = [
    #('output2001_human.csv', 'output2001_allLens.csv', 'output2001_allLens_correlations'),
    #('output2002_human.csv', 'output2002_allLens.csv', 'output2002_allLens_correlations'),
    #('output2001_human.csv', 'output2001_sameLen_merged.csv', 'output2001_sameLen_correlations_merged'),
    #('output2002_human.csv', 'output2002_sameLen_merged.csv', 'output2002_sameLen_correlations_merged')
    #('output2001_human.csv', 'output2001_diffLens_3.csv', 'output2001_diffLens_3_correlations'),
    #('output2002_human.csv', 'output2002_diffLens_2.csv', 'output2002_diffLens_2_correlations'),
    #('output2001_human.csv', 'output2001_toLongest.csv', 'output2001_toLongest_correlations'),
    #('output2002_human.csv', 'output2002_toLongest.csv', 'output2002_toLongest_correlations'),
    #('output2001_human.csv', 'output2001_sameLen_trunc.csv', 'output2001_sameLen_trunc_correlations'),
    #('output2002_human.csv', 'output2002_sameLen_trunc.csv', 'output2002_sameLen_trunc_correlations'),
    
    #('output2001_human.csv', 'output2001_diffLensSingle_3.csv', 'output2001_pairwiseDiffLen3_correlations'),
    #('output2001_human.csv', 'output2001_sameLen.csv', 'output2001_pairwise_correlations'),
    #('output2001_human.csv', 'output2001_toShortest.csv', 'output2001_pairwiseToShortest_correlations'),
    #('output2001_human.csv', 'output2001_toLongest.csv', 'output2001_pairwiseToLongest_correlations'),
    #('output2001_human.csv', 'output2001_diffLensSingle.csv', 'output2001_pairwiseDiffLen_correlations'),
    ('output2002_human.csv', 'output2002_diffLensSingle_2.csv', 'output2002_pairwiseDiffLen2_correlations'),
    ('output2002_human.csv', 'output2002_sameLen.csv', 'output2002_pairwise_correlations'),
    ('output2002_human.csv', 'output2002_toShortest.csv', 'output2002_pairwiseToShortest_correlations'),
    ('output2002_human.csv', 'output2002_toLongest.csv', 'output2002_pairwiseToLongest_correlations'),
    ('output2002_human.csv', 'output2002_diffLensSingle.csv', 'output2002_pairwiseDiffLen_correlations'),
    
    ]
    

# The ROUGE types used within the scores data:
ROUGE_TYPES = ['R1', 'R2', 'R3', 'R4', 'RSU', 'RL', 'RW', 'RS']


def getPairwiseDifferences(dataDict, systemNamesSorted):
    '''
    Returns a dictionary of system pair tuples to their corresponding score differences.
    The difference is in the order of the pair (sys1-sys2 for pair (sys1,sys2)).
    '''
    scoreDiffs = {}
    
    for i in range(len(systemNamesSorted)):
        sysName1 = systemNamesSorted[i]
        if not sysName1 in dataDict:
            continue
        score1Str = dataDict[sysName1]
        for j in range(i+1, len(systemNamesSorted)):
            sysName2 = systemNamesSorted[j]
            if not sysName2 in dataDict:
                continue
            score2Str = dataDict[sysName2]
            if score1Str == '-' or score2Str == '-':
                continue
            else:
                scoreDiffs[(sysName1, sysName2)] = float(score1Str) - float(score2Str)
    return scoreDiffs


def loadAndScore_humanAssessment(humanAssessmentCSVpath):
    '''
    Load the human assessment data from the CSV specified, and calculate the pairwise system scores.
    Returns the pairwise score difference, the summary lengths and the system names (sorted)
    The pairwise score differences are in the format:
    |_ summary_length
        |_ (sysName1, sysName2) -> score1 - score2
    '''
    systemNames = {}
    # The file is in the format: system_name,<len1>,<len2>,<len3>,<len4>
    with open(humanAssessmentCSVpath, 'r') as fIn:
        lines = fIn.readlines()
        # get the summary length names, and prepare a dictionary for each:
        summaryLens = lines[0].strip().split(',')[1:]
        data = {summLen:{} for summLen in summaryLens}
        # for each system, collect the scores for each summary length:
        for line in lines[1:]:
            lineParts = line.strip().split(',')
            systemName = lineParts[0]
            systemNames[systemName] = 1
            for summLenInd, summLen in enumerate(summaryLens):
                data[summLen][systemName] = lineParts[summLenInd+1]
    
    systemNamesSorted = sorted(systemNames.keys())
    
    # keep the differences of the system scores:
    scoreDiffs = {}
    for summLen in data:
        scoreDiffs[summLen] = getPairwiseDifferences(data[summLen], systemNamesSorted)
    

    return scoreDiffs, summaryLens, systemNamesSorted
    

def initDataStructureForAutoRankings(summaryLengths):
    '''
    To initialize a data strucure for all the automatic rankings.
    Dictionary with format:
    |_  rouge_type (from ROUGE_TYPES list)
        |_  summary_length
            |_  recall/precision/f1 -> {}

    Returns a newly created dictionary.
    '''
    data = {}
    for rougeType in ROUGE_TYPES:
        data[rougeType] = {}
        for summLen in summaryLengths:
            data[rougeType][summLen] = {'precision':{}, 'recall':{}, 'f1':{}}
    
    return data
    
def loadAndScore_AutomaticAssessment(autoAssessmentCSVpath, systemNamesSorted):
    '''
    Load the auto assessment data from the CSV specified, and rank the systems by scores.
    Returns a dictionary of format:
    |_  rougeType
        |_  summaryLength
            |_  recall/precision/f1
                |_  sysNamePair -> recallScoreDifference
            
    Assuming title line example: ROUGE_type,050_r,100_r,200_r,400_r,050_p,100_p,200_p,400_p,050_f,100_f,200_f,400_f
    '''
    with open(autoAssessmentCSVpath, 'r') as fIn:
        lines = fIn.readlines()
        
        # for the summaryLengths, take the first N/3 column names (_r/_p/_f repeats for each length) after the
        # first 'ROUGE_type' column, and then take the string until the '_<r|p|f>' suffix:
        firstLineParts = lines[0].strip().split(',')[1:]
        summaryLens = [firstLineParts[i][:-2] for i in range(len(firstLineParts)/3)]
        
        # initialize the data structure for the rankings:
        data = initDataStructureForAutoRankings(summaryLens)
        
        # Go over the rest of the lines.
        # An empty line means a system section will start soon.
        # A line with just one value is the system name.
        # A line with multiple columns looks like this example:
        #   R4,0.0046,0.0102,0.0178,0.0339,0.01915,0.0190,0.0159,0.015,0.0075,0.0132,0.0168,0.0208
        for line in lines[1:]:
            lineParts = line.strip().split(',')
            
            # line with single value, is the system name:
            if len(lineParts) == 1:
                systemName = lineParts[0]
                
            # line with multiple values is a data row:
            elif len(lineParts) > 1:
                rougeType = lineParts[0] # first column is the rouge type
                dataRow = lineParts[1:] # the rest of the row is the recall/precision/f1 for each length
                for summLenInd, summLen in enumerate(summaryLens):
                    data[rougeType][summLen]['recall'][systemName] = dataRow[summLenInd]
                    data[rougeType][summLen]['precision'][systemName] = dataRow[summLenInd + len(summaryLens)*1]
                    data[rougeType][summLen]['f1'][systemName] = dataRow[summLenInd + len(summaryLens)*2]
            
    # get score differences between pairs of systems for each rouge type, for each summary length and for rec/prec/f1:
    scoreDiffs = {}
    for rougeType in ROUGE_TYPES:
        scoreDiffs[rougeType] = {}
        for summLen in summaryLens:
            scoreDiffs[rougeType][summLen] = {
                'precision' : getPairwiseDifferences(data[rougeType][summLen]['precision'], systemNamesSorted),
                'recall' : getPairwiseDifferences(data[rougeType][summLen]['recall'], systemNamesSorted),
                'f1' : getPairwiseDifferences(data[rougeType][summLen]['f1'], systemNamesSorted)
                }
    
    return scoreDiffs

def getCorrelations(scoreDiffsHuman, scoreDiffsAuto):
    '''
    Gets all the correlation calculations between the human and auto pair-wise score difference lists provided.
    Returns a dictionary of format:
    |_  rougeType
        |_  summLen
            |_  recall/precision/f1
                |_  pearson/spearman/kendall -> correlation scores
    '''
    correlations = {}
    for rougeType in ROUGE_TYPES:
        print('Computing correlations for ROUGE: '+rougeType)
        correlations[rougeType] = {}
        for summLen in scoreDiffsHuman:
            print('\tComputing correlations for summLen: '+summLen)
            if summLen in scoreDiffsAuto[rougeType]:
                correlations[rougeType][summLen] = {}
                correlations[rougeType][summLen]['recall'] = \
                    computeCorrelations(scoreDiffsAuto[rougeType][summLen]['recall'], scoreDiffsHuman[summLen])
                correlations[rougeType][summLen]['precision'] = \
                    computeCorrelations(scoreDiffsAuto[rougeType][summLen]['precision'], scoreDiffsHuman[summLen])
                correlations[rougeType][summLen]['f1'] = \
                    computeCorrelations(scoreDiffsAuto[rougeType][summLen]['f1'], scoreDiffsHuman[summLen])
                    
    return correlations
    
def computeCorrelations(scoreDiffsDictAuto, scoreDiffsDictHuman):
    '''
    Returns a dictionary of pearson/spearman/kendall values for the two ranked lists given.
    The input is two lists of tuples of format (systemName, score) in different orders.
    They will be placed in order for the purpose of finding the correlations of rankings.
    '''
    # prepare the ranked lists for the correlation functions:
    listAutoPreped, listHumanPreped = prepareListsForCorrelation(scoreDiffsDictAuto, scoreDiffsDictHuman)
    
    # calculate the correlations:
    correlations = {}
    correlations['pearson'] = scipy.stats.pearsonr(listAutoPreped, listHumanPreped)[0]
    correlations['spearman'] = scipy.stats.spearmanr(listAutoPreped, listHumanPreped)[0]
    correlations['kendall'] = scipy.stats.kendalltau(listAutoPreped, listHumanPreped)[0]
    
    return correlations
    
def prepareListsForCorrelation(dict1, dict2):
    '''
    Puts the second list in the order of the first list in terms of the first value in the tuples.
    Makes sure values perfectly intersect.
    Returns two lists with an equal intersection of systemNames, with the scores only.
    '''
    # get the system names intersection of the two lists:
    set1 = set(dict1.keys())
    set2 = set(dict2.keys())
    intersectingSetOfSysNames = set1.intersection(set2)
    
    # create the two lists of score in the same system order:
    rankedList1 = [float(dict1[sysTuple]) for sysTuple in intersectingSetOfSysNames]
    rankedList2 = [float(dict2[sysTuple]) for sysTuple in intersectingSetOfSysNames]
    
    return rankedList1, rankedList2
    
def outputToCsv(correlations, outputFolderpath, summaryLengths):
    '''
    Outputs the correlation tables to CSV files with the following format in the
    folder specified. A table is created for recall/precision/f1 by pearson/spearman/kendall,
    nine CSVs in all.
    
    Method  LEN1    LEN2    LEN3    LEN4
    R1
    R2
    R3
    R4
    RL
    RS
    RSU
    RW
    
    '''
    # find a name that wasn't used yet for the output folder:
    folderNum = 1
    while os.path.exists(outputFolderpath):
        outputFolderpath = '{}_{}'.format(outputFolderpath, folderNum)
    os.makedirs(outputFolderpath) # create the output dir
    
    # write the table for each metric_corrType:
    for measure in ['recall','precision','f1']:
        for corrType in ['pearson', 'spearman', 'kendall']:
            csvFilepath = os.path.join(outputFolderpath, 'correlations_{}_{}.csv'.format(measure, corrType))
            with open(csvFilepath, 'w') as fOut:
                titleLine = ','.join(['Method']+[summLen for summLen in summaryLengths]) # Method,<len1>,<len2>,<len3>,<len4>
                fOut.write(titleLine+'\n')
                # each line is a ROUGE type and the correlation values for the lengths
                for rougeType in ROUGE_TYPES:
                    corrLine = ','.join([rougeType]+['{:.2f}'.format(correlations[rougeType][summLen][measure][corrType]) for summLen in summaryLengths])
                    fOut.write(corrLine+'\n')
                    

def main():
    # go over all inputs:
    for humanAssessmentCsvPath, autoAssessmentCsvPath, outputCsvPath in INPUTS:
        print('--- Computing correlations for next input...')
        # load the human pairwise score differences:
        scoreDiffsHuman, summaryLengths, systemNamesSorted = loadAndScore_humanAssessment(humanAssessmentCsvPath)
        # load the ROUGE pairwise score differences:
        scoreDiffsAuto = loadAndScore_AutomaticAssessment(autoAssessmentCsvPath, systemNamesSorted)
        # get the correlations between the human and ROUGE pairwise scores:
        correlations = getCorrelations(scoreDiffsHuman, scoreDiffsAuto)
        # output to CSV files:
        outputToCsv(correlations, outputCsvPath, summaryLengths)
                    
if __name__ == '__main__':
    main()