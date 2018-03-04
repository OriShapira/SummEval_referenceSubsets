'''
This script is for calculating the human scores assigned to summaries.
The script can run over several inputs as specified in the INPUTS list.

Change the INPUTS variable for your inputs.

To run: python calculateHumanAssessment.py
Outputs: a CSV file with the human assessment scores
'''

import os

# THE INPUTS TO RUN IN A LOOP - CHANGE THE PATHS TO THE HUMAN CSVS HERE:
# Each input: (ducVersion, HumanAssessmentTableFilepath, outputCSVpath)
INPUTS = [
    (2001, 'data/DUC2001/results1_table.txt', '2001_human.csv'),
    (2002, 'data/DUC2002/short.results.table', '2002_human.csv')
    ]

def getComparisonOptions(tableFile, ducVersion):
    '''
    Gets all the task names, summary lengths and system names from the huiman evaluation table file.
    Returns three dictionaries of format:
    |_  M (multi-doc) / P (per-doc)
        |_  <taskName>=1
    |_  M (multi-doc) / P (per-doc)
        |_  summaryLength=1
    |_  M (multi-doc) / P (per-doc)
        |_  systemName=1
    '''
    taskNames = {'M':{},'P':{}}
    systemNames = {'M':{},'P':{}}
    summaryLengths = {'M':{},'P':{}}
    
    # The DUC 2002 table has header lines to skip. DUC 2001 starts the data immediately with the first line:
    if ducVersion == 2001:
        processText = True
    elif ducVersion == 2002:
        processText = False
    
    with open(tableFile, 'r') as fTable:
        for line in fTable:
            lineStripped = line.strip()
            
            # for DUC 2002, skip the header lines:
            if not processText and ducVersion == 2002:
                # the first empty line means that from now the actual data starts:
                if lineStripped == '':
                    processText = True
                continue
            
            lineParts = lineStripped.split()
        
            taskName = lineParts[0]
            summaryLength = lineParts[3]
            if ducVersion == 2001:
                systemName = lineParts[7]
            elif ducVersion == 2002:
                systemName = lineParts[8]
            
            # MultiDoc:
            if lineParts[1] == 'M':
                taskNames['M'][taskName] = 1
                summaryLengths['M'][summaryLength] = 1
                systemNames['M'][systemName] = 1
                
            # PerDoc:
            elif lineParts[1] == 'P':
                taskNames['P'][taskName] = 1
                summaryLengths['P'][summaryLength] = 1
                systemNames['P'][systemName] = 1
                
    return taskNames, systemNames, summaryLengths

def initDataStructure(taskNames, systemNames, summaryLengths):
    '''
    To initialize a data strucure for all the ROUGE values.
    In the format of dictionaries:
    |_  system_name
        |_  summary_length
            |_  task_name -> score=-1
    
    Returns a newly created dictionary.
    '''
    data = {}
    for sysName in systemNames['M']:
        data[sysName] = {}
        for summLen in summaryLengths['M']:
            data[sysName][summLen] = {}
            for taskName in taskNames['M']:
                data[sysName][summLen][taskName] = -1
    
    return data

def getSystemScores(ducVersion, assessmentTableFile, taskNames, systemNames, summaryLengths):
    '''
    Gets the human assessment system scores for the DUC version specified (2001/2002) from the
    scores table file given. Pass in also the taskNames, systemNames and summaryLengths (as given
    from getComparisonOptions) to build the dataset.
    Returns a dictionary of the format described in initDataStructure.
    '''
    if ducVersion == 2001:
        return getSystemScores_DUC2001(assessmentTableFile, taskNames, systemNames, summaryLengths)
    elif ducVersion == 2002:
        return getSystemScores_DUC2002(assessmentTableFile, taskNames, systemNames, summaryLengths)
    else:
        return None
        
def getSystemScores_DUC2001(assessmentTableFile, taskNames, systemNames, summaryLengths):
    '''
    Gets the human assessment system scores for the DUC 2001 version from the
    scores table file given. Pass in also the taskNames, systemNames and summaryLengths (as given
    from getComparisonOptions) to build the dataset.
    Returns a dictionary of the format described in initDataStructure.
    '''
    allData = initDataStructure(taskNames, systemNames, summaryLengths)
    with open(assessmentTableFile, 'r') as fIn:
        for line in fIn:
            # example: D04 M --------------- 050 A  A A 1  3 2 2  0 4 0    2   2   1   0 0 -   1 2 1
            lineParts = line.strip().split()
            # only use the multi-document information (since only it has varying length summaries):
            if lineParts[1] == 'M':
                taskName = lineParts[0]
                summLen = lineParts[3]
                summarizerId = lineParts[7]
                numModelUnits = int(lineParts[14])
                
                # get the avg of the middle numbers of each triple at the end of the line
                # according to the number of model units (indices 18, 21, 24, ...):
                expressivenessScores = [int(lineParts[expressivenessScoreIndex]) \
                    for expressivenessScoreIndex in range(18, 19+(3*(numModelUnits-1)), 3)]
                avgExpressivenessScore = float(sum(expressivenessScores)) / numModelUnits
                
                allData[summarizerId][summLen][taskName] = avgExpressivenessScore
    
    return allData
    
