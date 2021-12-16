'''
This script is for calculating the ROUGE scores of system summaries against reference summaries in different configurations.
The script can run over several configurations as specified in the INPUTS list.

Change the INPUTS and INPUT_FORMAT variables for your inputs.

To run: python calculateRouge.py
Outputs: a CSV file with the ROUGE scores
'''

import os
from pyrouge import Rouge155
import time


# The comparison types between system and model summaries:
COMPARE_SAME_LEN = 0 # comparing a system summary to the model summaries of the same length
COMPARE_VARYING_LEN = 1 # comparing a system summary to the all possible model summaries (the prepared model summary folder decides on the input)
COMPARE_TO_LARGEST = 3 # comparing a system summary to the model summaries of the longest length only
COMPARE_TO_SMALLEST = 4 # comparing a system summary to the model summaries of the shortest length only
COMPARE_TO_SECONDSMALLEST = 5 # comparing a system summary to the model summaries of the second shortest length only
COMPARE_TO_SECONDLARGEST = 6 # comparing a system summary to the model summaries of the second longest length only
COMPARE_TO_ONE_SMALLER = 8 # comparing a system summary to the model summaries of a single length shorter (shortest length not processed)
COMPARE_TO_ONE_LARGER = 9 # comparing a system summary to the model summaries of a single length longer (longest length not processed)

# A parameter whether to remove the stopwords from the summaries.
REMOVE_STOP_WORDS = True
LEAVE_STOP_WORDS = False

# The rouge types. Keys are internal IDs for this code, and the values
# are the strings used in the dictioanry returned by the Rouge155 module.
ROUGE_TYPES = {
    'R1':'rouge_1',
    'R2':'rouge_2',
    'R3':'rouge_3',
    'R4':'rouge_4',
    'RSU':'rouge_su4',
    'RL':'rouge_l',
    'RW':'rouge_w_1.2',
    'RS':'rouge_s4'}

# The format in which the input summaries are. SEE is the DUC html format which ROUGE uses.
# Regular text format can also be used, where each sentence is on a separate line (has time and space overhead).
FORMAT_SEE = 'SEE'
FORMAT_TEXT = 'text'

# The input format to use - CHANGE THIS TO "FORMAT_TEXT" IF THE INPUT SUMMARIES ARE NOT IN SEE FORMAT:
INPUT_FORMAT = FORMAT_TEXT
# THE INPUTS TO RUN IN A LOOP - CHANGE YOUR INPUTS HERE:
# Each input: (comparisonType, modelSummariesFolderPath, systemSummariesFolderPath, outputCSVfilepath, DUC year [2001|2002], stopWordsMode)
INPUTS = [(COMPARE_SAME_LEN, 'golden2004','system2004', '2002_diffLens2007.csv', 2002, REMOVE_STOP_WORDS)]
    # EXAMPLES:
    # (COMPARE_VARYING_LEN, 'data/DUC2002/SEE.model_edited.abstracts.in.edus', 'data/DUC2002/SEE.peer_abstracts.in.sentences', '2002_diffLens.csv', 2002, LEAVE_STOP_WORDS),
    # (COMPARE_SAME_LEN, 'data/DUC2001/see.models', 'data/DUC2001/submissions.for.SEE', '2001_sameLen_noStops.csv', 2001, REMOVE_STOP_WORDS),
    # (COMPARE_TO_SMALLEST, 'data/DUC2002/SEE.model_edited.abstracts.in.edus', 'data/DUC2002/SEE.peer_abstracts.in.sentences', '2002_to010_noStops.csv', 2002, REMOVE_STOP_WORDS),
    # (COMPARE_TO_ONE_SMALLER, 'data/DUC2001/see.models', 'data/DUC2001/submissions.for.SEE', '2001_toOneShorter_noStops.csv', 2001, REMOVE_STOP_WORDS)
    # ]
    
