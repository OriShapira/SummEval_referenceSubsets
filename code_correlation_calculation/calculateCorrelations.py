'''
This script is for calculating the correlations between the human and ROUGE scores of system summaries.
The appropriate human csv and ROUGE csvs should be specified.
These were output by the scripts "calculateHumanAssessment.py" and "calculateRouge.py".
The script can run over several inputs as specified in the INPUTS list.

Change the INPUTS variable for your inputs.

To run: python calculateCorrelations.py
Outputs: a folder with CSVs for correlations
'''
import scipy.stats
import os

# THE INPUTS TO RUN IN A LOOP - CHANGE YOUR INPUTS HERE:
# the inputs to run on in the format "(humanAssessmentScoresTableFilepath, RougeScoresTableFilepath, outputCSVFolder)":
INPUTS = [
    # Examples:
    ('2001_human.csv', '2001_to050_noStops.csv', '2001_correlations_to050'),
    ('2002_human.csv', '2002_toOneShorter_noStops.csv', '2002_correlations_toOneShorter')
    ]
    

# The ROUGE types used within the scores data:
ROUGE_TYPES = ['R1', 'R2', 'R3', 'R4', 'RSU', 'RL', 'RW', 'RS']

def loadAndScore_humanAssessment(humanAssessmentCSVpath):
    '''
    Load the human assessment data from the CSV specified, and calculate the system scores.
    Returns:
        dictionary:
        |_ summary_length -> list of (sysName, score) tuples
        list of summary lengths
    '''
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
            for summLenInd, summLen in enumerate(summaryLens):
                data[summLen][systemName] = lineParts[summLenInd+1]
    
    # convert to list of tuples for each summary length:
    dataTuples = {}
    for summLen in data:
        dataTuples[summLen] = data[summLen].items() # list of tuples (sysName, score)

    return dataTuples, summaryLens
    

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
    
def loadAndScore_AutomaticAssessment(autoAssessmentCSVpath):
    '''
    Load the ROUGE assessment data from the CSV specified, and rank the systems by scores.
    Returns a dictionary of format:
    |_  rougeType
        |_  summaryLength
            |_  recall/precision/f1 -> list of (sysName, score) tuples
            
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
            
    # keep a list of (sysName, score) tuples for each rouge type, for each summary length and for rec/prec/f1:
    dataTuples = {}
    for rougeType in ROUGE_TYPES:
        dataTuples[rougeType] = {}
        for summLen in summaryLens:
            dataTuples[rougeType][summLen] = {
                'precision' : data[rougeType][summLen]['precision'].items(),
                'recall' : data[rougeType][summLen]['recall'].items(),
                'f1' : data[rougeType][summLen]['f1'].items()
                }
    
    return dataTuples

def getCorrelations(humanDataTuples, autoDataTuples):
    '''
    Gets all the correlation calculations between the human and auto ranked lists provided.
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
        for summLen in humanDataTuples:
            print('\tComputing correlations for summLen: '+summLen)
            if summLen in autoDataTuples[rougeType]:
                correlations[rougeType][summLen] = {}
                correlations[rougeType][summLen]['recall'] = \
                    computeCorrelations(autoDataTuples[rougeType][summLen]['recall'], humanDataTuples[summLen])
                correlations[rougeType][summLen]['precision'] = \
                    computeCorrelations(autoDataTuples[rougeType][summLen]['precision'], humanDataTuples[summLen])
                correlations[rougeType][summLen]['f1'] = \
                    computeCorrelations(autoDataTuples[rougeType][summLen]['f1'], humanDataTuples[summLen])
                    
    return correlations
    
def computeCorrelations(tuplesListAuto, tuplesListHuman):
    '''
    Returns a dictionary of pearson/spearman/kendall corellation values for the two ranked lists given.
    The input is two lists of tuples of format (systemName, score) in different orders.
    They will be placed in order for the purpose of finding the correlations of rankings.
    '''
    # prepare the ranked lists for the correlation functions:
    listAutoPreped, listHumanPreped = prepareListsForCorrelation(tuplesListAuto, tuplesListHuman)
    
    # calculate the correlations:
    correlations = {}
    correlations['pearson'] = scipy.stats.pearsonr(listAutoPreped, listHumanPreped)[0]
    correlations['spearman'] = scipy.stats.spearmanr(listAutoPreped, listHumanPreped)[0]
    correlations['kendall'] = scipy.stats.kendalltau(listAutoPreped, listHumanPreped)[0]
    
    return correlations
    
def prepareListsForCorrelation(tuplesList1, tuplesList2):
    '''
    Puts the second list in the order of the first list in terms of the first value in the tuples.
    Makes sure values perfectly intersect.
    Returns two lists with an equal intersection of systemNames, with the scores only (second part of tuple).
    '''
    # get the system names intersection of the two lists:
    set1 = set([sysName for sysName, score in tuplesList1 if score != '-'])
    set2 = set([sysName for sysName, score in tuplesList2 if score != '-'])
    intersectingSetOfSysNames = set1.intersection(set2)
    
    # convert to dictionaries for easy access:
    dictOf1 = dict(tuplesList1)
    dictOf2 = dict(tuplesList2)
    
    # create the two lists of scores in the same system order:
    rankedList1 = [float(dictOf1[sysName]) for sysName in intersectingSetOfSysNames]
    rankedList2 = [float(dictOf2[sysName]) for sysName in intersectingSetOfSysNames]
    
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
        # load the human scores:
        humanDataTuples, summaryLengths = loadAndScore_humanAssessment(humanAssessmentCsvPath)
        # load the ROUGE scores:
        autoDataTuples = loadAndScore_AutomaticAssessment(autoAssessmentCsvPath)
        # get the correlations between the human and ROUGE scores:
        correlations = getCorrelations(humanDataTuples, autoDataTuples)
        # output to CSV files:
        outputToCsv(correlations, outputCsvPath, summaryLengths)
        
if __name__ == '__main__':
    main()