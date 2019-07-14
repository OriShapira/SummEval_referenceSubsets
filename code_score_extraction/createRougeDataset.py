import os
import argparse
from nltk.tokenize import sent_tokenize
import calculateRouge
import numpy as np
import time

from spacy.lang.en import English

def split_sentences(raw_text):
    nlp = English()
    nlp.add_pipe(nlp.create_pipe('sentencizer'))
    doc = nlp(unicode(raw_text))
    sentences = [sent.string.strip() for sent in doc.sents]
    return sentences

def doc_sentences_extract(input_doc, doc_sent_dir):
    with open(input_doc,'r') as f:
        doc = f.read()
    sentences = split_sentences(doc)#sent_tokenize(doc)

    if not os.path.exists(doc_sent_dir):
        os.makedirs(doc_sent_dir)
    for sent_idx, sentence in enumerate(sentences):
        html_path = os.path.join(doc_sent_dir, 'D061.M.250.J.' + str(sent_idx)+'.html')
        with open(html_path, 'w') as f:
            f.write(sentence)

    return len(sentences)

def summ_sentences_extract(input_summ, summ_sent_dir):
    with open(input_summ,'r') as f:
        summ = f.read()
    sentences = split_sentences(summ)#sent_tokenize(summ)
    for sent_idx, sentence in enumerate(sentences):
        sent_dir = os.path.join(summ_sent_dir, str(sent_idx))
        if not os.path.exists(sent_dir):
            os.makedirs(sent_dir)
        html_path = os.path.join(sent_dir, 'D061.M.250.J.A' + '.html')
        with open(html_path, 'w') as f:
            f.write(sentence)
    return len(sentences)



def extractRouge(analyzedData, systemNames, summaryLengths):
    '''
    Outputs the analyzedData to a CSV file with the format:
    ROUGE_type,<summLen1>_r,<summLen2>_r,<summLenK>_r,<summLen1>_p,<summLen2>_p,<summLenK>_p,<summLen1>_f,<summLen2>_f,<summLenK>_f
    where each line is a rougeType, and systems are divided into sections.
    '''
    # with open(outputFilepath, 'w') as outF:
    #     # header line
    #     # example: ROUGE_type,050_r,100_r,200_r,400_r,050_p,100_p,200_p,400_p,050_f,100_f,200_f,400_f
    #     firstLineParts = ['ROUGE_type']
    #     firstLineParts.extend(
    #         ['{}_{}'.format(summLen, measure_type) for measure_type in ['r', 'p', 'f'] for summLen in summaryLengths])
    #     firstLine = ','.join(firstLineParts)
    #     outF.write(firstLine + '\n\n')
    #
    #     # the csv is divided into section for each system:
    #     for sysName in systemNames:
    #         outF.write(sysName + '\n')

    rouge_vec = np.zeros((len(systemNames)))
    for sysName in systemNames:
        if sysName in analyzedData:
            summLen = summaryLengths[0]  # we should get here only 1 summary length

            # the rest of the line is for the columns <sys_len>.<r/p/f>, if there's no value, then 0:
            mean_rouge = np.mean([analyzedData[sysName][summLen][rougeType]['recall'] \
                                      if analyzedData[sysName][summLen][rougeType]['recall'] != -1 \
                                      else 0 \
                                  for rougeType in ['R1', 'R2', 'RL']])

            rouge_vec[int(sysName)] = mean_rouge

    return rouge_vec




parser = argparse.ArgumentParser()

## Required parameters
parser.add_argument("--input_doc", default=None, type=str, required=True)
parser.add_argument("--input_summ", default=None, type=str, required=True)
parser.add_argument("--doc_sent_dir", default=r'C:\Users\user\Documents\Phd\rouge\SummEval_referenceSubsets\code_score_extraction\doc_sentences', type=str)
parser.add_argument("--summ_sent_dir", default=r'C:\Users\user\Documents\Phd\rouge\SummEval_referenceSubsets\code_score_extraction\summ_sentences', type=str)

# parser.add_argument("--bert_model", default=None, type=str, required=True,
#                         help="Bert pre-trained model selected in the list: bert-base-uncased, "
#                              "bert-large-uncased, bert-base-cased, bert-base-multilingual, bert-base-chinese.")
#
#     ## Other parameters
# parser.add_argument("--do_lower_case", action='store_true', help="Set this flag if you are using an uncased model.")
# parser.add_argument("--layers", default="-1,-2,-3,-4", type=str)
# parser.add_argument("--max_seq_length", default=128, type=int,
#                         help="The maximum total input sequence length after WordPiece tokenization. Sequences longer "
#                             "than this will be truncated, and sequences shorter than this will be padded.")
# parser.add_argument("--batch_size", default=32, type=int, help="Batch size for predictions.")
# parser.add_argument("--local_rank",
#                         type=int,
#                         default=-1,
#                         help = "local_rank for distributed training on gpus")
# parser.add_argument("--no_cuda",
#                         action='store_true',
#                         help="Whether not to use CUDA when available")

args = parser.parse_args()

num_doc_sent = doc_sentences_extract(args.input_doc, args.doc_sent_dir)
num_summ_sent = summ_sentences_extract(args.input_summ, args.summ_sent_dir)

rouge_mat = np.zeros((num_doc_sent,num_summ_sent))


for summ_sent_idx, summ_dir in enumerate(os.listdir(args.summ_sent_dir)):
    INPUTS = [(calculateRouge.COMPARE_SAME_LEN, os.path.join(args.summ_sent_dir,summ_dir),args.doc_sent_dir, None, None, calculateRouge.LEAVE_STOP_WORDS)]
    startTime = time.time()
    # Go over each input:
    compareType, refFolder, sysFolder, outputPath, ducVersion, stopWordsRemoval = INPUTS[0]
    print('---- NEXT INPUT')
    # get the different options:
    taskNames, systemNames, summaryLengths = calculateRouge.getComparisonOptions(sysFolder, refFolder)
    # get ROUGE scores:
    allData = calculateRouge.runRougeCombinations(compareType, sysFolder, refFolder, systemNames, summaryLengths,
                                                  ducVersion, stopWordsRemoval)
    # output scores to CSV:
    # calculateRouge.outputToCsv(allData, r'C:\Users\user\Documents\Phd\rouge\SummEval_referenceSubsets\code_score_extraction\try.csv', systemNames, summaryLengths)
    rouge_vec = extractRouge(allData, systemNames, summaryLengths)
    rouge_mat[:, summ_sent_idx] = rouge_vec
    curTime = time.time()
    print('Current input done! Elapsed time: {} seconds!'.format(curTime - startTime))
print('---- DONE WITH ALL INPUTS')