def getComparisonOptions(folderSystems, folderModels):
    '''
    Gets all the task names, summary lengths and system names from the system filenames of the Multi-doc summaries.
    Assuming format <taskName>.<M for Multi/P for Perdoc>.<summLen>.<AssessorId>.<systemId>.<txt/html> for multi-text
        example: D061.M.010.J.16.txt
    or <taskName>.<M for Multi/P for Perdoc>.<summLen>.<AssessorId>.<systemId>.<singleFileName>.<txt/html> for single-text
        example: D061.P.100.J.16.AP880916-0060.txt
        
    Returns three orderer list of: taskNames, systemNames, summaryLengths
    '''
    # keep the info for the multi-doc and per-doc separately:
    taskNames = {'M':{},'P':{}}
    systemNames = {'M':{},'P':{}}
    summaryLengths = {'M':{},'P':{}}
    
    # iterate through the filenames and keep the info according to the filename parts:
    for filename in os.listdir(folderSystems):
        nameParts = filename.split('.')
        if len(nameParts) < 5:
            continue
            
        taskName = nameParts[0]
        summaryLength = nameParts[2]
        systemName = nameParts[4]
        
        # MultiDoc (e.g.: D061.M.010.J.16.txt)
        if nameParts[1] == 'M':
            taskNames['M'][taskName] = 1
            summaryLengths['M'][summaryLength] = 1
            systemNames['M'][systemName] = 1
            
        # PerDoc (e.g.: D061.P.100.J.16.AP880916-0060.txt)
        elif nameParts[1] == 'P':
            taskNames['P'][taskName] = 1
            summaryLengths['P'][summaryLength] = 1
            systemNames['P'][systemName] = 1
            
    # remove the model names from the system names found:
    #for filename in os.listdir(folderModels):
    #    nameParts = filename.split('.')
    #    if len(nameParts) < 5:
    #        continue
    #    modelName = nameParts[4]
    #    if nameParts[1] == 'M' and modelName in systemNames['M']:
    #        del systemNames['M'][modelName]
    #    elif nameParts[1] == 'P' and modelName in systemNames['P']:
    #        del systemNames['P'][modelName]
    
    # take just the multi-doc info and sort it:
    taskNames = sorted(taskNames['M'].keys())
    systemNames = sorted(systemNames['M'].keys())
    summaryLengths = sorted(summaryLengths['M'].keys())
    
    return taskNames, systemNames, summaryLengths
    
def initDataStructure(systemNames, summaryLengths):
    '''
    To initialize a data strucure for all the ROUGE values.
    In the format of dictionaries:
    |_  system_name
        |_  summary_length
            |_  rouge_type (from ROUGE_TYPES keys)
                |_  < precision=-1 | recall=-1 | f1=-1 >
    
    Returns a newly created dictionary.
    '''
    data = {}
    for sysName in systemNames:
        data[sysName] = {}
        for summLen in summaryLengths:
            data[sysName][summLen] = {}
            for rougeType in ROUGE_TYPES:
                data[sysName][summLen][rougeType] = {'precision':-1, 'recall':-1, 'f1':-1}
    return data
    
def storeData(dataStruct, sysName, summLen, newData):
    '''
    Stores the Rouge155 module dictionary information into the dataStruct provided at
    the sysName, summLen entry.
    '''
    for rougeType, rougeDataStr in ROUGE_TYPES.items():
        dataStruct[sysName][summLen][rougeType]['recall'] = newData[rougeDataStr+'_recall']
        dataStruct[sysName][summLen][rougeType]['precision'] = newData[rougeDataStr+'_precision']
        dataStruct[sysName][summLen][rougeType]['f1'] = newData[rougeDataStr+'_f_score']

