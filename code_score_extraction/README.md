# Create ROUGE dataset
Code for creating alignment dataset between sentences in the summary and sentences in the document.
We assume each sentence in the reference summary summarize different group of sentences from the document.
We wish to associate each summary sentence with a subset of the document sentences.
Therefore we calculate a ROUGE matrix between every summary sentence to evry document sentence.

## Code usage
usage:

createRougeDataset.py [-h] --input_doc INPUT_DOC --input_summ
                             INPUT_SUMM [--doc_sent_dir DOC_SENT_DIR]
                             [--summ_sent_dir SUMM_SENT_DIR]

arguments:
  
  **--input_doc**   document path
  
  **--input_summ**  summary path
  
  **--doc_sent_dir**    directory path where the document sentences will be saved
  
  **--summ_sent_dir**   directory path where the summary sentences will be saved
