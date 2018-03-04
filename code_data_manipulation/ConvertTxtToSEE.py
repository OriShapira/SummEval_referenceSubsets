'''
This script reads in txt files and outputs it in SEE format to new files (htmls).
Keeps same file names.
Change the INPUT_FOLDER and OUTPUT_FOLDER variable for your needs.

Run: python ConvertTxt2SEE.py
'''

from pyrouge.utils.file_utils import DirectoryProcessor


INPUT_FOLDER = ''
OUTPUT_FOLDER = ''


def convert_summaries_to_rouge_format(input_dir, output_dir):
    DirectoryProcessor.process(input_dir, output_dir, convert_text_to_rouge_format)

def convert_text_to_rouge_format(text, title="dummy title"):
    """
    Convert a text to a format ROUGE understands. The text is
    assumed to contain one sentence per line.

        text:   The text to convert, containg one sentence per line.
        title:  Optional title for the text. The title will appear
                in the converted file, but doesn't seem to have
                any other relevance.

    Returns: The converted text as string.

    """
    sentences = text.split("\n")
    sent_elems = [
        "<a name=\"{i}\">[{i}]</a> <a href=\"#{i}\" id={i}>"
        "{text}</a>".format(i=i, text=sent)
        for i, sent in enumerate(sentences, start=1) if sent != '']
    html = """<html>
<head>
<title>{title}</title>
</head>
<body bgcolor="white">
{elems}
</body>
</html>""".format(title=title, elems="\n".join(sent_elems))

    return html
    

convert_summaries_to_rouge_format(INPUT_FOLDER, OUTPUT_FOLDER)