import re
import os
import shutil
import json

import PyPDF2
from quiz2test import converter
import pathlib


def save_quiz(quiz, filename):
    with open(filename, 'w', encoding="utf8") as f:
        json.dump(quiz, f)


def load_quiz(filename):
    with open(filename, 'r', encoding="utf8") as f:
        quiz = json.load(f)
    return quiz


def save_text(text, filename):
    with open(filename, 'w', encoding="utf8") as f:
        f.write(text)


def read_txt(filename):
    with open(filename, 'r', encoding="utf8") as f:
        return f.read()


def read_pdf(filename, output_dir, use_ocr, lang, dpi, psm, oem):
    text = ""
    if not use_ocr:
        with open(filename, 'rb') as f:
            pdf = PyPDF2.PdfFileReader(f)

            for p in pdf.pages:
                text += p.extractText() + "\n\n\n"
    else:
        basedir, tail = os.path.split(filename)
        fname, extension = os.path.splitext(tail)

        # Scan pages
        print("Converting PDF pages to images...")
        savepath = f"{output_dir}/scanned/{fname}"
        create_folder(savepath)
        converter.pdf2image(filename, savepath, dpi)

        # Get files to OCR, and sort them alphabetically (tricky => [page-0, page-1, page-10, page-2,...])
        scanned_files = get_files(savepath, extensions={"jpg"})
        scanned_files.sort(key=tokenize)

        # Perform OCR on the scanned pages
        orc_savepath = f"{output_dir}/ocr/{fname}"
        create_folder(orc_savepath)

        pages_txt = []
        for i, filename in enumerate(scanned_files, 1):
            print("Performing OCR {} of {}".format(i, len(scanned_files)))
            text = read_image(filename, output_dir, lang, dpi, psm, oem, subfolder=orc_savepath)
            pages_txt.append(text)
        text = "\n".join(pages_txt)
    return text


def read_image(filename, output_dir, lang, dpi, psm, oem, subfolder=None):
    basedir, tail = os.path.split(filename)
    fname, extension = os.path.splitext(tail)

    # Save path
    if not subfolder:
        subfolder = f"{output_dir}/ocr/{subfolder}"
        create_folder(subfolder)

    # Perform OCR
    converter.image2text(filename, f"{subfolder}/{fname}", lang, dpi, psm, oem)

    # Read file
    text = read_txt(filename=f"{subfolder}/{fname}.txt")
    return text


def check_input(path, extensions=None):
    # Check input path
    if not os.path.exists(path):
        raise IOError("Input path does not exists: {}".format(path))

    # Read input files
    if os.path.isfile(path):
        files = [path]
    else:
        files = get_files(path, extensions)

    # Check files
    if not files:
        raise IOError("Not files where found at: {}".format(path))

    return files


def create_folder(path, empty_folder=True):
    basedir = os.path.basename(path)

    # Check output path
    if os.path.exists(path):
        if empty_folder:
            print("Deleting '{}' folder contents...".format(basedir))
            shutil.rmtree(path)
    else:
        print("Creating directories: {}".format(path))

    # Create path, recursively
    path = pathlib.Path(path)
    path.mkdir(parents=True, exist_ok=True)


def get_files(path, extensions):
    files = []
    for filename in os.listdir(path):
        # Get extension
        fname, ext = os.path.splitext(filename)
        ext = ext.replace('.', '')  # remove dot

        # Check if the extension is valid
        if ext in extensions:
            files.append(os.path.join(path, filename))
        else:
            pass
            #print("Ignoring file: '{}'. Invalid extension".format(filename))
    return files


def get_blacklist(filename):
    if filename and os.path.exists(filename):
        with open(filename, 'r', encoding="utf8") as f:
            lines = f.read()
            words = [l.strip() for l in lines.split('\n') if l.strip()]
            return list(set(words))
    else:
        print("[WARNING] blacklist file not found")
    return []


def build_quiz(questions, correct_answers=None):
    quiz = {}

    # Add questions
    for q in questions:
        id_question, question, answers = q
        quiz[id_question] = {
            'id': id_question,
            'question': question,
            'answers': answers,
            'correct_answer': None
        }

    # Add answers
    if correct_answers:
        for ans in correct_answers:
            id_question, answer = ans
            if id_question in quiz:
                quiz[id_question]['correct_answer'] = answer
            else:
                print("[WARNING] Missing question for answer '{}'".format(id_question))
    return quiz


def tokenize(filename):
    digits = re.compile(r'(\d+)')
    return tuple(int(token) if match else token
                 for token, match in
                 ((fragment, digits.search(fragment))
                  for fragment in digits.split(filename)))


def merge_txt_files(files, savepath, overwrite=True):
    if not files:
        raise IOError("No files to merge")
    else:
        files.sort(key=tokenize)  # Sort files (tricky => [page-0, page-1, page-10, page-2,...])

        # Create new file
        with open(savepath, 'w', encoding="utf8") as f:

            # Walk through each file
            for filename in files:
                basedir, tail = os.path.split(filename)

                # Check start
                if tail.startswith("page"):

                    # Read orc file
                    with open(filename, encoding="utf8") as f_ocr:
                        f.write(f_ocr.read())
