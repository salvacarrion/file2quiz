# Quiz2Test

Quiz2Test allows you to extract multiple choice questions from unstructured sources (txt, pdfs and images) and 
save them using a structured format (json, anki)


## Requirements

- [Python 3.7+](https://www.python.org/downloads/)

To enable the OCR functionality, you also need:

- [ImageMagick](https://imagemagick.org/)
- [Tesseract](https://tesseract-ocr.github.io/)


## Installation

Open the terminal, go to the folder of this package and type:

On Ubuntu/Debian/Mac OS:

```
python3 setup.py install --user
```

On Windows:

```
py setup.py install --user
```


## Usage

By the default, quiz2test searches in the folder `raw/` for files to parse. Then, it saves the quizzes at `quizzes`.

> There might be additional folders created depending of the actions (scanned, ocr, etc)


### Parse files

To parse a file (or all the files in a directory), type:

```
quiz2test --action parse --input examples/raw --token "==="
```

Input file (`examples/raw/demo.txt`):

```
This is a demo in order to
show how the program works

1. Can quiz2test manage multiple choice questions with weird formats?
a. Yes! That's its purpose!
B) no, it can't
c	it depends...
D- who knows????


2. Can quiz2test deal with
broken lines
?
a. Maybe...
b) Yes, but format the "letter [symbol]
sentence is required
c	No, that's imposible
d) Yes, but only for text files

3. Can we exclude certain words or patterns?
a) Still in progress
b) You wish...
c) No, but that would be awesome!
d) Yes, like: "WORD1TODELETE" or "pattern1", "pattern123"



===
Solutions:
1. A
2 - b
3: d
```


### Read output

To read a json file (or all the json files in a directory), type:

```
quiz2test --action read --input examples/parsed
```

Output:

```
===========================================
Quiz #1: demo
===========================================

1) Can quiz2test manage multiple choice questions with weird formats?
*a) Yes! Thats its purpose!
b) no, it cant
c) it depends...
d) who knows????

2) Can quiz2test deal with broken lines ?
a) Maybe...
*b) Yes, but format the "letter [symbol] sentence is required
c) No, thats imposible
d) Yes, but only for text files

3) Can we exclude certain words or patterns?
a) Still in progress
b) You wish...
c) No, but that would be awesome!
*d) Yes, like: "" or "", ""
```

### More options

To view all the available options, type `quiz2test` in the terminal:

```
usage: quiz2test [-h] [-a {parse,read,convert2anki}] [-i INPUT] [-o OUTPUT]
                 [-t TOKEN] [-s] [-b BLACKLIST] [--single_line]
                 [--num_answers NUM_ANSWERS] [--use_ocr] [--lang LANG]
                 [--dpi DPI] [--psm PSM] [--oem OEM]

optional arguments:
  -h, --help            show this help message and exit
  -a {parse,read,convert2anki}, --action {parse,read,convert2anki}
                        shows output
  -i INPUT, --input INPUT
                        File or folder to search for the raw documents
  -o OUTPUT, --output OUTPUT
                        Folder to save the output
  -t TOKEN, --token TOKEN
                        Token used to split questions and answers
  -s, --show_correct    Show correct answer
  -b BLACKLIST, --blacklist BLACKLIST
                        Blacklist file with the excluded words or patterns
  --single_line         Use single line to split elements
  --num_answers NUM_ANSWERS
                        Number of answers per question
  --use_ocr             Use an OCR (tesseract) to extract the text from the
                        PDF
  --lang LANG           [Tesseract] Specify language(s) used for OCR
  --dpi DPI             [Tesseract] Specify DPI for input image
  --psm PSM             [Tesseract] Specify page segmentation mode
  --oem OEM             [Tesseract] Specify OCR Engine mode
```
