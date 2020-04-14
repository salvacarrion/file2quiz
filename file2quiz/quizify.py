import os
import re
import regex
import string

from file2quiz import reader
from file2quiz import utils

# (num/letter) + (symbols+/space*)
#RGX_BASE = r"([\.\)\-\]\t ]+)"
RGX_BASE = r"([\t ]*[\p{posix_punct}\t]+[\t ]*)"

# Questions startswith [¡¿, letter] or [number with a whitespace,+,-];  weird case "1.2.2" => (Not a question"
# Answers startswith [¡¿, letter] or [number with a whitespace,+,-]; weird case "a.2.2" => "a) 2.2"
RGX_QUESTION = regex.compile(r"^(\d+[\d\.]*?)"       + RGX_BASE + "(?=[¡¿\t ]*[\p{Latin}]+|[-+\t ]+[\d]+)", regex.MULTILINE)
RGX_ANSWER = regex.compile(r"^([\d\.]*[a-zA-Z]{1})" + RGX_BASE + "(?=[¡¿\t ]*[\p{Latin}]+|[-+\t ]?[\d]+)", regex.MULTILINE)

# (debug) ascii: (\d+[\d\.]*?)([\.\)\-\t ]+[\t ]*)(?=[¡¿\t ]*[a-zA-Z]+|[-+\t ]+[\d]+)

# Reserved words to not change
si_prefixes = ['', 'Y', 'Z', 'E', 'P', 'T', 'G', 'M', 'k', 'h', 'd', 'c', 'm', 'μ', 'n', 'p', 'f', 'a', 'z', 'y']
si_units = ['s', 'm', 'k', 'a', 'k', 'mol', 'cd']
si_units_der = ['rad','sr','Hz','N','Pa','J','W','C','V','F','Ω','S','Wb','T','H','°C','lm','lx','Bq','Gy','Sv','kat'
                'l', 'eV', 'º', 'm2', 'm3', 'm²', 'm³']
possible_units = set([f"{p}{u}" for p in si_prefixes for u in si_units+si_units_der])
RESERVED_WORDS = possible_units


def preprocess_text(text, blacklist, mode):
    # Remove unwanted characters
    text = text \
        .replace('“', '\"').replace('”', '\"') \
        .replace('‘', '\'').replace('’', '\'') \
        .replace('€)', 'c)') \
        .replace('©', 'c)') \
        .replace('``', '\"') \
        .replace('´´', '\"') \
        .replace('’', '\'') \
        .replace('´', '') \
        .replace('`', '') \
        .replace('\ufeff', '')

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


def normalize_question(text, remove_id=True, sentence_case=True):
    # Remove identifiers
    if remove_id:
        text = regex.sub(RGX_QUESTION, "", text)

    # Remove space before quotation mark or colons
    text = regex.sub(r"([\s,;:\-\.\?]*)([\?:])(\s*)$", r"\2", text)

    # Generic normalization
    text = normalize_generic(text, sentence_case)
    return text


def normalize_answers(text, remove_id=True, sentence_case=True):
    # Remove identifiers and clean text
    if remove_id:
        text = regex.sub(RGX_ANSWER, "", text)

    # Remove final period
    text = regex.sub(r"([\s\.]*)$", "", text)

    # Generic normalization
    text = normalize_generic(text, sentence_case)
    return text


def normalize_generic(text, sentence_case=True):
    # Remove whitespaces
    text = utils.remove_whitespace(text)

    # First letter upper case
    if sentence_case and len(text) > 2:
        first_word = text.split()[0] if text else ""
        text = text[0].upper() + text[1:] if first_word not in RESERVED_WORDS else text

    # Remove broken line hyphens
    text = regex.sub(r"(?<=\p{Latin}+)([\-\u2012\u2013\u2014\u2015\u2053]+\s+)(?=\p{Latin}+)", '', text)

    # Remove space before/after a parentheses, quotation mark, etc
    text = regex.sub(r"(?<=[\(\[\{\¿\¡]+)(\s+)", '', text)
    text = regex.sub(r"(\s+)(?=[\)\]\}\?\!]+)", '', text)
    return text


def q_summary(text, length=50):
    text = text.replace("\n", "")
    text = text if len(text)<length else text[:length] + "..."
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
                print("\t- [WARNING] Missing question for answer '{}'".format(id_question))
    return quiz


