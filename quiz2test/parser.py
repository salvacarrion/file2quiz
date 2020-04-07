import os
import re
import shutil
import regex
import json
import string

digits = re.compile(r'(\d+)')
letters = re.compile(r'([a-zA-Z]+)')

# p_question = r"^(\d+[\s]*[\W]{0,2}[\S\s]*?)(?=^[a-zA-Z]*[\s\W]+.*$)"
# p_answer = r"^([a-zA-Z]*)[\s\W]+(.*)$"
# rgx_block_question = re.compile(r'^(\d+[\s]*[\W]{0,2}[\S\s]*?)(?=^\d+[\s]*[\W]{0,2})', re.MULTILINE)

rgx_block_question = re.compile(r'(^\d+[\s]*[\W]{0,2}[\S\s]*?)(?=^\d+[\s]*[\W]{0,2}[\S\s]*?)', re.MULTILINE)
rgx_question = re.compile(r'^(\d+)[\s]*[\W]{0,2}([\S\s]*?)(?=^[a-zA-Z]{1}[\s\W]+.*$)', re.MULTILINE)
rgx_answer = re.compile(r'^([a-zA-Z]{1})[\s\W]+(.*)$', re.MULTILINE)
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
    files = read_files(input_dir)

    # Check files
    if not files:
        raise IOError("Not files where found at: {}".format(input_dir))

    # Parse exams
    for i, f in enumerate(files, 1):
        basedir = os.path.basename(f)
        fname, extension = os.path.splitext(basedir)

        # Read file
        txt_questions, txt_answers = read_file(f, answer_token)

        # Parse questions and correct answers
        questions = parse_questions(txt_questions)
        correct_answers = parse_correct_answers(txt_answers, letter2num=True) if answer_token else None

        # Check number of questions and answers
        if correct_answers and len(questions) != len(correct_answers):
            raise IOError("The number of questions ({}) and correct answers ({}) does not match".format(len(questions), len(correct_answers)))

        # Build quiz
        quiz = build_json(questions, correct_answers)

        # Save file
        filename = os.path.join(output_dir, "{}.json".format(fname))
        save_quiz(quiz, filename)
        print("{}. Quiz '{}' saved!".format(i, fname))


def read_files(path, extension="txt"):
    files = []
    for file in os.listdir(path):
        if file.endswith(".{}".format(extension)):
            files.append(os.path.join(path, file))
    return files


def read_file(filename, answer_token):
    txt_questions, txt_answers = None, None

    with open(filename, 'r') as f:
        txt = clean_text(f.read())

        # Check if the text has to be splitted
        if not answer_token:
            txt_questions = txt

        else:
            # Split text if contains questions and answers
            sections = re.split(re.compile(r"^{}$".format(re.escape(answer_token)), re.MULTILINE), txt)
            if len(sections) == 2:
                txt_questions, txt_answers = sections
            else:
                raise IOError("No answer section found. Check delimiter")
    return txt_questions.strip(), txt_answers.strip()


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
    text = regex.sub('\p{Latin}\p{posix_punct}]+', '', text)

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
        id_question, question = (remove_whitespace(v) for v in rgx_question.findall(q_block)[0])
        answers = [remove_whitespace(ans[1]) for ans in rgx_answer.findall(q_block)]

        # Add questions
        questions.append([str(id_question).strip().lower(), question, answers])
    return questions


def parse_correct_answers(txt, letter2num=False):
    answers = []
    letter2num = "abcdefghijklmnopqrstuvwxyz"

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


def quiz2txt(quiz, show_correct=True):
    txt = ""

    # Sort questions by key
    keys = sorted(quiz.keys(), key=lambda x: int(x))
    for i, id_question in enumerate(keys):
        question = quiz[id_question]

        # Format question
        txt += "{}) {}\n".format(id_question, question['question'])

        # Format answers
        for j, ans in enumerate(question['answers']):
            isCorrect = "*" if j == question.get("correct_answer") else ""
            txt += "{}{}) {}\n".format(isCorrect, string.ascii_lowercase[j].lower(), ans)
        txt += "\n"
    return txt
