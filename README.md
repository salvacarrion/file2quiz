# text2quiz

text2quiz is a text processing utility that extract multiple-choice questions from unstructured sources, among other things.

Functions:

- **file2text:** Extract text information from a variety of file formats such as PDFs, HTML, images, etc.
- **text2quiz:** Parse multiple-choice tests from unstructured sources.
- **test2anki:** Export the extracted tests into a format that Anki can read.
- **txt2text:** (not yet implemented) Correct the spelling and sentences from a broken text (post-processing step):
    - e.g.: `thiss€nctence1sbr0ken => This sentence is broken`

Formats supported: `".txt", ".pdf", ".jpg", ".jpeg", ".jfif", ".png", ".tiff", ".bmp", ".pnm", ".html", ".htm", ".doc", ".docx", ".epub"`

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


### Extract text from files

To extract the text of a file (or all the files in a directory), type:

```
quiz2test --action extract-text --input examples/raw
```

> By the default, it searches in the folder `raw/` for files to process. 


### Parsing multiple-choice tests

To parse a multiple-choice test (or all the tests in a directory), type:

```
quiz2test --action txt2quiz --input examples/txt
```

> By the default, it searches in the folder `txt/` for tests to process. 


### Export tests to Anki 

To export a multiple-choice test (or all the tests in a directory) to anki, type:

```
quiz2test --action quiz2anki --input examples/quizzes
```

> By the default, it searches in the folder `quizzes/` for tests to process. 


### Read tests (json) 

To read a test (or all the tests in a directory), type:

```
quiz2test --action read-quiz --input examples/quizzes
```

> By the default, it searches in the folder `quizzes/` for tests to process. 


## Example

Let's say we want extract the quiz from a file like the one below, and then export it to Anki.

Input file: `examples/raw/demo.pdf`:

``` text
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
c	No, that's impossible
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

First need to to extract its text by typing:

```
quiz2test --action extract-text --input examples/raw/demo.pdf --output examples/
```

Now we have the text extracted. However, what we have here is an unstructured txt file. 
To parse this txt file into a structured format like json, we type:

```
quiz2test --action txt2quiz --input examples/txt --output examples/ --token-answer "==="
```

> `--token-answer "==="` is the token used here to to split the questions and answers


This give us a *.json file that is not easy to read. If we want to see its content, we type:

```
quiz2test --action read-quiz --input examples/quizzes --output examples/
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
c) No, thats impossible
d) Yes, but only for text files

3) Can we exclude certain words or patterns?
a) Still in progress
b) You wish...
c) No, but that would be awesome!
*d) Yes, like: "" or "", ""
```

Now that we have check that our file is correct, we can convert it to anki typing:

```
quiz2test --action quiz2anki --input examples/quizzes --output examples/
```

### More options

To view all the available options, type `quiz2test` in the terminal:

```
usage: quiz2test [-h] [--action {read-quiz,extract-text,txt2quiz,quiz2anki}]
                 [--input INPUT] [--output OUTPUT] [--blacklist BLACKLIST]
                 [--token_answer TOKEN_ANSWER] [--single-line SINGLE_LINE]
                 [--show_correct SHOW_CORRECT] [--num_answers NUM_ANSWERS]
                 [--use_ocr USE_OCR] [--lang LANG] [--dpi DPI] [--psm PSM]
                 [--oem OEM]

optional arguments:
  -h, --help            show this help message and exit
  --action {read-quiz,extract-text,txt2quiz,quiz2anki}
                        Actions to perform
  --input INPUT         Input file or directory
  --output OUTPUT       Output directory
  --blacklist BLACKLIST
                        Blacklist file with the excluded words or patterns
  --token_answer TOKEN_ANSWER
                        Token used to split the file between questions and
                        answers
  --single-line SINGLE_LINE
                        Use single line to split elements
  --show_correct SHOW_CORRECT
                        Show correct answer
  --num_answers NUM_ANSWERS
                        Number of answers per question
  --use_ocr USE_OCR     Use an OCR to extract text from the PDFs
  --lang LANG           [Tesseract] Specify language(s) used for OCR
  --dpi DPI             [Tesseract] Specify DPI for input image
  --psm PSM             [Tesseract] Specify page segmentation mode
  --oem OEM             [Tesseract] Specify OCR Engine mode
```
