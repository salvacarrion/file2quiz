import os
import re
import regex
import string
import json

import PyPDF2

from quiz2test import utils, converter


def extract_text(input_dir, output_dir, use_ocr, lang, dpi, psm, oem, save_files=False):
    # Get files
    files = utils.get_files(input_dir)

    # Create output dir
    txt_dir = os.path.join(output_dir, "txt")
    utils.create_folder(txt_dir) if save_files else None

    # Extract text
    extracted_texts = []  # list of tuples (text, filename)
    for i, filename in enumerate(files, 1):
        # Read file
        txt_pages = read_file(filename, output_dir, use_ocr, lang, dpi, psm, oem)
        extracted_texts.append(("\n".join(txt_pages), filename))

    # Save extracted texts
    if save_files:
        for i, (text, filename) in enumerate(extracted_texts):
            fname, ext = utils.get_fname(filename)
            save_txt(text, os.path.join(txt_dir, f"{fname}.txt"))

    return extracted_texts


def read_file(filename, output_dir, use_ocr, lang, dpi, psm, oem):
    # Get path values
    fname, extension = utils.get_fname(filename)

    # Select method depending on the extension
    if extension in {".txt"}:
        txt_pages = [read_txt(filename)]
    elif extension in {".pdf"}:
        txt_pages = read_pdf(filename, output_dir, use_ocr, lang, dpi, psm, oem)
    elif extension in {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}:
        txt_pages = read_image(filename, output_dir, lang, dpi, psm, oem, parent_dir=fname)
    else:
        raise IOError("Invalid file extension")

    return txt_pages  # Must be a list of string


def read_txt(filename):
    with open(filename, 'r', encoding="utf8") as f:
        return f.read()


def save_txt(text, filename):
    with open(filename, 'w', encoding="utf8") as f:
        f.write(text)


def read_json(filename):
    with open(filename, 'r', encoding="utf8") as f:
        return json.load(f)


def save_json(quiz, filename):
    with open(filename, 'w', encoding="utf8") as f:
        json.dump(quiz, f)


def read_pdf(filename, output_dir, use_ocr, lang, dpi, psm, oem):
    if use_ocr:
        return read_pdf_ocr(filename, output_dir, lang, dpi, psm, oem)
    else:
        return read_pdf_text(filename)


def read_pdf_ocr(filename, output_dir, lang, dpi, psm, oem):
    pages_txt = []
    fname, ext = utils.get_fname(filename)

    # Scan pages
    print("Converting PDF to images...")
    savepath = f"{output_dir}/scanned/{fname}"
    utils.create_folder(savepath)
    converter.pdf2image(filename, savepath, dpi)

    # Get files to OCR, and sort them alphabetically (tricky => [page-0, page-1, page-10, page-2,...])
    scanned_files = utils.get_files(savepath, extensions={".jpg"})
    scanned_files.sort(key=utils.tokenize)

    # Perform OCR on the scanned pages
    for i, filename in enumerate(scanned_files, 1):
        print("Performing OCR {} of {}".format(i, len(scanned_files)))
        text = read_image(filename, output_dir, lang, dpi, psm, oem, parent_dir=fname, empty_folder=False)
        pages_txt.append(text[0])

    return pages_txt


def read_pdf_text(filename):
    pages_txt = []

    # Extract selectable text from the PDF
    with open(filename, 'rb') as f:
        pdf = PyPDF2.PdfFileReader(f)

        # Read pages
        for p in pdf.pages:
            text = p.extractText()
            pages_txt.append(text)
    return pages_txt


def read_image(filename, output_dir, lang, dpi, psm, oem, parent_dir=None, empty_folder=True):
    fname, extension = utils.get_fname(filename)

    # Save path
    savepath = f"{output_dir}/ocr"
    savepath += f"/{parent_dir}" if parent_dir else ""
    utils.create_folder(savepath, empty_folder=empty_folder)  # Do not empty if it is part of a batch

    # Perform OCR
    converter.image2text(filename, f"{savepath}/{fname}.txt", lang, dpi, psm, oem)

    # Read file
    text = read_txt(filename=f"{savepath}/{fname}.txt")
    return [text]


