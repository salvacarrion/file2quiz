import os
import json

from file2quiz import utils, converter

from io import StringIO
from bs4 import BeautifulSoup
from tika import parser as tp
from file2quiz import preprocess


def extract_text(input_dir, output_dir, save_files=False, extensions=None, *args, **kwargs):
    print(f'##############################################################')
    print(f'### TEXT EXTRACTION')
    print(f'##############################################################\n')

    # Get files
    files = utils.get_files(input_dir, extensions)

    # Get blacklist
    blacklist = read_blacklist(os.path.join(output_dir, "blacklist.txt"))

    # Create output dir
    txt_dir = os.path.join(output_dir, "txt")
    utils.create_folder(txt_dir, empty_folder=True) if save_files else None

    # Create output dir (selector)
    txt_selector_dir = os.path.join(output_dir, "txt_selector")
    utils.create_folder(txt_selector_dir, empty_folder=True) if save_files and kwargs.get("extract_style") else None

    # Extract text
    extracted_texts = []  # list of tuples (text, filename)
    for i, filename in enumerate(files, 1):
        tail, basedir = utils.get_tail(filename)
        print("")
        print(f'==============================================================')
        print(f'[INFO] ({i}/{len(files)}) Extracting text from: "{tail}"')
        print(f'==============================================================')

        # Read file
        text, text_selected = read_file(filename, output_dir, *args, **kwargs)

        # Remove blacklisted words
        text = utils.replace_words(text, blacklist, replace="")

        # Add extracted texts
        extracted_texts.append((text, text_selected, filename))

        # Show info
        if not text.strip():
            print(f"\t- [WARNING] No text was found ({tail})")
        print(f"\t- [INFO] Extracting done! ({tail})")

        # Save extracted texts
        if save_files:
            print(f"\t- [INFO] Saving file... ({tail}.txt)")
            save_txt(text, os.path.join(txt_dir, f"{tail}.txt"))

            if kwargs.get("extract_style") and text_selected:
                save_txt(text_selected, os.path.join(txt_selector_dir, f"{tail}_selected.txt"))

    print("")
    print("--------------------------------------------------------------")
    print("SUMMARY")
    print("--------------------------------------------------------------")
    print(f"- [INFO] Documents analyzed: {len(extracted_texts)}")
    print("--------------------------------------------------------------\n\n")
    return extracted_texts


def read_file(filename, output_dir, *args, **kwargs):
    text, text_selected = None, None

    # Get path values
    basedir, tail = os.path.split(filename)
    fname, extension = utils.get_fname(filename)
    extension = extension.lower().strip()

    # Select method depending on the extension
    if extension in {".txt"}:
        text = read_txt(filename)
    elif extension in {".pdf"}:
        txt_pages = read_pdf(filename, output_dir, **kwargs)
        text = "\n\n".join(txt_pages)
    elif extension in {".jpg", ".jpeg", ".jfif", ".png", ".tiff", ".bmp", ".pnm"}:
        text = read_image(filename, output_dir, parent_dir=tail, **kwargs)
    elif extension in {".html", ".htm"}:
        text, text_selected = read_html(filename, extract_style=kwargs.get("extract_style"))
    elif extension in {".doc", ".docx"}:
        text, text_selected = read_docx(filename, extract_style=kwargs.get("extract_style"))
    elif extension in {".rtf"}:
        text = _read_tika(filename)
    else:
        print(f"\t- [WARNING] Unknown format (*{extension}). Trying with generic parser. ({tail})")
        text = _read_tika(filename)

    return text, text_selected  # Must be a list of string


def read_txt(filename, **kwargs):
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


def read_quiz(filename):
    return read_json(filename)


def save_quiz(quiz, filename):
    return save_json(quiz, filename)


def read_image(filename, output_dir, parent_dir=None, empty_folder=False, no_preprocess=False, **kwargs):
    basedir, tail = os.path.split(filename)

    # Create OCR folder
    ocr_savepath = f"{output_dir}/ocr/txt"
    ocr_savepath += f"/{parent_dir}" if parent_dir else ""
    utils.create_folder(ocr_savepath, empty_folder=empty_folder)  # Do not empty if it is part of a batch

    # Perform OCR
    converter.image2text(filename, f"{ocr_savepath}/{tail}.txt", **kwargs)

    # Read file
    text = read_txt(filename=f"{ocr_savepath}/{tail}.txt")
    return text


def read_pdf(filename, output_dir, use_ocr=False, min_char=200, **kwargs):
    if use_ocr:
        if kwargs.get("lang") is None:
            raise ValueError("A language is required to perform the OCR")
        return read_pdf_ocr(filename, output_dir, **kwargs)
    else:
        pages = read_pdf_text(filename, **kwargs)
        # Check number of characters
        total_chars = sum([len(p.strip()) for p in pages if isinstance(p, str)])
        if total_chars < min_char:
            print(f"\t- [WARNING] Too few characters ({total_chars}) were detected on the PDF. "
                  f"An OCR probably needed to extract the text from this file.")
        return pages


