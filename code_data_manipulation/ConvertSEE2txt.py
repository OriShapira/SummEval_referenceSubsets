'''
This script reads in HTML files in SEE format and outputs the texts to new files
with a sentence per line. Keeps same file names but changes extension to txt.
Change the "workFolders" variable for your needs.

Run: python ConvertSEE2txt.py
'''

import sys
import os
import spacy

nlp = spacy.load('en')

def convert(inputFolder, outputFolder):
    for filename in os.listdir(inputFolder):
        if not filename.endswith('.html'):
            continue
        sourceFilepath = os.path.join(inputFolder, filename)
        targetFilepath = os.path.join(outputFolder, filename[:-4]+'txt')
        # read in all the sentences (apparently not necessarilly whole sentences, even though it's supposed to be so):
        textParts = []
        with open(sourceFilepath, 'r') as inFile:
            for line in inFile:
                lineStripped = line.strip()
                # example:   <a size="10" name="1">[1]</a> <a href="#1" id=1>Record Intensity Hurricane Gilbert Causes Havoc In The Caribbean.</a>
                if lineStripped.startswith('<a ') and lineStripped.endswith('</a>'):
                    indexOfTextStart = lineStripped.index('<a ', 2)
                    indexOfTextStart = lineStripped.index('>', indexOfTextStart) + 1
                    text = lineStripped[indexOfTextStart:-4]
                    textParts.append(text)
        
        # do sentence segementation on the text read in from the HTML:
        doc = nlp(unicode(' '.join(textParts)))
        docSents = [sent.text for sent in doc.sents]
        # write the sentences line by line:
        with open(targetFilepath, 'w') as outFile:
            outFile.write('\n'.join(docSents))

if __name__ == '__main__':
    # CHANGE THE INPUT/OUTPUT FOLDERS ACCORDING TO YOUR NEEDS
    workFolders = [ # (input_folder, output_folder)
        # example:
        ('DUC2001/see.models', 'DUC2001/modelsTxt'),
        ('DUC2002/SEE.peer_abstracts.in.sentences', 'DUC2002/submissionsTxt')
        ]
    for inputFolder, outputFolder in workFolders:
        print('Converting folder "{}"...'.format(inputFolder))
        convert(inputFolder, outputFolder)
        print('Finished conversion of "{}" into folder "{}"'.format(inputFolder, outputFolder))
    print('Conversion complete!')