def runRougeCombinations(comparisonType, folderSystems, folderModels, systemNames, summaryLengths, ducVersion, stopWordsRemoval):
    '''
    Get the ROUGE values for all the system vs model combinations.
    Measures each system summary against:
        - *all* model summaries (comparisonType==COMPARE_VARYING_LEN)
        - *same length* model summaries (comparisonType==COMPARE_SAME_LEN)
        - *smallest length* model summaries (comparisonType==COMPARE_TO_SMALLEST)
        - *second smallest length* model summaries (comparisonType==COMPARE_TO_SECONDSMALLEST)
        - *second longest length* model summaries (comparisonType==COMPARE_TO_SECONDLARGEST)
        - *longest length* model summaries (comparisonType==COMPARE_TO_LARGEST)
        - *one smaller length* model summaries (comparisonType==COMPARE_TO_ONE_SMALLER)
        - *one larger length* model summaries (comparisonType==COMPARE_TO_ONE_LARGER)
    Returns a dictionary of the format specified in the initDataStructure method.
    '''
    print('Calculating all ROUGE scores...')
    
    # initialize the ROUGE object:
    rougeCalculator = Rouge155()
                
    # initialize the data structure to hold all the ROUGE results:
    allData = initDataStructure(systemNames, summaryLengths)
    
    # for each system get the ROUGE results separately:
    for sysName in systemNames:
        print('\t--- On system: {} ---'.format(sysName))
        
        # for each summary length get the ROUGE results separately:
        for summLen in summaryLengths:
            # the reference summary files to use for this iteration (regex of filenames for pyrouge):
            refSummFilenamePattern = getModelSummariesPattern(comparisonType, summLen, summaryLengths, ducVersion)
            
            # The system summary files to use for this iteration are the multi-doc ones
            # for the current length, for the current system:
            sysSummFilenamePattern = '(.*).M.{}.(.*)\.{}.html'.format(summLen, sysName)
            
            # set the properties for the ROUGE object:
            rougeCalculator.system_dir = folderSystems
            rougeCalculator.model_dir = folderModels
            rougeCalculator.system_filename_pattern = sysSummFilenamePattern
            rougeCalculator.model_filename_pattern = refSummFilenamePattern
            
            # add the ROUGE flag to truncate the system summaries according to their defined length:
            rougeAdditionalParams = ['-l', int(summLen)]
            # possibly add the ROUGE flag to remove stop words:
            stopWords = ''
            if stopWordsRemoval == REMOVE_STOP_WORDS:
                rougeAdditionalParams.append('-s')
                stopWords = '-s'
            rougeCalculator.add_rouge_args_to_default(rougeAdditionalParams)
            
            try:
                # When using plain text format, run convert_and_evaluate.
                # For SEE format, use just evaluate(), since convert is for text->SEE conversion.
                if INPUT_FORMAT == FORMAT_SEE:
                    output = rougeCalculator.evaluate()
                elif INPUT_FORMAT == FORMAT_TEXT:
                    output = rougeCalculator.convert_and_evaluate(split_sentences=True, rouge_args='-e {} -c 95 -2 4 -U -r 1000 -n 4 -w 1.2 -a -l {} {}'.format(rougeCalculator._data_dir,int(summLen), stopWords))
                    
                # get the ROUGE output:
                output_dict = rougeCalculator.output_to_dict(output)
                # keep the data in the allData data structure:
                storeData(allData, sysName, summLen, output_dict)
            except:
                pass
        #break ### break here to check just the first system on all tasks
    
    
    print('Current ROUGEing done!')
    return allData
    
def getModelSummariesPattern(comparisonType, summLen, summaryLengthsOrdered, ducVersion):
    '''
    Defines the model summary filename regex for pyrouge, according to the different parameters requested.
    '''
    # Note: The "#ID#" is the pyrouge way of saying to match the task name of the system to the same task for the model.
    
    if comparisonType == COMPARE_SAME_LEN:
        refSummFilenamePattern = '#ID#.M.{}.(.*).(.*).html'.format(summLen)
    elif comparisonType == COMPARE_VARYING_LEN:
        refSummFilenamePattern = '#ID#.M.(.*).(.*).(.*).html' # all summaries
    elif comparisonType == COMPARE_TO_SMALLEST:
        refSummFilenamePattern = '#ID#.M.{}.(.*).(.*).html'.format(summaryLengthsOrdered[0])
    elif comparisonType == COMPARE_TO_SECONDSMALLEST:
        refSummFilenamePattern = '#ID#.M.{}.(.*).(.*).html'.format(summaryLengthsOrdered[1])
    elif comparisonType == COMPARE_TO_SECONDLARGEST:
        refSummFilenamePattern = '#ID#.M.{}.(.*).(.*).html'.format(summaryLengthsOrdered[-2])
    elif comparisonType == COMPARE_TO_LARGEST:
        refSummFilenamePattern = '#ID#.M.{}.(.*).(.*).html'.format(summaryLengthsOrdered[-1])
    elif comparisonType == COMPARE_TO_ONE_SMALLER:
        # use the summary length that is one shorter than the system summary's:
        summLenIndexToUse = summaryLengthsOrdered.index(summLen) - 1
        if summLenIndexToUse >= 0:
            summLenToUse = summaryLengthsOrdered[summLenIndexToUse]
        else:
            summLenToUse = '999' # will do nothing since no filename with the regex will be found
        refSummFilenamePattern = '#ID#.M.{}.(.*).(.*).html'.format(summLenToUse)
    elif comparisonType == COMPARE_TO_ONE_LARGER:
        # use the summary length that is one longer than the system summary's:
        summLenIndexToUse = summaryLengthsOrdered.index(summLen) + 1
        if summLenIndexToUse < len(summaryLengthsOrdered):
            summLenToUse = summaryLengthsOrdered[summLenIndexToUse]
        else:
            summLenToUse = '999' # will do nothing since no filename with the regex will be found
        refSummFilenamePattern = '#ID#.M.{}.(.*).(.*).html'.format(summLenToUse)
            
    return refSummFilenamePattern
    