def read_pdf_ocr(filename, output_dir, **kwargs):
    pages_txt = []
    basedir, tail = os.path.split(filename)

    # Scan pages
    savepath = f"{output_dir}/ocr/scanned/{tail}"
    if os.path.exists(savepath):
        print("\t- [INFO] Skipping scanning. The folder already exists.")
    else:
        utils.create_folder(savepath, empty_folder=True)
        print("\t- [INFO] Converting PDF to images...")
        converter.pdf2image(filename, savepath, **kwargs)

    # Get files to OCR, and sort them alphabetically (tricky => [page-0, page-1, page-10, page-2,...])
    scanned_files = utils.get_files(savepath, extensions={'.tiff'})
    scanned_files.sort(key=utils.tokenize)

    # Scan pages
    savepath = f"{output_dir}/ocr/preprocessed/{tail}"
    if os.path.exists(savepath):
        print("\t- [INFO] Skipping pre-processing. The folder already exists.")
    else:
        utils.create_folder(savepath, empty_folder=True)
        print("\t- [INFO] Pre-processing images...")
        for i, f in enumerate(scanned_files, 1):
            print(f"\t- [INFO] Pre-processing image {i} of {len(scanned_files)}")
            preprocess.preprocess_img_file(f, savepath, i, **kwargs)

    # Get preprocessed files
    preprocessed_files = utils.get_files(savepath, extensions={'.pgm'})
    preprocessed_files.sort(key=utils.tokenize)

    # Perform OCR on the scanned pages
    for i, filename in enumerate(preprocessed_files, 1):
        print("\t- [INFO] Performing OCR {} of {}".format(i, len(preprocessed_files)))
        text = read_image(filename, output_dir,  parent_dir=tail, empty_folder=False, **kwargs)
        pages_txt.append(text)

    return pages_txt


def read_pdf_text(filename, **kwargs):
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
    return text


def read_html(filename, extract_style=None, **kwargs):
    if not extract_style:
        return _read_tika(filename), None
    else:
        from selenium import webdriver
        from selenium.webdriver.common.by import By

        # Set browser
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(chrome_options=options)

        # Request site
        driver.get("file://" + filename)

        # Get all text
        text_all = driver.find_element(By.CSS_SELECTOR, "*").text

        # Walk through all the elements
        text_bold = []
        for elem in driver.find_elements(By.CSS_SELECTOR, "*"):
            elem_text = utils.remove_whitespace(str(elem.text))
            if elem_text:
                if extract_style == "bold":
                    # Really slow
                    is_bold = int(elem.value_of_css_property('font-weight')) >= 700
                    if is_bold:
                        text_bold.append(elem_text)

        # Close driver
        driver.quit()

        text_bold = "\n".join(text_bold).strip()
        return text_all, text_bold


def _aux_selector(xhtml_data, *args, **kwargs):
    elements = xhtml_data.find_all('b')
    text = [elem.text for elem in elements] if elements else ""
    return text


def read_html_bs4(filename, xml_selector=None, *args, **kwargs):
    # Read file
    with open(filename, encoding='utf-8') as f:
        data = f.read()
    xhtml_data = BeautifulSoup(data, features='lxml')

    # Extract all text
    text = xhtml_data.text

    # Extract selected text
    if xml_selector:
        text_selector = []

        # Use custom function?
        xml_func = xml_selector if callable(xml_selector) else _aux_selector

        # Walk through elements
        for elem_text in xml_func(xhtml_data, *args, **kwargs):
            text_selected = utils.remove_whitespace(elem_text)  # No breaklines
            text_selector.append(text_selected)

        # Join selected text (one element per line)
        text_selector = "\n".join(text_selector)
    else:
        text_selector = None

    return text, text_selector


def read_rtf(filename):
    return _read_tika(filename)


def read_docx(filename, extract_style=None):
    if not extract_style:
        return _read_tika(filename), None
    else:

        try:
            from docx import Document  # Problems with "from collections import Sequence" (deprecated)
        except ImportError as e:
            print("\t- [ERROR] You need to install 'pywin32'")
            exit()
        document = Document(filename)
        text_all = []
        text_bold = []
        for p in document.paragraphs:
            # Get paragraphs
            text = p.text
            text_all.append(text)

            # Get bold text
            # Not all bold paragraphs are mark as "bold" neither runs (check both)
            if extract_style and text.strip():
                if p.style.font.bold:  # Whole paragraph is bold
                    text_bold.append(text)
                else:  # Walk through chunks
                    text = " "
                    for r in p.runs:
                        if r.bold:
                            text += r.text + " "
                    text = utils.remove_whitespace(text)
                    text_bold.append(text) if text else None

        text_all = "\n".join(text_all)
        text_bold = "\n".join(text_bold)
        return text_all, text_bold


def read_blacklist(path):
    # Get blacklist
    if path and os.path.isfile(path):
        blacklist = read_txt(path)
        blacklist = list(set([l.strip() for l in blacklist.split("\n") if l.strip()]))
        print("\t- [INFO] Using blacklist file. (Regex knowledge is required).")
    else:
        blacklist = []
    return blacklist
