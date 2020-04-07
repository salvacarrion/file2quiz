import os
import re
import shutil
import regex
import json
import string

import PyPDF2

digits = re.compile(r'(\d+)')
letters = re.compile(r'([a-zA-Z]+)')

rgx_block_question = re.compile(r'(^\d+[\s]*[\.\-\)\t]+[\S\s]*?)(?=^\d+[\s]*[\.\-\)\t]+[\S\s]*?)', re.MULTILINE)  # question to question
rgx_question = re.compile(r'^(\d+)[\s]*[\.\-\)\s]+([\S\s]*?)(?=^[a-zA-Z]{1}[\s]*[\.\-\)\t]+[\S\s]*?$)', re.MULTILINE)  # question to answer
rgx_answer = re.compile(r'^([a-zA-Z]{1})[\s]*[\.\-\)\t]+([\S\s]*?)(?=^.*[\s]*[\.\-\)\t]+[\S\s]*?)', re.MULTILINE) # answer to answer
rgx_block_correct_answer = re.compile(r'(^\d+\D*)', re.MULTILINE)


def parse_exams(input_dir, output_dir, answer_token=None):
    # Check input path
    if not os.path.exists(input_dir):
        raise IOError("Input path does not exists: {}".format(input_dir))

    # Check output path
    if os.path.exists(output_dir):
        print("Deleting output folder contents...")
        shutil.rmtree(output_dir)
    else:
        print("Output path does not exists. Creating folder...".format(output_dir))
    os.mkdir(output_dir)

    # Read input files
    files = get_files(input_dir)

    # Check files
    if not files:
        raise IOError("Not files where found at: {}".format(input_dir))

    # Parse exams
    for i, filename in enumerate(files, 1):
        # Read file
        txt_questions, txt_answers = read_file(filename, answer_token)

        # Parse questions and correct answers
        questions = parse_questions(txt_questions)
        correct_answers = parse_correct_answers(txt_answers, letter2num=True) if answer_token else None

        # Check number of questions and answers
        if correct_answers and len(questions) != len(correct_answers):
            raise IOError("The number of questions ({}) and correct answers ({}) does not match".format(len(questions), len(correct_answers)))

        # Build quiz
        quiz = build_json(questions, correct_answers)

        # Save file
        fname, extension = os.path.splitext(os.path.basename(filename))
        savepath = os.path.join(output_dir, "{}.json".format(fname))
        save_quiz(quiz, savepath)
        print("{}. Quiz '{}' saved!".format(i, fname))


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


def read_file(filename, answer_token):
    txt_questions, txt_answers = "", ""

    # Get path values
    basedir = os.path.basename(filename)
    fname, extension = os.path.splitext(basedir)
    extension = extension.replace('.', '')  # remove dot

    # Select method depending on the extension
    if extension == "txt":
        txt = read_txt(filename)
    elif extension == "pdf":
        txt = read_pdf(filename)
    else:
        raise IOError("Invalid file extension")
    txt = clean_text(txt)

    # Check if the text has to be splitted
    if not answer_token:
        txt_questions = txt

    else:
        # Split text if contains questions and answers
        sections = re.split(re.compile(r"^{}$".format(re.escape(answer_token)), re.MULTILINE), txt)
        if len(sections) == 2:
            txt_questions, txt_answers = sections
        else:
            txt_questions = txt
            #raise IOError("No answer section found. Check delimiter")
    return txt_questions.strip(), txt_answers.strip()


def read_pdf(filename):
    text = ""
    with open(filename, 'rb') as f:
        pdf = PyPDF2.PdfFileReader(f)

        for p in pdf.pages:
            text += p.extractText() + "\n\n\n"
    return text


def read_txt(filename):
    text = ""
    with open(filename, 'r') as f:
        text = f.read()
    return text


def clean_text(text):
    # Remove unwanted characters
    text = text\
        .replace("\t", " ")\
        .replace("\n.", ".")\
        .replace(" .", ".")\
        .replace(" º", "º")\
        .replace('“', '').replace('”', '').replace("'", '')\
        .replace("€)", 'c)')\
        .replace("``", '\"')\
        .replace("´´", '\"')\
        .replace("\ufeff", '')
    text = re.sub(r'[ ]{2,}', ' ', text)  # two whitespaces

    # Only latin characters
    #text = regex.sub('\p{Latin}\p{posix_punct}]+', '', text)

    lines = []
    for l in text.split('\n'):
        l = l.strip()
        if l:
            lines.append(l)
    text = "\n".join(lines)

    return text


def remove_whitespace(text):
    text = re.sub(r"\s", " ", text)
    text = re.sub(r'[ ]{2,}', ' ', text)  # two whitespaces
    return text.strip()


def parse_questions(txt):
    questions = []

    # Split block of questions
    txt += '\n\n0. blabla'  # trick for regex
    question_blocks = rgx_block_question.findall(txt)
    for i, q_block in enumerate(question_blocks):
        q_block += "\n\nz) blablabal"   # trick for regex
        id_question, question = (remove_whitespace(v) for v in rgx_question.findall(q_block)[0])
        answers = [remove_whitespace(ans[1]) for ans in rgx_answer.findall(q_block)]

        # Add questions
        questions.append([str(id_question).strip().lower(), question, answers])
    return questions


def parse_correct_answers(txt, letter2num=True):
    answers = []

    # Split block of questions
    blocks = rgx_block_correct_answer.findall(txt)
    for block in blocks:

        # Get ID question
        block = re.sub(r"[^\da-zA-Z]", '', block)
        id_question = str(digits.search(block)[1]).strip().lower()
        id_answer = str(letters.search(block)[1]).strip().lower()

        if letter2num:
            id_answer = string.ascii_lowercase.index(id_answer)

        # Add questions
        answers.append([id_question, id_answer])
    return answers


def build_json(questions, correct_answers=None):
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


def save_quiz(quiz, filename):
    with open(filename, 'w') as f:
        json.dump(quiz, f)


def load_quiz(filename):
    with open(filename, 'r') as f:
        quiz = json.load(f)
    return quiz


def quiz2txt(quiz, show_correct):
    txt = ""

    # Sort questions by key
    keys = sorted(quiz.keys(), key=lambda x: int(x))
    for i, id_question in enumerate(keys):
        question = quiz[id_question]

        # Format question
        txt += "{}) {}\n".format(id_question, question['question'])

        # Format answers
        for j, ans in enumerate(question['answers']):
            isCorrect = "*" if show_correct and j == question.get("correct_answer") else ""
            txt += "{}{}) {}\n".format(isCorrect, string.ascii_lowercase[j].lower(), ans)
        txt += "\n"
    return txt.strip()