def outputToCsv(analyzedData, outputFilepath, systemNames, summaryLengths):
    '''
    Outputs the analyzedData to a CSV file with the format:
    ROUGE_type,<summLen1>_r,<summLen2>_r,<summLenK>_r,<summLen1>_p,<summLen2>_p,<summLenK>_p,<summLen1>_f,<summLen2>_f,<summLenK>_f
    where each line is a rougeType, and systems are divided into sections.
    '''
    with open(outputFilepath, 'w') as outF:
        # header line
        # example: ROUGE_type,050_r,100_r,200_r,400_r,050_p,100_p,200_p,400_p,050_f,100_f,200_f,400_f
        firstLineParts = ['ROUGE_type']
        firstLineParts.extend(['{}_{}'.format(summLen, measure_type) for measure_type in ['r', 'p', 'f'] for summLen in summaryLengths])
        firstLine = ','.join(firstLineParts)
        outF.write(firstLine+'\n\n')
        
        # the csv is divided into section for each system:
        for sysName in systemNames:
            outF.write(sysName+'\n')
            if sysName in analyzedData:
                # each line for the system is a specific rouge type:
                for rougeType in ROUGE_TYPES:
                    # the first column of the line is the rouge type:
                    lineParts = [rougeType]
                    
                    # the rest of the line is for the columns <sys_len>.<r/p/f>, if there's no value, then '-':
                    lineParts.extend([str(analyzedData[sysName][summLen][rougeType]['recall']) \
                        if analyzedData[sysName][summLen][rougeType]['recall'] != -1  \
                        else '-' \
                        for summLen in summaryLengths ])
                    lineParts.extend([str(analyzedData[sysName][summLen][rougeType]['precision']) \
                        if analyzedData[sysName][summLen][rougeType]['precision'] != -1  \
                        else '-' \
                        for summLen in summaryLengths ])
                    lineParts.extend([str(analyzedData[sysName][summLen][rougeType]['f1']) \
                        if analyzedData[sysName][summLen][rougeType]['f1'] != -1  \
                        else '-' \
                        for summLen in summaryLengths ])
                            
                    line = ','.join(lineParts)
                    outF.write(line+'\n')
            outF.write('\n\n')


def main():
    startTime = time.time()
    # Go over each input:
    for compareType, refFolder, sysFolder, outputPath, ducVersion, stopWordsRemoval in INPUTS:
        print('---- NEXT INPUT')
        # get the different options:
        taskNames, systemNames, summaryLengths = getComparisonOptions(sysFolder, refFolder)
        # get ROUGE scores:
        allData = runRougeCombinations(compareType, sysFolder, refFolder, systemNames, summaryLengths, ducVersion, stopWordsRemoval)
        # output scores to CSV:
        outputToCsv(allData, outputPath, systemNames, summaryLengths)
        curTime = time.time()
        print('Current input done! Elapsed time: {} seconds!'.format(curTime - startTime))
    print('---- DONE WITH ALL INPUTS')
    
if __name__ == '__main__':
    main()
