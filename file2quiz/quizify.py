import os
import re
import regex
import string

from file2quiz import reader
from file2quiz import utils


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
        .replace('“', '\"').replace('”', '\"')\
        .replace('‘', '\'').replace('’', '\'')\
        .replace("€)", 'c)') \
        .replace("©", 'c)') \
        .replace("``", '\"') \
        .replace("´´", '\"') \
        .replace("’", "\'") \
        .replace("\ufeff", '')

    # Only latin characters
    if only_latin:
        text = regex.sub(r"\p{Latin}\p{posix_punct}]+", '', text)

    # Strip whitespace line-by-line
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    text = "\n".join(lines)

    return text


def build_quiz(questions, solutions=None):
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
    if solutions:
        for ans in solutions:
            id_question, answer = ans
            if id_question in quiz:
                quiz[id_question]['correct_answer'] = answer
            else:
                print("[WARNING] Missing question for answer '{}'".format(id_question))
    return quiz


def parse_quiz(input_dir, output_dir, blacklist=None, token_answer=None, single_line=False, num_answers=None,
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
    quizzes_dir = os.path.join(output_dir, "quizzes/json")
    utils.create_folder(quizzes_dir) if save_files else None

    # Parse exams
    quizzes = []
    for i, filename in enumerate(files, 1):
        # Read file
        txt_file = reader.read_txt(filename)

        # Parse txt quiz
        quiz = parse_quiz_txt(txt_file, blacklist=blacklist, token_answer=token_answer, single_line=single_line, num_answers=num_answers)
        quizzes.append((quiz, filename))

    # Save quizzes
    if save_files:
        for i, (quiz, filename) in enumerate(quizzes):
            fname, ext = utils.get_fname(filename)
            reader.save_json(quiz, os.path.join(quizzes_dir, f"{fname}.json"))

    return quizzes


def parse_quiz_txt(text, blacklist=None, token_answer=None, single_line=False, num_answers=None):
    # Preprocess text
    text = preprocess_text(text, blacklist)

    # Split file (questions / answers)
    txt_questions, txt_answers = text, None
    if token_answer:
        if utils.has_regex(token_answer):
            print("[INFO] Your answer token contains regular expressions. Regex knowledge is required.")

        sections = re.split(re.compile(f"{token_answer}", re.IGNORECASE|re.MULTILINE), text)
        if len(sections) == 1:
            print("[WARNING] No correct answer section was detected. (Review the 'answer token', supports regex)")
        elif len(sections) == 2:
            # print("[INFO] Correct answer section detected")
            txt_questions, txt_answers = sections
        else:
            print("[ERROR] Too many sections were detected. (Review the 'answer token', supports regex)")
            exit()

    # Parse quiz
    questions = parse_questions(txt_questions, single_line, num_answers)
    solutions = parse_solutions(txt_answers, letter2num=True) if txt_answers else None

    # Check number of questions and answers
    if solutions and len(questions) != len(solutions):
        print(f"[WARNING] The number of questions ({len(questions)}) "
              f"and solutions ({len(solutions)}) do not match")

    # Build quiz
    quiz = build_quiz(questions, solutions)
    return quiz


def parse_questions(txt, single_line, num_expected_answers=None):
    questions = []

    # Define regex (Do do not allow break lines until the first letter of the q/a is found
    rgx_question = re.compile(r'^(\d+)([^\w\n]+)(?=\w)', re.MULTILINE)
    rgx_answer = re.compile(r'^([a-zA-Z]{1})([^\w\n]+)(?=\w)', re.MULTILINE)

    # Define delimiters
    DELIMITER = "@\n@\n@\n"

    # Split block of questions
    txt = re.sub(rgx_question, rf"{DELIMITER}\1\2", txt)
    raw_questions = txt.split(DELIMITER)
    raw_questions = [q for q in raw_questions[1:] if q.strip()] if raw_questions else []  # We can split the first chunk

    for i, raw_question in enumerate(raw_questions):

        # Split block of answers
        raw_answers = re.sub(rgx_answer, rf"{DELIMITER}\1\2", raw_question)
        raw_answers = raw_answers.split(DELIMITER)

        if num_expected_answers:
            question = " ".join(raw_answers[:-num_expected_answers])  # We allow the question to be "break" the rules
            answers = raw_answers[-num_expected_answers:]  # Select answers first
        else:
            question = raw_answers[0]  # First item is the answer
            answers = raw_answers[1:]

        # Get question ID
        id_question = re.search(rgx_question, question).group(1)
        id_question = id_question.lower().strip()

        # Remove identifiers and clean text
        question = utils.remove_whitespace(re.sub(rgx_question, "", question))
        answers = [utils.remove_whitespace(re.sub(rgx_answer, "", ans)) for ans in answers]

        # Check number of answers
        num_answers = len(answers)
        if num_answers < 2:
            print(f'[WARNING] Less than two answers. Skipping question: [Q: "{question}"]')
            continue
        else:
            # Check against expected answers
            if num_expected_answers:
                if num_answers != num_expected_answers:
                    print(f'[WARNING] {num_answers} answers found / {num_expected_answers} expected. '
                          f'Skipping question: [Q: "{question}"]')
                    continue

        # Add questions
        questions.append([id_question, question, answers])
    return questions


def parse_solutions(txt, letter2num=True):
    answers = []

    # Define regex
    rgx_solutions = re.compile(r'(\b[\d]+)[\W\s]*([a-zA-Z]{1})(?!\w)', re.MULTILINE)
    solutions = re.findall(rgx_solutions, txt)

    for i, (id_question, id_answer) in enumerate(solutions):
        # Format IDs
        id_question = id_question.lower().strip()
        id_answer = id_answer.lower().strip()

        # Letter to number (a => 0, b => 1, c => 2,...)
        id_answer = string.ascii_lowercase.index(id_answer) if letter2num else id_answer

        # Add questions
        answers.append([id_question, id_answer])
    return answers


