import os
import shutil
import json

import PyPDF2

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


def read_pdf(filename):
    text = ""
    with open(filename, 'rb') as f:
        pdf = PyPDF2.PdfFileReader(f)

        for p in pdf.pages:
            text += p.extractText() + "\n\n\n"
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


def check_output(output):
    # Check output path
    if os.path.exists(output):
        print("Deleting output folder contents...")
        shutil.rmtree(output)
    else:
        print("Output path does not exists. Creating folder...".format(output))
    os.mkdir(output)


def get_files(path, extensions=None):
    files = []

    if extensions is None:
        extensions = {'txt', 'pdf'}

    for filename in os.listdir(path):
        # Get extension
        fname, ext = os.path.splitext(filename)
        ext = ext.replace('.', '')  # remove dot

        # Check if the extension is valid
        if ext in extensions:
            files.append(os.path.join(path, filename))
        else:
            print("Ignoring file: '{}'. Invalid extension".format(filename))
    return files


def get_banned_words(filename):
    if filename and os.path.exists(filename):
        with open(filename, 'r', encoding="utf8") as f:
            lines = f.read()
            words = [l.strip() for l in lines.split('\n') if l.strip()]
            return list(set(words))
    else:
        print("[WARNING] Banned words file not found")
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
