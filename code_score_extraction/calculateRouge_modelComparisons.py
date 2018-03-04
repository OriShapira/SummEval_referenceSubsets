'''
This script is for calculating the ROUGE scores between *model* summaries, in order to compare
authors and different length model summaries.
The script can run over several configurations as specified in the INPUTS list.

Change the INPUTS and INPUT_FORMAT variables for your inputs.

To run: python calculateRouge_modelComparisons.py
'''

import os
from pyrouge import Rouge155
import time

COMPARE_SAME_AUTHOR = 0 # comparing a model summary to another by the *same* author
COMPARE_OTHER_AUTHORS = 1 # comparing a model summary to those by the *other* author(s)
COMPARE_ALL_AUTHORS = 2 # comparing a model summary to those by *all* authors (including the origin summary's author)

# A parameter whether to remove the stopwords from the summaries.
REMOVE_STOP_WORDS = True
LEAVE_STOP_WORDS = False

# The rouge types. Keys are internal IDs for this code, and the values
# are the strings used in the dictionary returned by the Rouge155 module.
ROUGE_TYPES = {
    'R1':'rouge_1',
    'R2':'rouge_2',
    'R3':'rouge_3',
    'R4':'rouge_4',
    'RSU':'rouge_su*',
    'RL':'rouge_l',
    'RW':'rouge_w_1.2',
    'RS':'rouge_s*'}

# The format in which the input summaries are. SEE is the DUC html format which ROUGE uses.
# Regular text format can also be used, where each sentence is on a separate line (has time and space overhead).
FORMAT_SEE = 'SEE'
FORMAT_TEXT = 'text'

# The input format to use - CHANGE THIS TO "FORMAT_TEXT" IF THE INPUT SUMMARIES ARE NOT IN SEE FORMAT:
INPUT_FORMAT = FORMAT_SEE
    
# THE INPUTS TO RUN IN A LOOP - CHANGE YOUR INPUTS HERE:
# Each input: (modelSummariesFolderPath, outputCSVFolder, comparisonType, stopWordsMode)
INPUTS = [
    # examples:
    ('data/DUC2001/see.models', '2001_modelRougeComparisonSameAuthor_noStops', COMPARE_SAME_AUTHOR, REMOVE_STOP_WORDS),
    ('data/DUC2002/SEE.model_edited.abstracts.in.edus', '2002_modelRougeComparisonOtherAuthors_noStops', COMPARE_OTHER_AUTHORS, REMOVE_STOP_WORDS)
    ]
    
def getComparisonOptions(folderModels):
    '''
    Gets all the task names, summary lengths and system names from the system files.
    Assuming format <taskName>.<M for Multi/P for Perdoc>.<summLen>.<AssessorId>.<systemId>.txt for multi-text
        example: D061.M.010.J.16.txt
    or <taskName>.<M for Multi/P for Perdoc>.<summLen>.<AssessorId>.<systemId>.<singleFileName>.txt for single-text
        example: D061.P.100.J.16.AP880916-0060.txt
        
    Returns lists: taskNames, summaryLengths, systemNames
    '''
    taskNames = {}
    systemNames = {}
    summaryLengths = {}
    
    for filename in os.listdir(folderModels):
        nameParts = filename.split('.')
        if len(nameParts) < 5 or nameParts[1] != 'M':
            continue

        # Format example: D061.M.010.J.16.txt
        
        taskName = nameParts[0]
        summaryLength = nameParts[2]
        systemName = nameParts[4]
        
        taskNames[taskName] = 1
        summaryLengths[summaryLength] = 1
        systemNames[systemName] = 1
        
            
    taskNames = sorted(taskNames.keys())
    systemNames = sorted(systemNames.keys())
    summaryLengths = sorted(summaryLengths.keys())
    
    return taskNames, systemNames, summaryLengths
    