def parse_quiz(input_dir, output_dir, blacklist_path=None, token_answer=None, num_answers=None, mode="auto",
               save_files=False, *args, **kwargs):
    print(f'##############################################################')
    print(f'### QUIZ PARSER')
    print(f'##############################################################\n')

    # Get files
    files = utils.get_files(input_dir, extensions={'.txt'})

    # Get blacklist
    blacklist = reader.read_blacklist(blacklist_path)

    # Create quizzes folder
    quizzes_dir = os.path.join(output_dir, "quizzes/json")
    utils.create_folder(quizzes_dir) if save_files else None

    # Parse exams
    quizzes = []
    total_questions = 0
    for i, filename in enumerate(files, 1):
        tail, basedir = utils.get_tail(filename)
        fname, ext = utils.get_fname(filename)

        print("")
        print(f'==============================================================')
        print(f'[INFO] ({i}/{len(files)}) Parsing quiz: "{tail}"')
        print(f'==============================================================')

        # Read file
        txt_file = reader.read_txt(filename)

        # Parse txt quiz
        quiz = parse_quiz_txt(txt_file, blacklist, token_answer, num_answers, mode, *args, **kwargs)

        # Keep count of total questions
        total_questions += len(quiz)
        quizzes.append((quiz, filename))

        # Show info
        if len(quiz) == 0:
            print(f"\t- [WARNING] No quizzes were found ({tail})")
        print(f"\t- [INFO] Parsing done! {len(quiz)} questions were found. ({tail})")

        # Save quizzes
        if save_files:
            print(f"\t- [INFO] Saving json... ({fname}.json)")
            reader.save_json(quiz, os.path.join(quizzes_dir, f"{fname}.json"))

    print("")
    print("--------------------------------------------------------------")
    print("SUMMARY")
    print("--------------------------------------------------------------")
    print(f"- [INFO] Documents parsed: {len(quizzes)}")
    print(f"- [INFO] Questions found: {total_questions}")
    print("--------------------------------------------------------------\n\n")
    return quizzes


def parse_quiz_txt(text, blacklist=None, token_answer=None, num_answers=None, mode="auto", *args, **kwargs):
    # Preprocess text
    text = preprocess_text(text, blacklist, mode)

    # Define delimiter
    DELIMITER = "\n@\n@\n@\n"

    # Split file (questions / answers)
    txt_questions, txt_answers = text, None
    if token_answer:
        if utils.has_regex(token_answer):
            print("\t- [INFO] Your answer token contains regular expressions. Regex knowledge is required.")

        # Split section (first match)
        rxg_splitter = regex.compile(f"{token_answer}", regex.IGNORECASE | regex.MULTILINE)
        text = regex.sub(rxg_splitter, DELIMITER, text, count=1)
        sections = text.split(DELIMITER)

        if len(sections) == 1:
            print("\t- [WARNING] No correct answer section was detected. (Review the 'answer token', supports regex)")
        elif len(sections) == 2:
            # print("\t- [INFO] Correct answer section detected")
            txt_questions, txt_answers = sections
        else:
            print("\t- [ERROR] Too many sections were detected. (Review the 'answer token', supports regex)")
            exit()

    # Parse quiz
    questions = parse_questions(txt_questions, num_answers, mode, *args, **kwargs)
    solutions = parse_solutions(txt_answers, letter2num=True) if txt_answers else None

    # Check number of questions and answers
    if solutions and len(questions) != len(solutions):
        print(f"\t- [WARNING] The number of questions ({len(questions)}) "
              f"and solutions ({len(solutions)}) do not match")

    # Build quiz
    quiz = build_quiz(questions, solutions)
    return quiz


def parse_questions(txt, num_expected_answers=None, mode="auto", *args, **kwargs):
    if mode == "auto":
        return parse_questions_auto(txt, num_expected_answers, *args, **kwargs)
    elif mode == "single-line":
        return parse_questions_single_line(txt, num_expected_answers, *args, **kwargs)
    else:
        raise ValueError(f"Unknown question mode: '{mode}'")


def parse_questions_auto(txt, num_expected_answers, *args, **kwargs):
    questions = []

    # Define delimiters
    DELIMITER = "\n@\n@\n@\n"

    # Split block of questions
    txt = regex.sub(RGX_QUESTION, rf"{DELIMITER}\1\2", txt)
    raw_questions = txt.split(DELIMITER)
    raw_questions = [q for q in raw_questions[1:] if q.strip()] if raw_questions else []  # We can split the first chunk

    # Parse questions
    for i, raw_question in enumerate(raw_questions, 1):
        # Split block of answers
        raw_answers = regex.sub(RGX_ANSWER, rf"{DELIMITER}\1\2", raw_question)
        raw_answers = raw_answers.split(DELIMITER)

        # Normalize question items
        parsed_question = parse_normalize_question(raw_answers, num_expected_answers, i, *args, **kwargs)

        # Add question
        if parsed_question:
            id_question, question, answers = parsed_question

            # Add questions
            questions.append([id_question, question, answers])
    return questions


