# file2quiz

![build](https://github.com/salvacarrion/file2quiz/workflows/build/badge.svg)

**file2quiz** is a text processing utility to extract multiple-choice questions from unstructured sources, among other things.


**Functions:**

- **file2text:** Extract text information from a variety of file formats such as JPEG, PNG, PDFs, DOCX, HTML, etc.
- **fil2quiz, text2quiz:** Parse multiple-choice tests from unstructured sources into an structured json file.
- **quiz2text, quiz2anki:** Export json tests into a given format (text, Anki,...)
- **txt2text:** *(not yet implemented)* Fix a broken text. This post-processing step is usually needed after an OCR.
    - e.g.: `thiss€nctence1sbr0ken => This sentence is broken`


**Formats supported:**
```
".txt", ".rtf". ".doc", ".docx", ".pdf", ".html", ".htm", ".epub"`
".jpg", ".jpeg", ".jfif", ".png", ".tiff", ".bmp", ".pnm",...
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

To run these examples, go to the `examples/` folder from the source.


### Parsing multiple-choice tests

To parse a multiple-choice test (or all the tests in a directory), type:

```
# Option 1: (all supported formats)
file2quiz --action file2quiz --input raw/ --token-answer "^(===|solutions:)"

# Option 2: (only *.txt)
file2quiz --action text2quiz --input txt/ --token-answer "==="
```

> It is quite convenient to make use of these flags: `--save-txt --show-answers` to also save 
> the txt version of and show the correct answer.
> To exclude certain words or patterns from the processing, you can use a text file containing one expression per line. 
> (It supports regular expressions; check `examples/blacklist.txt)


### Export tests

To export a multiple-choice test (or all the tests in a directory), type:

```
# Export to txt:
file2quiz --action quiz2text --input quizzes/json/

# Export to Anki:
file2quiz --action quiz2anki --input quizzes/json/
```

> By the default, it searches in the folder `quizzes/json/` for tests to process. 


### Extract text from files

To extract the text of a file (or all the files in a directory), type:

```
file2quiz --action file2text --input raw/
```

> By the default, it searches in the folder `raw/` for files to process. 


## Example

Let's say we want extract the quiz from a file like the one below, and then export it to Anki.

Input file: `examples/raw/demo.pdf`:

``` text
This is a demo to
show how the program works

1. Can file2quiz manage multiple-choice questions with weird formats?
a. Yes! That's its purpose!
B) no, it can't
c --- -1 negative number...
D- who knows????


2) Can file2quiz deal with
broken lines in
2020?
a. Maybe...
b)) Yes, but
      the format "[letter] [symbol] [sentence]"

  is required

c --- No, that's impossible
d ]] Yes, but only for text files

3.1- Can we exclude certain words or patterns?
3a - Still in progress
3.2b )   You wish...
3.3c . No, but that would be awesome!
3.4d.-Yes, like: "WORD1TODELETE" or "pattern1", "pattern123"
```

First need to to extract its text by typing:

```
file2quiz --action file2text --input raw/demo.pdf --output .
```

> You can parse the quiz directly using this options: `--action file2quiz`


Now we have the text extracted. However, what we have here is an unstructured txt file. 
To parse this txt file into a structured format like json, we type:

```
file2quiz --action text2quiz --token-answer "^(===|solutions:)"
```

> `--token-answer` is the token used here to to split the questions and answers, and it's case insensitive.
> OCRs work better with letters that symbols, so if you're processing an image, we recommend you to use a 
> word as token (e.g.: `--token-answer "solutions"`)


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

To view all the available options, type `file2quiz --help` in the terminal:

```
usage: file2quiz [-h]
                 [--action {file2quiz,file2text,text2quiz,quiz2text,quiz2anki}]
                 [--input INPUT] [--output OUTPUT] [--mode {auto,single-line}]
                 [--blacklist BLACKLIST] [--token-answer TOKEN_ANSWER]
                 [--show-answers]
                 [--fill-missing-answers FILL_MISSING_ANSWERS]
                 [--num-answers NUM_ANSWERS] [--save-txt] [--use-ocr USE_OCR]
                 [--lang LANG] [--dpi DPI] [--psm PSM] [--oem OEM]

optional arguments:
  -h, --help            show this help message and exit
  --action {file2quiz,file2text,text2quiz,quiz2text,quiz2anki}
                        Actions to perform
  --input INPUT         Input file or directory
  --output OUTPUT       Output file or directory
  --mode {auto,single-line}
                        Mode used to detect questions
  --blacklist BLACKLIST
                        Blacklist file with the excluded words or patterns
                        (regex)
  --token-answer TOKEN_ANSWER
                        (regex) Token used to split the file between questions
                        and answers
  --show-answers        Show correct answer
  --fill-missing-answers FILL_MISSING_ANSWERS
                        Texto used to fill missing answers
  --num-answers NUM_ANSWERS
                        Number of answers per question
  --save-txt            Save quizzes in txt
  --use-ocr USE_OCR     Use an OCR to extract text from the PDFs
  --lang LANG           [Tesseract] Specify language(s) used for OCR
  --dpi DPI             [Tesseract] Specify DPI for input image
  --psm PSM             [Tesseract] Specify page segmentation mode
  --oem OEM             [Tesseract] Specify OCR Engine mode
```