def initDataStructure(systemNames, summaryLengths):
    '''
    To initialize a data strucure for all the ROUGE values.
    In the format of dictionaries:
    |_  system_name
        |_  summary_length_of_checked
            |_  summary_length_of_model
                |_  rouge_type (from ROUGE_TYPES keys)
                    |_  <precision|recall|f1> -> -1
    
    Returns a newly created dictionary.
    '''
    data = {}
    for sysName in systemNames:
        data[sysName] = {}
        for summLen in summaryLengths:
            data[sysName][summLen] = {}
            for summLen2 in summaryLengths:
                data[sysName][summLen][summLen2] = {}
                for rougeType in ROUGE_TYPES:
                    data[sysName][summLen][summLen2][rougeType] = {'precision':-1, 'recall':-1, 'f1':-1}
    return data
    
def storeData(dataStruct, sysName, summLenChecked, summLenModel, newData):
    '''
    Stores the Rouge155 module dictionary information into the dataStruct provided at
    the sysName, summLen entry.
    '''
    for rougeType, rougeDataStr in ROUGE_TYPES.items():
        dataStruct[sysName][summLenChecked][summLenModel][rougeType]['recall'] = newData[rougeDataStr+'_recall']
        dataStruct[sysName][summLenChecked][summLenModel][rougeType]['precision'] = newData[rougeDataStr+'_precision']
        dataStruct[sysName][summLenChecked][summLenModel][rougeType]['f1'] = newData[rougeDataStr+'_f_score']

