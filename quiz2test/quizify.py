import os
import re
import regex
import string

from quiz2test import reader
from quiz2test import utils


rgx_block_question = re.compile(r'(^\d+[\s]*[\.\-\)\t]+[\S\s]*?)(?=^\d+[\s]*[\.\-\)\t]+[\S\s]*?)', re.MULTILINE)  # question to question
rgx_question = re.compile(r'^(\d+)[\s]*[\.\-\)\s]+([\S\s]*?)(?=^[a-zA-Z]{1}[\s]*[\.\-\)\t]+[\S\s]*?$)', re.MULTILINE)  # question to answer
rgx_question_single = re.compile(r'^(\d+)[\s]*[\.\-\)\s]+([\S\s]*?)$')
rgx_answer = re.compile(r'^([a-zA-Z]{1})[\s]*[\.\-\)\t]+([\S\s]*?)(?=^.*[\s]*[\.\-\)\t]+[\S\s]*?)', re.MULTILINE)  # answer to answer
rgx_answer_single = re.compile(r'^([a-zA-Z]{1})[\s]*[\.\-\)\t]+([\S\s]*?)$')
rgx_block_correct_answer = re.compile(r'(^\d+\D*)', re.MULTILINE)


def preprocess_text(text, blacklist):
    # Remove blacklisted words
    text = utils.replace_words(text, blacklist, replace="")
    text = clean_text(text)
    return text


def clean_text(text, only_latin=False):
    # Remove unwanted characters
    text = text \
        .replace("\n.", ".") \
        .replace(" .", ".") \
        .replace(" º", "º") \
        .replace('“', '').replace('”', '').replace("'", '') \
        .replace("€)", 'c)') \
        .replace("``", '\"') \
        .replace("´´", '\"') \
        .replace("’", "\'") \
        .replace("\ufeff", '')
    text = re.sub(r"[ ]{2,}", ' ', text)  # two whitespaces

    # Only latin characters
    if only_latin:
        text = regex.sub(r"\p{Latin}\p{posix_punct}]+", '', text)

    lines = []
    for l in text.split('\n'):
        l = l.strip()
        if l:
            lines.append(l)
    text = "\n".join(lines)

    return text


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


def parse_quiz(input_dir, output_dir, blacklist=None, answer_token=None, single_line=False, num_answers=None,
               save_files=False):
    # Get files
    files = utils.get_files(input_dir, extensions={'.txt'})

    # Get blacklist
    if os.path.isfile(blacklist):
        blacklist = reader.read_txt(blacklist)
        blacklist = list(set([l.strip() for l in blacklist.split("\n") if l.strip()]))
    else:
        blacklist = []

    # Create quizzes folder
    quizzes_dir = os.path.join(output_dir, "quizzes")
    utils.create_folder(quizzes_dir) if save_files else None

    # Parse exams
    quizzes = []
    for i, filename in enumerate(files, 1):
        # Read file
        txt_file = reader.read_txt(filename)

        # Preprocess text
        txt_file = preprocess_text(txt_file, blacklist)

        # Split file (questions / answers)
        txt_questions, txt_answers = txt_file, None
        if answer_token:
            sections = re.split(answer_token, txt_file)
            if len(sections) == 1:
                print("[INFO] No correct answer section was detected")
            elif len(sections) == 2:
                print("[INFO] Correct answer section detected")
                txt_questions, txt_answers = sections
            else:
                print("[ERROR] Too many sections were detected")
                exit()

        # Parse quiz
        questions = parse_questions(txt_questions, single_line, num_answers)
        correct_answers = parse_correct_answers(txt_answers, letter2num=True) if txt_answers else None

        # Check number of questions and answers
        if correct_answers and len(questions) != len(correct_answers):
            print(f"[WARNING] The number of questions ({len(questions)}) "
                  f"and correct answers ({len(correct_answers)}) do not match")

        # Build quiz
        quiz = build_quiz(questions, correct_answers)
        quizzes.append((quiz, filename))

    # Save quizzes
    if save_files:
        for i, (quiz, filename) in enumerate(quizzes):
            fname, ext = utils.get_fname(filename)
            reader.save_json(quiz, os.path.join(quizzes_dir, f"{fname}.json"))

    return quizzes


def parse_questions(txt, single_line, num_answers=None):
    questions = []

    # Split block of questions
    txt += '\n\n0. blabla'  # trick for regex
    question_blocks = rgx_block_question.findall(txt)
    for i, q_block in enumerate(question_blocks):

        if single_line:
            lines = q_block.split("\n")
            id_question, question = (utils.remove_whitespace(v) for v in rgx_question_single.match(lines[0]).groups())

            answers = []
            for q_answer in lines[1:]:
                m = rgx_answer_single.match(q_answer)
                if m and len(m.groups()) == 2:
                    id_ans, ans = m.groups()
                else:
                    ans = q_answer
                answers.append(utils.remove_whitespace(ans))
        else:
            q_block += "\n\nz) blablabal"  # trick for regex
            id_question, question = (utils.remove_whitespace(v) for v in rgx_question.findall(q_block)[0])
            answers = [utils.remove_whitespace(ans[1]) for ans in rgx_answer.findall(q_block)]

        # Review answers (double-check)
        answers = [ans for ans in answers if ans]  # Add non-empty answers

        # Check number of answers
        q_str_error = q_block.replace('\n', ' ').strip()
        if num_answers and len(answers) != num_answers:
            print("[WARNING] Skipping question. {} answers found / {} expected. "
                  "[Q: \"{}\"]".format(len(answers), num_answers, q_str_error))
            continue
        else:
            if len(answers) < 2:
                print("[WARNING] Skipping question. Less than two answers. [Q: \"{}\"]".format(q_str_error))
                continue

        # Add questions
        questions.append([str(id_question).strip().lower(), question, answers])
    return questions


def parse_correct_answers(txt, letter2num=True):
    answers = []

    # Compile regex
    digits = re.compile(r'(\d+)')
    letters = re.compile(r'([a-zA-Z]+)')

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


