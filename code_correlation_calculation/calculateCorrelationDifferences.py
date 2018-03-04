'''
This script is for writing out the differences between a source correlations table and other correlation tables
to easily see the improvement/deterioration of the correlations when using different configurations
of model summaries as opposed to the standard method of comparing a system summary to model summaries 
of the same length.

Change the FROM_DATA_FOLDER, TO_DATA_INFO and OUTPUT_FOLDER variables for your needs.

To run: python calculateCorrelationDifferences.py
Outputs: a folder of correlation difference CSVs
'''

import os

# CHANGE THESE FOR YOUR NEEDS:
# the folder with the correlations against which to compare:
FROM_DATA_FOLDER = 'output2001_sameLen_correlations'
# the configurations to compare to FROM_DATA_FOLDER
# format: (aliasNameForConfig, folderpath)
TO_DATA_INFO = [
    # examples:
    ('to050', 'output2001_to050_correlations'),
    ('toOneShorter', 'output2001_toOneShorter_correlations'),
    ]
# the output folder for the differences:
OUTPUT_FOLDER = 'deltas2001'

# the ROUGE types to average on. Possibilities: R1, R2, R3, R4, RSU, RL, RW, RS
ROUGE_TYPES_TO_USE = ['R1', 'R2', 'RL', 'RSU']


def getCorrelationNumbers(dataFolder):
    '''
    Gets the correlation values from the specified folder of CSVs.
    Expects folders and files from the output of the script 'calculate_correlations.py'
    
    Returns a dictionary in the format:
    |_ [recall|precision|f1]
        |_ [pearson|spearman|kendall]
            |_ rougeType
                |_ summLength -> correlation value
    '''
    data = {}
    for filename in os.listdir(dataFolder):
        # example filename: correlations_recall_pearson.csv
        # example input file:
        #  Method,050,100,200,400
        #  R1,0.55,0.69,0.87,0.79
        #  R2,0.54,0.71,0.90,0.94
        #  ...

        filepath = os.path.join(dataFolder, filename)
        filenameParts = filename.split('.')[0].split('_')
        # ignore filenames with less than 3 parts separated by underscores:
        if len(filenameParts) < 3:
            continue
        metric = filenameParts[1]
        correlationType = filenameParts[2]
        
        # read the values:
        with open(filepath, 'r') as fIn:
            for line in fIn:
                strippedLine = line.strip()
                # title line - get the summary lengths:
                if strippedLine.startswith('Method'):
                    summLens = strippedLine.split(',')[1:]
                # non-title lines:
                else:
                    lineParts = strippedLine.split(',')
                    rougeType = lineParts[0]
                    corrValues = map(float, lineParts[1:])
                    
                    # store the correlation values for the current line (rougeType)
                    for summLenInd, summLen in enumerate(summLens):
                        if not metric in data:
                            data[metric] = {}
                        if not correlationType in data[metric]:
                            data[metric][correlationType] = {}
                        if not rougeType in data[metric][correlationType]:
                            data[metric][correlationType][rougeType] = {}
                        data[metric][correlationType][rougeType][summLen] = corrValues[summLenInd]
                        
    return data, summLens