def runRougeCombinations(folderModels, systemNames, summaryLengths, comparisonType, stopWordsRemoval):
    '''
    Get the ROUGE values for all the different length combinations.
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
        
        # for each summary length of the model summary being checked:
        for summLenChecked in summaryLengths:
            
            for summLenModel in summaryLengths:
                # the reference summary files to use for this iteration:
                refSummFilenamePattern = getRefSummariesFilenamePattern( \
                    comparisonType, summLenModel, sysName, systemNames)
                
                # The system summary file to use for this iteration is the multi-doc ones
                # for the the current length, for the current system:
                sysSummFilenamePattern = '(.*).M.{}.(.*).{}.html'.format(summLenChecked, sysName)
                
                # set the properties for the ROUGE object:
                rougeCalculator.system_dir = folderModels
                rougeCalculator.model_dir = folderModels
                rougeCalculator.system_filename_pattern = sysSummFilenamePattern
                rougeCalculator.model_filename_pattern = refSummFilenamePattern
                
                if stopWordsRemoval == REMOVE_STOP_WORDS:
                    rougeCalculator.add_rouge_args_to_default(['-s'])
                
                try:
                    # When using plain text format, run convert_and_evaluate.
                    # For SEE format, use just evaluate(), since convert is for text->SEE conversion.
                    if INPUT_FORMAT == FORMAT_SEE:
                        output = rougeCalculator.evaluate()
                    elif INPUT_FORMAT == FORMAT_TEXT:
                        output = rougeCalculator.convert_and_evaluate()
                    output = rougeCalculator.evaluate()
                    output_dict = rougeCalculator.output_to_dict(output)
                    # keep the data in the allData data structure:
                    storeData(allData, sysName, summLenChecked, summLenModel, output_dict)
                except:
                    pass
    
    
    print('Current ROUGEing done!')
    return allData
    
def getRefSummariesFilenamePattern(comparisonType, summLenModel, sysName, allSystemNames):
    '''
    Defines the model summary filename regex for pyrouge, according to the different parameters requested.
    '''
    # Note: The "#ID#" is the pyrouge way of saying to match the task name of the system to the same task for the model.
    
    if comparisonType == COMPARE_SAME_AUTHOR:
        # same author (sysName), and in the current model summary length:
        refSummFilenamePattern = '#ID#.M.{}.(.*).{}.html'.format(summLenModel, sysName)
    elif comparisonType == COMPARE_ALL_AUTHORS:
        # all authors (systemNames), and in the current model summary length:
        refSummFilenamePattern = '#ID#.M.{}.(.*).(.*).html'.format(summLenModel)
    elif comparisonType == COMPARE_OTHER_AUTHORS:
        authorsListToUse = allSystemNames[:]
        authorsListToUse.remove(sysName)
        authorsRegexList = '(' + '|'.join(authorsListToUse) + ')'
        # all *other* authors (systemNames), and in the current model summary length:
        refSummFilenamePattern = '#ID#.M.{}.(.*).{}.html'.format(summLenModel, authorsRegexList)
    return refSummFilenamePattern


def getAverageScoresOverAllModels(analyzedData, systemNames, summaryLengths):
    '''
    Computes the average ROUGE scores per metric, rougeType, summLenChecked and summLenModel.
    Returns a dictionary of the format:
    |_  <precision|recall|f1>
        |_  rouge_type (from ROUGE_TYPES keys)
            |_  summary_length_of_checked
                |_  summary_length_of_model -> <avg_score>
    '''
    # prepare a dictionary for the sum of scores per metric,rougeType,summLenChecked,summLenModel:
    sumScoresAllModels = {
        metric:{rougeType:{summLenChecked:{summLenModel:0 
        for summLenModel in summaryLengths} 
        for summLenChecked in summaryLengths} 
        for rougeType in ROUGE_TYPES} 
        for metric in ['recall','precision','f1']}
    # prepare a dictionary for the count of scores per metric,rougeType,summLenChecked,summLenModel:
    countScoresAllModels = {
        metric:{rougeType:{summLenChecked:{summLenModel:0 
        for summLenModel in summaryLengths} 
        for summLenChecked in summaryLengths} 
        for rougeType in ROUGE_TYPES} 
        for metric in ['recall','precision','f1']}
    # add up the scores per metric,rougeType,summLenChecked,summLenModel, and count how many were considered:
    for sysName in systemNames:
        if sysName in analyzedData:
            for metricType in ['recall','precision','f1']:
                for rougeType in ROUGE_TYPES:
                    for summLenChecked in summaryLengths:
                        for summLenModel in summaryLengths:
                            if analyzedData[sysName][summLenChecked][summLenModel][rougeType][metricType] != -1:
                                sumScoresAllModels[metricType][rougeType][summLenChecked][summLenModel] += analyzedData[sysName][summLenChecked][summLenModel][rougeType][metricType]
                                countScoresAllModels[metricType][rougeType][summLenChecked][summLenModel] += 1
                                
    # prepare a dictionary for the averages of scores per metric,rougeType,summLenChecked,summLenModel:
    avgScoresAllModels = {
        metric:{rougeType:{summLenChecked:{summLenModel:0 
        for summLenModel in summaryLengths} 
        for summLenChecked in summaryLengths} 
        for rougeType in ROUGE_TYPES} 
        for metric in ['recall','precision','f1']}
    # get the averages per metric,rougeType,summLenChecked,summLenModel:                            
    for sysName in systemNames:
        for metricType in ['recall','precision','f1']:
            for rougeType in ROUGE_TYPES:
                for summLenChecked in summaryLengths:
                    summLenCheckedVal = int(summLenChecked)
                    for summLenModel in summaryLengths:
                        summLenModelVal = int(summLenModel)
                        if countScoresAllModels[metricType][rougeType][summLenChecked][summLenModel] > 0:
                            avgScoresAllModels[metricType][rougeType][summLenChecked][summLenModel] = \
                                sumScoresAllModels[metricType][rougeType][summLenChecked][summLenModel] / countScoresAllModels[metricType][rougeType][summLenChecked][summLenModel]
                                
                            # If the model summ len is larger than that of the checked summ, multiply the average by the relative size
                            # in order to get a clearer number. For example if we compare a 50 summ to a 400 summ, the max recall can 
                            # be 1/8 = 0.125, so a value of 0.1 is actually a recall of 80% (80% of the 50 summ is contained in the 400 summ).
                            # Showing 0.8 is clearer than 0.125.
                            if summLenModelVal > summLenCheckedVal:
                                mult = float(summLenModelVal / summLenCheckedVal)
                                avgScoresAllModels[metricType][rougeType][summLenChecked][summLenModel] *= mult
                                    
                        else:
                            avgScoresAllModels[metricType][rougeType][summLenChecked][summLenModel] = 0
    
    return avgScoresAllModels
                            
    
def outputToCsv(analyzedData, outputFolder, systemNames, summaryLengths, avgScoresAllModels):
    '''
    Outputs the analyzedData to CSV files (for each system (author) name and metric (recall/precision/f1) in the format:
    <ROUGE-type>,050,100,200,400
    050
    100
    200
    400
    for all ROUGE types.
    Also outputs the average analyzedData for all systems (authors) (per metric) in the same format.
    '''
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)
    
    # the csv is divided into section for each system:
    for sysName in systemNames:
        if sysName in analyzedData:
            for metricType in ['recall','precision','f1']:
                outputFilepath = os.path.join(outputFolder, '{}_{}.csv'.format(sysName, metricType))
                with open(outputFilepath, 'w') as outF:
                    outF.write('Rows:CheckedSize,Columns:referencesSize\n\n')
                    for rougeType in ROUGE_TYPES:
        
                        # each rouge type get a table:
                        firstLine = ','.join([rougeType] + [str(summLenModel) for summLenModel in summaryLengths])
                        outF.write(firstLine+'\n')
            
                        for summLenChecked in summaryLengths:
                        
                            # the first column of the line is the summary length of the summary being checked:
                            lineParts = [summLenChecked]
                            
                            # the rest of the line is for the columns <sys_len>.<r/p/f>, if there's no value, then '-':
                            lineParts.extend([str(analyzedData[sysName][summLenChecked][summLenModel][rougeType][metricType]) \
                                if analyzedData[sysName][summLenChecked][summLenModel][rougeType][metricType] != -1  \
                                else '-' \
                                for summLenModel in summaryLengths ])
                                    
                            line = ','.join(lineParts)
                            outF.write(line+'\n')
                        outF.write('\n')
                        
    # also write the overall average to three files (recall, precision, f1):
    for metricType in ['recall','precision','f1']:
        outputFilepath = os.path.join(outputFolder, 'TOTAL_{}.csv'.format(metricType))
        with open(outputFilepath, 'w') as outF:
            outF.write('Rows:CheckedSize,Columns:referencesSize,When refLen>checkedLen the values are multiplies by the relative size\n\n')
            for rougeType in ROUGE_TYPES:

                # each rouge type get a table:
                firstLine = ','.join([rougeType] + [str(summLenModel) for summLenModel in summaryLengths])
                outF.write(firstLine+'\n')
    
                for summLenChecked in summaryLengths:
                
                    # the first column of the line is the summary length of the summary being checked:
                    lineParts = [summLenChecked]
                    
                    # the rest of the line is for the columns <sys_len>.<r/p/f>, if there's no value, then '-':
                    lineParts.extend([str(avgScoresAllModels[metricType][rougeType][summLenChecked][summLenModel]) \
                        for summLenModel in summaryLengths ])
                            
                    line = ','.join(lineParts)
                    outF.write(line+'\n')
                outF.write('\n')


def main():
    startTime = time.time()
    # iterate over the inputs:
    for modelSummariesFolderPath, outputCSVFolder, comparisonType, stopWordsRemoval in INPUTS:
        print('---- NEXT INPUT')
        # get the task names, system names and summary lengths from the model summaries filenames:
        taskNames, systemNames, summaryLengths = getComparisonOptions(modelSummariesFolderPath)
        # get the ROUGE scores between the model authors:
        allData = runRougeCombinations(modelSummariesFolderPath, systemNames, summaryLengths, comparisonType, stopWordsRemoval)
        # get also the averages over all models:
        avgScoresAllModels = getAverageScoresOverAllModels(allData, systemNames, summaryLengths)
        # output to CSV files:
        outputToCsv(allData, outputCSVFolder, systemNames, summaryLengths, avgScoresAllModels)
        curTime = time.time()
        print('Current input done! Elapsed time: {} seconds!'.format(curTime - startTime))
    print('---- DONE WITH ALL INPUTS')
    
if __name__ == '__main__':
    main()