def parse_questions_single_line(txt, num_expected_answers, *args, **kwargs):
    questions = []

    # Define regex (Do do not allow break lines until the first letter of the q/a is found
    rgx_block = regex.compile(r'([\n]{2,})', regex.MULTILINE)

    # Define delimiters
    DELIMITER = "\n@\n@\n@\n"

    # Split block of questions
    txt = regex.sub(rgx_block, rf"{DELIMITER}", txt)
    raw_questions = txt.split(DELIMITER)
    raw_questions = [q for q in raw_questions if q.strip()] if raw_questions else []  # We can split the first chunk

    # Parse questions
    for i, raw_question in enumerate(raw_questions, 1):

        # Split question and answers
        raw_answers = raw_question.split('\n')

        # Normalize question items
        parsed_question = parse_normalize_question(raw_answers, num_expected_answers, i, *args, **kwargs)

        # Add question
        if parsed_question:
            id_question, question, answers = parsed_question

            # Add questions
            questions.append([id_question, question, answers])
    return questions


def parse_normalize_question(question_blocks, num_expected_answers, suggested_id, *args, **kwargs):
    # Remove empty lines
    question_blocks = [item.strip() for item in question_blocks if item.strip()]

    # Check number of items
    if len(question_blocks) < 2+1:
        print(f'\t- [INFO] Block with less than two answers. Skipping block: [Q: "{q_summary(question_blocks[0])}"]')
        return None

    # Set policy depending on the questions and answers
    policy = "single-line-question"
    extra_answers = []
    if num_expected_answers:
        # Too many answers
        if len(question_blocks) > num_expected_answers + 1:
            print(f"\t- [WARNING] More answers ({len(question_blocks)-1}) than expected ({num_expected_answers}). "
                  f'Inferring question [Q: "{q_summary(question_blocks[0])}]"')
            policy = "multiline-question"

        # Too few answers
        elif len(question_blocks) < num_expected_answers + 1:
            # Auto-fill answers?
            missing_ans_txt = kwargs.get("fill_missing_answers")
            if missing_ans_txt:
                num_missing_ans = (num_expected_answers + 1) - len(question_blocks)
                extra_answers = [f'"z) {missing_ans_txt}' for _ in range(num_missing_ans)]

            print(f"\t- [WARNING] Less answers ({len(question_blocks)-1}) than expected ({num_expected_answers}). "
                  f'Filling {len(extra_answers)} missing answers. [Q: "{q_summary(question_blocks[0])}"]')

    # Choose questions and answers
    if policy == "single-line-question":  # Rule: Single-line question and answers variable
        question = question_blocks[0]
        answers = question_blocks[1:] + extra_answers

    elif policy == "multiline-question":  # Rule: Multi-line question and answers fixed
        question = " ".join(question_blocks[:-num_expected_answers])
        answers = question_blocks[-num_expected_answers:] + extra_answers
    else:
        raise NameError("Unknown policy")

    # Get question ID
    id_question = regex.search(RGX_QUESTION, question)
    if id_question:
        id_question = id_question.group(1)
        id_question = regex.sub(r"\.*$", "", id_question)
    else:
        id_question = str(suggested_id)
    id_question = id_question.lower().strip()

    # Normalize question and answers
    question = normalize_question(question)
    answers = [normalize_answers(ans) for ans in answers]

    return id_question, question, answers


def parse_solutions(txt, letter2num=True):
    answers = []

    # Define regex
    rgx_solutions = regex.compile(r'\b(\d+[\d\.]*?)[\W\s]*([a-zA-Z]{1})(?!\w)', regex.MULTILINE)
    solutions = regex.findall(rgx_solutions, txt)

    for i, (id_question, id_answer) in enumerate(solutions):
        # Format question IDs
        id_question = id_question.lower().strip()
        id_question = regex.sub(r"\.*$", "", id_question)

        id_answer = id_answer.lower().strip()
        id_answer = regex.sub(r"\.*$", "", id_answer)

        # Letter to number (a => 0, b => 1, c => 2,...)
        id_answer = string.ascii_lowercase.index(id_answer) if letter2num else id_answer

        # Add questions
        answers.append([id_question, id_answer])
    return answers


