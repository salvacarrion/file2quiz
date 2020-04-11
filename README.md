# file2quiz

![build](https://github.com/salvacarrion/file2quiz/workflows/build/badge.svg)

**file2quiz** is a text processing utility to extract multiple-choice questions from unstructured sources, among other things.


**Functions:**

- **file2text:** Extract text information from a variety of file formats such as JPEG, PNG, PDFs, DOCX, HTML, etc.
- **text2quiz:** Parse multiple-choice tests from unstructured sources into an structured json file.
- **quiz2(format):** Export json tests into a given format (text, Anki,...)
- **txt2text:** *(not yet implemented)* Fix a broken text. This post-processing step is usually needed after an OCR.
    - e.g.: `thiss€nctence1sbr0ken => This sentence is broken`


**Formats supported:**
```
".txt", ".rtf". ".doc", ".docx", ".pdf", ".html", ".htm", ".epub"`
".jpg", ".jpeg", ".jfif", ".png", ".tiff", ".bmp", ".pnm", 
```


## Requirements

- [Python 3.7+](https://www.python.org/downloads/)

To enable the OCR functionality, you also need:

On Ubuntu/Debian:

```
sudo apt install imagemagick
sudo apt install tesseract-ocr
```

On MacOS:

```
brew install imagemagick
brew install tesseract --all-languages
```


## Installation

Open the terminal, go to the folder of this package and type:

On Ubuntu/Debian/MacOS:

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
file2quiz --action extract-text --input examples/raw
```

> By the default, it searches in the folder `raw/` for files to process. 


### Parsing multiple-choice tests

To parse a multiple-choice test (or all the tests in a directory), type:

```
file2quiz --action txt2quiz --input examples/txt
```

> By the default, it searches in the folder `txt/` for tests to process. 


### Export tests to Anki 

To export a multiple-choice test (or all the tests in a directory) to anki, type:

```
file2quiz --action quiz2anki --input examples/quizzes
```

> By the default, it searches in the folder `quizzes/json` for tests to process. 


### Read tests (json) 

To read a test (or all the tests in a directory), type:

```
file2quiz --action read-quiz --input examples/quizzes
```

> By the default, it searches in the folder `quizzes/json` for tests to process. 


## Example

Let's say we want extract the quiz from a file like the one below, and then export it to Anki.

Input file: `examples/raw/demo.pdf`:

``` text
This is a demo to
show how the program works

1. Can file2quiz manage multiple-choice questions with weird formats?
a. Yes! That's its purpose!
B) no, it can't
c	it depends...
D- who knows????


2) Can file2quiz deal with
broken lines
?
a. Maybe...
b)) Yes, but
      the format "[letter] [symbol] [sentence]"

  is required

c --- No, that's impossible
d ]] Yes, but only for text files

3.- Can we exclude certain words or patterns?
a - Still in progress
b )   You wish...
c . No, but that would be awesome!
d.-Yes, like: "WORD1TODELETE" or "pattern1", "pattern123"



===
Solutions:
(1. A)
2 - b    3: d
```

First need to to extract its text by typing:

```
file2quiz --action file2text --input raw/demo.pdf --output .
```

> We're execute these commands inside the `examples/` folder

Now we have the text extracted. However, what we have here is an unstructured txt file. 
To parse this txt file into a structured format like json, we type:

```
file2quiz --action text2quiz --token-answer "==="
```

> `--token-answer "==="` is the token used here to to split the questions and answers, and it's case insensitive.
> OCRs work better with letters that symbols, so if you're processing an image, we recommend you to use a 
> word as token (e.g.: `--token-answer "soluciones"`)


This gave us a json file. If we want read its content, have to convert it to a text file

```
file2quiz --action quiz2text --show-answers
```

Output:

```
1. Can file2quiz manage multiple-choice questions with weird formats?
*a) Yes! That's its purpose!
b) no, it can't
c) it depends...
d) who knows????

2. Can file2quiz deal with broken lines ?
a) Maybe...
*b) Yes, but the format "[letter] [symbol] [sentence]" is required
c) No, that's impossible
d) Yes, but only for text files

3. Can we exclude certain words or patterns?
a) Still in progress
b) You wish...
c) No, but that would be awesome!
*d) Yes, like: "" or "", ""
```

Now that we have check that our file is correct, we can convert it to anki typing:

```
file2quiz --action quiz2anki
```

### More options

To view all the available options, type `file2quiz` in the terminal:

```
usage: file2quiz [-h] [--action {quiz2anki,text2quiz,quiz2text,file2text}]
                 [--input INPUT] [--output OUTPUT] [--blacklist BLACKLIST]
                 [--token-answer TOKEN_ANSWER] [--single-line SINGLE_LINE]
                 [--show-answers] [--num-answers NUM_ANSWERS]
                 [--use-ocr USE_OCR] [--lang LANG] [--dpi DPI] [--psm PSM]
                 [--oem OEM]

optional arguments:
  -h, --help            show this help message and exit
  --action {quiz2anki,text2quiz,quiz2text,file2text}
                        Actions to perform
  --input INPUT         Input file or directory
  --output OUTPUT       Output file or directory
  --blacklist BLACKLIST
                        Blacklist file with the excluded words or patterns
  --token-answer TOKEN_ANSWER
                        Token used to split the file between questions and
                        answers
  --single-line SINGLE_LINE
                        Use single line to split elements
  --show-answers        Show correct answer
  --num-answers NUM_ANSWERS
                        Number of answers per question
  --use-ocr USE_OCR     Use an OCR to extract text from the PDFs
  --lang LANG           [Tesseract] Specify language(s) used for OCR
  --dpi DPI             [Tesseract] Specify DPI for input image
  --psm PSM             [Tesseract] Specify page segmentation mode
  --oem OEM             [Tesseract] Specify OCR Engine mode
```
