import os
import re
import regex
import string
import json

from file2quiz import utils, converter

from io import StringIO
from bs4 import BeautifulSoup
from tika import parser as tp


def extract_text(input_dir, output_dir, use_ocr=False, lang="eng", dpi=300, psm=3, oem=3, save_files=False,
                 extensions=None):
    # Get files
    files = utils.get_files(input_dir, extensions)

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
            basedir, tail = os.path.split(filename)
            save_txt(text, os.path.join(txt_dir, f"{tail}.txt"))

    return extracted_texts


def read_file(filename, output_dir, use_ocr, lang, dpi, psm, oem):
    # Get path values
    basedir, tail = os.path.split(filename)
    fname, extension = utils.get_fname(filename)
    extension = extension.lower().strip()

    # Select method depending on the extension
    if extension in {".txt"}:
        txt_pages = [read_txt(filename)]
    elif extension in {".pdf"}:
        txt_pages = read_pdf(filename, output_dir, use_ocr, lang, dpi, psm, oem)
    elif extension in {".jpg", ".jpeg", ".jfif", ".png", ".tiff", ".bmp", ".pnm"}:
        txt_pages = read_image(filename, output_dir, lang, dpi, psm, oem, parent_dir=tail)
    elif extension in {".html", ".htm"}:
        txt_pages = read_html(filename)
    elif extension in {".doc", ".docx"}:
        txt_pages = read_docx(filename)
    elif extension in {".rtf"}:
        txt_pages = read_docx(filename)
    else:
        print(f"[WARNING] Unknown format (*{extension}). Trying with generic parser. ({tail})")
        txt_pages = _read_tika(filename)

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


def read_pdf_ocr(filename, output_dir, lang, dpi, psm, oem, img_format="tiff"):
    pages_txt = []
    basedir, tail = os.path.split(filename)

    # Scan pages
    print("Converting PDF to images...")
    savepath = f"{output_dir}/scanned/{tail}"
    utils.create_folder(savepath)
    converter.pdf2image(filename, savepath, dpi, img_format=img_format)

    # Get files to OCR, and sort them alphabetically (tricky => [page-0, page-1, page-10, page-2,...])
    scanned_files = utils.get_files(savepath, extensions={f".{img_format}"})
    scanned_files.sort(key=utils.tokenize)

    # Perform OCR on the scanned pages
    for i, filename in enumerate(scanned_files, 1):
        print("Performing OCR {} of {}".format(i, len(scanned_files)))
        text = read_image(filename, output_dir, lang, dpi, psm, oem, parent_dir=tail, empty_folder=False)
        pages_txt.append(text[0])

    return pages_txt


def read_pdf_text(filename):
    pages_txt = []

    _buffer = StringIO()
    data = tp.from_file(filename, xmlContent=True)
    xhtml_data = BeautifulSoup(data['content'], features="lxml")
    for page, content in enumerate(xhtml_data.find_all('div', attrs={'class': 'page'})):
        _buffer.write(str(content))
        parsed_content = tp.from_buffer(_buffer.getvalue())
        _buffer.truncate()
        pages_txt.append(parsed_content['content'].strip())

    return pages_txt


def read_image(filename, output_dir, lang, dpi, psm, oem, parent_dir=None, empty_folder=True):
    basedir, tail = os.path.split(filename)

    # Save path
    savepath = f"{output_dir}/ocr"
    savepath += f"/{parent_dir}" if parent_dir else ""
    utils.create_folder(savepath, empty_folder=empty_folder)  # Do not empty if it is part of a batch

    # Perform OCR
    converter.image2text(filename, f"{savepath}/{tail}.txt", lang, dpi, psm, oem)

    # Read file
    text = read_txt(filename=f"{savepath}/{tail}.txt")
    return [text]


def _read_tika(filename):
    parsed = tp.from_file(filename)
    text = parsed["content"].strip()
    return [text]


def read_html(filename):
    return _read_tika(filename)


def read_rtf(filename):
    return _read_tika(filename)


def read_docx(filename):
    return _read_tika(filename)