def outputDeltas(fromData, allToData, outputFolder, comparisonTypes, summLens, rougeTypes):
    '''
    for each metric_correlation, create a table file with:
    title line:   comparison,                     <len1>, <len2>, ...
    rows:         <comparisonName_rougeType>,     <val1>, <val2>, ...
    where a value is the difference between the "from" correlation value to the comparison-"to" correlation value.
    bottom row:   average,                        <len1Avg>,  <len2Avg>,  ...
      of averages of the specified ROUGE types to use.
      
    Example file (one per metric_corrType):
    "
    comparison,050,100,200,400,avgPerRouge

    to050_R1,0.0,0.08,0.04,0.14,0.065
    to050_R2,0.0,0.02,-0.01,-0.02,-0.0025
    to050_RL,0.0,0.07,0.03,0.12,0.055
    to050_RSU,0.0,0.06,0.04,0.15,0.0625
    avgPerLen,0.000,0.057,0.025,0.098,0.045

    to100_R1,-0.01,0.0,0.02,0.11,0.03
    to100_R2,-0.04,0.0,0.02,-0.01,-0.0075
    to100_RL,0.0,0.0,0.02,0.09,0.0275
    to100_RSU,0.0,0.0,0.05,0.12,0.0425
    avgPerLen,-0.012,0.000,0.027,0.078,0.023125
    "
    
    Also outputs "final" difference files:
    example:
    "
    comparison,050,100,200,400,final

    to050,0.0,0.0575,0.025,0.0975,0.045
    to100,-0.0125,0.0,0.0275,0.0775,0.023125
    "
    '''
    # create the output directory:
    if not os.path.exists(outputFolder):
        os.makedirs(outputFolder)
    
    for metric in fromData:
        for correlationType in fromData[metric]:
            tableFilepath = os.path.join(outputFolder, 'deltas_{}_{}.csv'.format(metric, correlationType))
            print('Createing table: ' + tableFilepath)
            
            # keep track of the values:
            finalValsPerLen = {comparisonType:{} for comparisonType in comparisonTypes}
            finalVals = {comparisonType:-1 for comparisonType in comparisonTypes}
            with open(tableFilepath, 'w') as fOut:
                # title line ("comparison,<len1>,<len2>,..."):
                fOut.write(','.join(['comparison'] + summLens + ['avgPerRouge']) + '\n\n')

                for comparisonType in comparisonTypes:
                    toData = allToData[comparisonType]
                    print('\tline: ' + comparisonType)
                    sumOfDeltasPerLength = {}
                    numOfDeltasPerLength = {}
                    for rougeType in rougeTypes:
                        # the row for a single rouge type of the current comparison type
                        #  ("<compareType_rougeType>,<len1Delta>,<len2Delta>,...,<avgOfAllLensOfCurRouge>")
                        sumOfDeltasForRougeType = 0.0
                        dataLineParts = ['{}_{}'.format(comparisonType, rougeType)]
                        for summLen in summLens:
                            if toData[metric][correlationType][rougeType][summLen] >= -1:
                                delta = toData[metric][correlationType][rougeType][summLen] - fromData[metric][correlationType][rougeType][summLen]
                                sumOfDeltasPerLength[summLen] = sumOfDeltasPerLength.get(summLen, 0.) + delta
                                numOfDeltasPerLength[summLen] = numOfDeltasPerLength.get(summLen, 0) + 1
                                sumOfDeltasForRougeType += delta
                            else:
                                delta = -999
                            dataLineParts.append(delta)
                        
                        dataLineParts.append(sumOfDeltasForRougeType / len(summLens))
                        fOut.write(','.join(map(str, dataLineParts)) + '\n')
                        
                    # the bottom row of the current comparison type ("avgPerLen,<avgOfLen1>,<avgOfLen2>,...,<avgOfLenOfRougeType>")
                    avgDeltasPerLength = [sumOfDeltasPerLength[summLen] / numOfDeltasPerLength[summLen] if summLen in sumOfDeltasPerLength else 0. for summLen in summLens]
                    dataLineParts = ['avgPerLen']
                    dataLineParts += ['{:.3f}'.format(avgDeltaPerLen) for avgDeltaPerLen in avgDeltasPerLength]
                    finalValForComparisonType = sum(avgDeltasPerLength) / len(summLens)
                    dataLineParts.append(finalValForComparisonType)
                    fOut.write(','.join(map(str, dataLineParts)) + '\n')
                    finalValsPerLen[comparisonType] = {summLen:avgDeltaPerLen for summLen, avgDeltaPerLen in zip(summLens, avgDeltasPerLength)}
                    finalVals[comparisonType] = finalValForComparisonType
                    
                    fOut.write('\n')
                    
            # write the overall final values in a "final" file:
            finalFilepath = os.path.join(outputFolder, 'final_deltas_{}_{}.csv'.format(metric, correlationType))
            with open(finalFilepath, 'w') as fOut:
                fOut.write(','.join(['comparison'] + summLens + ['final']) + '\n\n')
                for comparisonType in comparisonTypes:
                    rowParts = [comparisonType] + map(str, [finalValsPerLen[comparisonType][summLen] for summLen in summLens]) + [str(finalVals[comparisonType])]
                    fOut.write(','.join(rowParts) + '\n')

                        
def main():
    # get the correlation values of the source configuration:
    fromData, summaryLengths = getCorrelationNumbers(FROM_DATA_FOLDER)
    allToData = {}
    comparisonTypes = []
    # for each configuration to compare:
    for toDataName, toDatafolder in TO_DATA_INFO:
        # get the correlation values of the target configuration:
        toData, _ = getCorrelationNumbers(toDatafolder)
        allToData[toDataName] = toData
        
        comparisonTypes.append(toDataName)
    # output to folders:
    outputDeltas(fromData, allToData, OUTPUT_FOLDER, comparisonTypes, summaryLengths, ROUGE_TYPES_TO_USE)
                        
if __name__ == '__main__':
    main()