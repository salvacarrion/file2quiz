import os
import re
import regex
import string

from file2quiz import reader
from file2quiz import utils

# Define regex (Do do not allow break lines until the first letter of the q/a is found
RGX_QUESTION = re.compile(r'^(\d+)([^\w\n]+)(?=\s+\d+|\s*[a-zA-Z])', re.MULTILINE)
RGX_ANSWER = re.compile(r'^([a-zA-Z]{1})([^\w\n]+)(?=\s+\d+|\s*[a-zA-Z])', re.MULTILINE)


def preprocess_text(text, blacklist, mode):
    # Remove unwanted characters
    text = text \
        .replace('“', '\"').replace('”', '\"') \
        .replace('‘', '\'').replace('’', '\'') \
        .replace("€)", 'c)') \
        .replace("©", 'c)') \
        .replace("``", '\"') \
        .replace("´´", '\"') \
        .replace("’", "\'") \
        .replace("\ufeff", '')

    # Only latin characters + numbers + punctuation + whitespaces. (this also includes emojis)
    text = utils.normalize_text(text)

    # Strip whitespace line-by-line
    lines = [l.strip() for l in text.split('\n')]
    text = "\n".join(lines)

    # Specific pre-processing
    if mode == "auto":
        # Remove empty lines
        lines = [l for l in text.split('\n') if l.strip()]
        text = "\n".join(lines)
    else:
        pass

    # Remove blacklisted words
    text = utils.replace_words(text, blacklist, replace="")
    return text


def normalize_question(text, remove_id=True):
    # Remove identifiers
    if remove_id:
        text = re.sub(RGX_QUESTION, "", text)

    # Remove space before quotation mark or colons
    text = re.sub(r"([\s,;:\-\.\?]*)([\?:])(\s*)$", r"\2", text)

    # Remove whitespaces
    text = utils.remove_whitespace(text)

    # First letter upper case
    text = text[0].upper() + text[1:] if len(text) > 2 else text
    return text


def normalize_answers(text, remove_id=True):
    # Remove identifiers and clean text
    if remove_id:
        text = re.sub(RGX_ANSWER, "", text)

    # Remove final period
    text = re.sub(r"([\s\.]*)$", "", text)

    # Remove whitespaces
    text = utils.remove_whitespace(text)

    # First letter upper case
    text = text[0].upper() + text[1:] if len(text) > 2 else text
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


def parse_quiz(input_dir, output_dir, blacklist=None, token_answer=None, num_answers=None,
               mode="auto", save_files=False):
    # Get files
    files = utils.get_files(input_dir, extensions={'.txt'})

    # Get blacklist
    if blacklist and os.path.isfile(blacklist):
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
        quiz = parse_quiz_txt(txt_file, blacklist, token_answer, num_answers, mode)
        quizzes.append((quiz, filename))

    # Save quizzes
    if save_files:
        for i, (quiz, filename) in enumerate(quizzes):
            fname, ext = utils.get_fname(filename)
            reader.save_json(quiz, os.path.join(quizzes_dir, f"{fname}.json"))

    return quizzes


def parse_quiz_txt(text, blacklist=None, token_answer=None,  num_answers=None, mode="auto"):
    # Preprocess text
    text = preprocess_text(text, blacklist, mode)

    # Define delimiter
    DELIMITER = "\n@\n@\n@\n"

    # Split file (questions / answers)
    txt_questions, txt_answers = text, None
    if token_answer:
        if utils.has_regex(token_answer):
            print("[INFO] Your answer token contains regular expressions. Regex knowledge is required.")

        # Split section (first match)
        rxg_splitter = re.compile(f"{token_answer}", re.IGNORECASE | re.MULTILINE)
        text = re.sub(rxg_splitter, DELIMITER, text, count=1)
        sections = text.split(DELIMITER)

        if len(sections) == 1:
            print("[WARNING] No correct answer section was detected. (Review the 'answer token', supports regex)")
        elif len(sections) == 2:
            # print("[INFO] Correct answer section detected")
            txt_questions, txt_answers = sections
        else:
            print("[ERROR] Too many sections were detected. (Review the 'answer token', supports regex)")
            exit()

    # Parse quiz
    questions = parse_questions(txt_questions, num_answers, mode)
    solutions = parse_solutions(txt_answers, letter2num=True) if txt_answers else None

    # Check number of questions and answers
    if solutions and len(questions) != len(solutions):
        print(f"[WARNING] The number of questions ({len(questions)}) "
              f"and solutions ({len(solutions)}) do not match")

    # Build quiz
    quiz = build_quiz(questions, solutions)
    return quiz


