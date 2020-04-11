import re
import os
import shutil
import pathlib

import regex


def get_fname(filename):
    basedir, tail = os.path.split(filename)
    fname, ext = os.path.splitext(tail)
    return fname, ext


def get_files(path, extensions=None):
    # if extensions is None:
    #     extensions = {".txt", ".pdf", ".jpg", ".jpeg", ".html"}

    # Search
    valid_files = []
    files = os.listdir(path) if os.path.isdir(path) else [path]
    for filename in files:
        fname, ext = get_fname(filename)

        # Skip hidden files
        if not fname.startswith("."):
            # Check if the extension is valid
            if extensions is None or ext in extensions:
                valid_files.append(os.path.join(path, filename))
    return valid_files


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


def tokenize(filename):
    # Sorts strings that contain numbers using a natural order (file001, file002, file003, etc)
    digits = re.compile(r'(\d+)')
    return tuple(int(token) if match else token
                 for token, match in
                 ((fragment, digits.search(fragment))
                  for fragment in digits.split(filename)))


def replace_words(text, blacklist, replace=""):
    if blacklist:
        blacklist_regex = "|".join(blacklist)
        return re.sub(rf"{blacklist_regex}", replace, text)
    else:
        return text


def remove_whitespace(text):
    text = re.sub(r"\s", " ", text)
    text = re.sub(r'[ ]{2,}', ' ', text)  # two whitespaces
    return text.strip()

