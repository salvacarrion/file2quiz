import os
import re
import regex
import string
import json

from file2quiz import utils, converter, reader

from io import StringIO
from bs4 import BeautifulSoup
from tika import parser as tp


def extract_text(input_dir, output_dir, blacklist_path=None, use_ocr=False, lang="eng", dpi=300, psm=3, oem=3, save_files=False,
                 extensions=None):
    print(f'##############################################################')
    print(f'### TEXT EXTRACTION')
    print(f'##############################################################\n')

    # Get files
    files = utils.get_files(input_dir, extensions)

    # Get blacklist
    blacklist = reader.read_blacklist(blacklist_path)

    # Create output dir
    txt_dir = os.path.join(output_dir, "txt")
    utils.create_folder(txt_dir) if save_files else None

    # Extract text
    extracted_texts = []  # list of tuples (text, filename)
    for i, filename in enumerate(files, 1):
        tail, basedir = utils.get_tail(filename)
        print("")
        print(f'==============================================================')
        print(f'[INFO] ({i}/{len(files)}) Extracting text from: "{tail}"')
        print(f'==============================================================')

        # Read file
        txt_pages = read_file(filename, output_dir, use_ocr, lang, dpi, psm, oem)
        text = "\n".join(txt_pages)

        # Remove blacklisted words
        text = utils.replace_words(text, blacklist, replace="")

        # Add extracted texts
        extracted_texts.append((text, filename))

        # Show info
        if not text.strip():
            print(f"\t- [WARNING] No text was found ({tail})")
        print(f"\t- [INFO] Extracting done! ({tail})")

        # Save extracted texts
        if save_files:
            print(f"\t- [INFO] Saving file... ({tail}.txt)")
            save_txt(text, os.path.join(txt_dir, f"{tail}.txt"))

    print("")
    print("--------------------------------------------------------------")
    print("SUMMARY")
    print("--------------------------------------------------------------")
    print(f"- [INFO] Documents analyzed: {len(extracted_texts)}")
    print("--------------------------------------------------------------\n\n")
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
        print(f"\t- [WARNING] Unknown format (*{extension}). Trying with generic parser. ({tail})")
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


def read_pdf(filename, output_dir, use_ocr, lang, dpi, psm, oem):
    if use_ocr:
        return read_pdf_ocr(filename, output_dir, lang, dpi, psm, oem)
    else:
        return read_pdf_text(filename)


def read_pdf_ocr(filename, output_dir, lang, dpi, psm, oem, img_format="tiff"):
    pages_txt = []
    basedir, tail = os.path.split(filename)

    # Scan pages
    savepath = f"{output_dir}/scanned/{tail}"
    utils.create_folder(savepath)
    print("\t- [INFO] Converting PDF to images...")
    converter.pdf2image(filename, savepath, dpi, img_format=img_format)

    # Get files to OCR, and sort them alphabetically (tricky => [page-0, page-1, page-10, page-2,...])
    scanned_files = utils.get_files(savepath, extensions={f".{img_format}"})
    scanned_files.sort(key=utils.tokenize)

    # Perform OCR on the scanned pages
    for i, filename in enumerate(scanned_files, 1):
        print("\t- [INFO] Performing OCR {} of {}".format(i, len(scanned_files)))
        text = read_image(filename, output_dir, lang, dpi, psm, oem, parent_dir=tail, empty_folder=False)
        pages_txt.append(text[0])

    return pages_txt


def read_pdf_text(filename):
    pages_txt = []

    # Read PDF file
    data = tp.from_file(filename, xmlContent=True)
    xhtml_data = BeautifulSoup(data['content'], features='lxml')
    for i, content in enumerate(xhtml_data.find_all('div', attrs={'class': 'page'})):
        # Parse PDF data using TIKA (xml/html)
        # It's faster and safer to create a new buffer than truncating it
        # https://stackoverflow.com/questions/4330812/how-do-i-clear-a-stringio-object
        _buffer = StringIO()
        _buffer.write(str(content))
        parsed_content = tp.from_buffer(_buffer.getvalue())

        # Add pages
        tmp = parsed_content.get("content", None)  # Sometimes content exists but is None
        text = tmp.strip() if tmp else ""
        pages_txt.append(text)

    return pages_txt


def _read_tika(filename, *args, **kargs):
    parsed = tp.from_file(filename)
    text = parsed["content"].strip()
    return [text]


def read_html(filename):
    return _read_tika(filename)


def read_rtf(filename):
    return _read_tika(filename)


def read_docx(filename):
    return _read_tika(filename)


def read_blacklist(path):
    # Get blacklist
    if path and os.path.isfile(path):
        blacklist = read_txt(path)
        blacklist = list(set([l.strip() for l in blacklist.split("\n") if l.strip()]))
        print("\t- [INFO] Using blacklist file. (Regex knowledge is required).")
    else:
        blacklist = []
    return blacklist