def parse_questions(txt, num_expected_answers=None, mode="auto"):
    if mode == "auto":
        return parse_questions_auto(txt, num_expected_answers)
    elif mode == "single-line":
        return parse_questions_single_line(txt, num_expected_answers)
    else:
        raise ValueError(f"Unknown question mode: '{mode}'")


def parse_questions_auto(txt, num_expected_answers):
    questions = []

    # Define delimiters
    DELIMITER = "\n@\n@\n@\n"

    # Split block of questions
    txt = re.sub(RGX_QUESTION, rf"{DELIMITER}\1\2", txt)
    raw_questions = txt.split(DELIMITER)
    raw_questions = [q for q in raw_questions[1:] if q.strip()] if raw_questions else []  # We can split the first chunk

    # Parse questions
    for i, raw_question in enumerate(raw_questions, 1):
        # Split block of answers
        raw_answers = re.sub(RGX_ANSWER, rf"{DELIMITER}\1\2", raw_question)
        raw_answers = raw_answers.split(DELIMITER)

        # Normalize question items
        parsed_question = parse_normalize_question(raw_answers, num_expected_answers, i)

        # Add question
        if parsed_question:
            id_question, question, answers = parsed_question

            # Add questions
            questions.append([id_question, question, answers])
    return questions


def parse_questions_single_line(txt, num_expected_answers):
    questions = []

    # Define regex (Do do not allow break lines until the first letter of the q/a is found
    rgx_block = re.compile(r'([\n]{2,})', re.MULTILINE)

    # Define delimiters
    DELIMITER = "\n@\n@\n@\n"

    # Split block of questions
    txt = re.sub(rgx_block, rf"{DELIMITER}", txt)
    raw_questions = txt.split(DELIMITER)
    raw_questions = [q for q in raw_questions if q.strip()] if raw_questions else []  # We can split the first chunk

    # Parse questions
    for i, raw_question in enumerate(raw_questions, 1):

        # Split question and answers
        raw_answers = raw_question.split('\n')

        # Normalize question items
        parsed_question = parse_normalize_question(raw_answers, num_expected_answers, i)

        # Add question
        if parsed_question:
            id_question, question, answers = parsed_question

            # Add questions
            questions.append([id_question, question, answers])
    return questions


def parse_normalize_question(question_blocks, num_expected_answers, suggested_id):
    # Remove whitespaces
    question_blocks = [utils.remove_whitespace(item) for item in question_blocks]

    # Get questions and answers
    if num_expected_answers:
        question = " ".join(question_blocks[:-num_expected_answers])  # We allow the question to be "break" the rules
        answers = question_blocks[-num_expected_answers:]  # Select answers first
    else:
        question = question_blocks[0]  # First item is the answer
        answers = question_blocks[1:]

    # Get question ID
    id_question = re.search(RGX_QUESTION, question)
    if id_question:
        id_question = id_question.group(1)
    else:
        id_question = str(suggested_id)
    id_question = id_question.lower().strip()

    # Normalize question and answers
    question = normalize_question(question)
    answers = [normalize_answers(ans) for ans in answers]

    # Check number of answers
    num_answers = len(answers)
    if num_answers < 2:
        print(f'[WARNING] Less than two answers. Skipping question: [Q: "{question}"]')
        return None
    else:
        # Check against expected answers
        if num_expected_answers:
            if num_answers != num_expected_answers:
                print(f'[WARNING] {num_answers} answers found / {num_expected_answers} expected. '
                      f'Skipping question: [Q: "{question}"]')
                return None
    return id_question, question, answers


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