def getSystemScores_DUC2002(assessmentTableFile, taskNames, systemNames, summaryLengths):
    '''
    Gets the human assessment system scores for the DUC 2002 version from the
    scores table file given. Pass in also the taskNames, systemNames and summaryLengths (as given
    from getComparisonOptions) to build the dataset.
    Returns a dictionary of the format described in initDataStructure.
    '''
    allData = initDataStructure(taskNames, systemNames, summaryLengths)
    processText = False # start processing data only after the first blank line
    with open(assessmentTableFile, 'r') as fIn:
        for line in fIn:
            lineStripped = line.strip()
            
            # wait for the empty line (after all the headers):
            if not processText:
                if lineStripped == '':
                    processText = True
                continue
                
            # example: D061 M --------------- 050  47 J   I I  19     2  0 0 0 0 0   0 0 0 1 0 1 0   0.00     5   5   0   7   0.400 0.600 0.400   0.287 0.420 0.267  
            lineParts = lineStripped.split()
            # only use the multi-document information (since only it has varying length summaries):
            if lineParts[1] == 'M':
                taskName = lineParts[0]
                summLen = lineParts[3]
                summarizerId = lineParts[8]
                meanCoverageScore = lineParts[27]
                
                allData[summarizerId][summLen][taskName] = float(meanCoverageScore)
    
    return allData


def analyzeData(allData):
    '''
    Measures the average expressiveness scores over all tasks for each system, at each summary length.
    Returns a dictionary of format:
    |_  systemName
        |_  summaryLength -> score
    with the average values for each.
    '''
    analyzedData = {} # init dictionary
    for sysName in allData:
        analyzedData[sysName] = {} # init dictionary for current system
        # now calculate the average scores for each summary length:
        for summLen in allData[sysName]:
            # collect all the separate task scores, discluding -1 values:
            scores = [allData[sysName][summLen][taskName] \
                for taskName in allData[sysName][summLen] \
                if allData[sysName][summLen][taskName] != -1]
            # store the average of the scores:
            if len(scores) > 0:
                analyzedData[sysName][summLen] = sum(scores) / len(scores)
                #print('{}\t{}\t{}\t{}'.format(sysName, summLen, zip(allData[sysName][summLen].keys(), scores), analyzedData[sysName][summLen]))
    
    return analyzedData

def outputToCsv(analyzedData, outputFilepath, systemNames, summaryLengths, allData):
    '''
    Outputs the analyzedData to a CSV file pf the format:
    <systen_name>,<summLen1>,<summLen2>,...,<summLenK>
    '''
    # keep the summary lengths and system names in order for easier reading of the CSV:
    summLens = sorted(summaryLengths['M'].keys())
    sysNames = sorted(systemNames['M'].keys())
    
    with open(outputFilepath, 'w') as outF:
        # header line
        # example: system_name,050,100,200,400
        firstLineParts = ['system_name']
        firstLineParts.extend(['{}'.format(summLen) for summLen in summLens])
        firstLine = ','.join(firstLineParts)
        outF.write(firstLine+'\n')
        
        for sysName in sysNames:
            # the first column of the line is the system name:
            lineParts = [sysName]
            
            # the rest of the line is for the columns <sys_len>, if there's no value, then '-':
            lineParts.extend([str(analyzedData[sysName][summLen]) \
                if sysName in analyzedData and summLen in analyzedData[sysName] \
                else '-' \
                for summLen in summLens])
                
            line = ','.join(lineParts)
            outF.write(line+'\n')
            
def main():
    # iterate over the inputs:
    for ducVersion, humanAssessmentTablePath, outputCsvPath in INPUTS:
        # get the task names, system names and summary lengths from the input file:
        taskNames, systemNames, summaryLengths = getComparisonOptions(humanAssessmentTablePath, ducVersion)
        # get the raw per summary scores:
        allData = getSystemScores(ducVersion, humanAssessmentTablePath, taskNames, systemNames, summaryLengths)
        # calculate overall system scores per length:
        analyzedData = analyzeData(allData)
        # output to CSV:
        outputToCsv(analyzedData, outputCsvPath, systemNames, summaryLengths, allData)
    
if __name__ == '__main__':
    main()