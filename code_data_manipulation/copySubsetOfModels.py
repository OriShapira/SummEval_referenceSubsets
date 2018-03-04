'''
This script copies a subset of model summaries from one folder to another.
It can either copy a single model per length, or a single model per author (per task).
Change the MODELS_FOLDER_PATH, MODELS_FOLDER_PATH_DEST and SUBSET_TYPE variables according to your needs.

Run: python copySubsetOfModels.python
Outputs: new folder with the copied models
'''
import os
from random import shuffle
import shutil

# The input and output folders - CHANGE ACCORDING TO YOUR NEEDS:
MODELS_FOLDER_PATH = 'DUC2001/see.models'
MODELS_FOLDER_PATH_DEST = 'DUC2001/see.models.oneperlen'

# the types of subsets per task:
ONE_PER_AUTHOR = 1
ONE_PER_LENGTH = 2

# The subset type to use - CHANGE ACCORDING TO YOUR NEEDS:
SUBSET_TYPE = ONE_PER_AUTHOR




# list of authors in each task (i.e. the fifth part of the filename in e.g. D04.M.100.A.F.html):
authorsInTasks = {}
# the lengths available:
lengths = []
# the author vairants in each task (i.e. the fourth part of the filename in e.g. D04.M.100.A.F.html)
# this is kept just in order to build the filenames back:
authorVariablePerTask = {}
# get the authors and lengths avaialable:
for ind, filename in enumerate(os.listdir(MODELS_FOLDER_PATH)):
    parts = filename.split('.')
    if len(parts) == 6:
        taskname = parts[0]
        if taskname not in authorsInTasks:
            authorsInTasks[taskname] = []
        author = parts[4]
        if author not in authorsInTasks[taskname]:
            authorsInTasks[taskname].append(author)
        length = parts[2]
        if not length in lengths:
            lengths.append(length)
        authorVariable = parts[3]
        authorVariablePerTask[taskname] = authorVariable
        
for task in authorsInTasks:
    # radomize the order of the authors and lengths:
    shuffle(authorsInTasks[task])
    shuffle(lengths)
    numAuthors = len(authorsInTasks[task])
    
    # copy the files:
    if SUBSET_TYPE == ONE_PER_AUTHOR:
        # This section is for getting the same number of lengths as authors (random length per author)
        for i in range(numAuthors):
            filenameToCopy = '{}.M.{}.{}.{}.html'.format(task, lengths[i], authorVariablePerTask[task], authorsInTasks[task][i])
            filepathToCopyFrom = os.path.join(MODELS_FOLDER_PATH, filenameToCopy)
            filepathToCopyTo = os.path.join(MODELS_FOLDER_PATH_DEST, filenameToCopy)
            shutil.copyfile(filepathToCopyFrom, filepathToCopyTo)
    elif SUBSET_TYPE == ONE_PER_LENGTH:
        # This section is for getting the one summary per length, each with a random author
        for i in range(len(lengths)):
            filenameToCopy = '{}.M.{}.{}.{}.html'.format(task, lengths[i], authorVariablePerTask[task], authorsInTasks[task][i%numAuthors])
            filepathToCopyFrom = os.path.join(MODELS_FOLDER_PATH, filenameToCopy)
            filepathToCopyTo = os.path.join(MODELS_FOLDER_PATH_DEST, filenameToCopy)
            shutil.copyfile(filepathToCopyFrom, filepathToCopyTo)