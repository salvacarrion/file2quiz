import os
import regex
import string

from file2quiz import reader
from file2quiz import utils

RGX_SPLITTER = r"[\)\-\]\t ]+"  # Exclude "dots" as they can appear in the ID.
RGX_QUESTION = r"^\d+[\d\.]*"
RGX_ANSWER = r"^[\d\.]*[a-zA-Z]{1}"


def preprocess_text(text, blacklist=None, mode="auto"):
    # Remove unwanted characters
    text = text \
        .replace('`a', 'à').replace('´a', 'á').replace('¨a', 'ä')\
        .replace('`e', 'è').replace('´e', 'é').replace('¨e', 'ë')\
        .replace('`i', 'ì').replace('´i', 'í').replace('¨i', 'ï')\
        .replace('`o', 'ò').replace('´o', 'ó').replace('¨o', 'ö')\
        .replace('`u', 'ù').replace('´u', 'ú').replace('¨u', 'ü')\
        .replace('¨', '\"') \
        .replace('“', '\"').replace('”', '\"') \
        .replace('‘', '\'').replace('’', '\'') \
        .replace('``', '\"') \
        .replace('´´', '\"') \
        .replace('’', '\'') \
        .replace('´', '') \
        .replace('`', '') \
        .replace('…', '...') \
        .replace('€)', 'c)') \
        .replace('©', 'c)') \
        .replace('\ufeff', '')

    # Only latin characters + numbers + punctuation + whitespaces. (this also includes emojis)
    text = utils.normalize_text(text)

    # Remove breaklines for problematic non-id numbers ("el\n155 art. blablabla")
    pattern = regex.compile(r"(?<![\n\?\:]|\.\.\.)[\t ]*\n[\t ]*(?=\d+[\d\.]*[\,\; ]+)", regex.MULTILINE)
    text = regex.sub(pattern, " ", text)

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
    text = utils.replace_words(text, blacklist, replace="") if blacklist else text

    # Fix answers like: (a), (  b  ), etc
    pattern = regex.compile(r"^[\(\[]+\s*([\d\.]*[a-zA-Z]{1})\s*([\)\-\]\t ]+)", regex.MULTILINE)
    text = regex.sub(pattern, r"\1) ", text)

    return text


def get_block_id(block, is_question):
    ID_RGX = RGX_QUESTION if is_question else RGX_ANSWER
    pattern = regex.compile(fr"^({ID_RGX})({RGX_SPLITTER}?)(.*$)")
    m = regex.search(pattern, block)

    if not m:
        return None, block
    else:
        b_id = m.group(1)
        b_text = m.group(3)

        # Normalize ID
        b_id = regex.sub(r"^\.*", "", b_id)  # Remove leading dots
        b_id = regex.sub(r"\.*$", "", b_id)  # Remove trailing dots
        b_id = utils.remove_whitespace(b_id)  # Just in case
        b_id = b_id.lower()
        return b_id, b_text


def preprocess_questions_block(text):
    # Define delimiters
    DELIMITER = "\n@\n@\n@\n"

    # Detect start of question
    pattern = regex.compile(fr"(?<={RGX_QUESTION})([\t ]+)(?=[¿?!¡])", regex.MULTILINE)
    text = regex.sub(pattern, r") ", text)

    # Detect end of question
    rgx_fix_question = regex.compile(fr"(?<={RGX_QUESTION})([\t ]+)(.*)(?=[?:]$|\.\.\.$)", regex.MULTILINE)
    text = regex.sub(rgx_fix_question, r") \2", text)

    # Split block of questions
    pattern = regex.compile(fr"({RGX_QUESTION})({RGX_SPLITTER}.*$)", regex.MULTILINE)
    text = regex.sub(pattern, rf"{DELIMITER}\1\2", text)
    raw_questions = text.split(DELIMITER)
    raw_questions = [q for q in raw_questions[1:] if q.strip()] if raw_questions else []  # We can split the first chunk
    return raw_questions


def preprocess_answers_block(text, single_line=False):
    if single_line:
        raw_blocks = text.split('\n')
    else:
        # Detect start of answer
        pattern = regex.compile(fr"(?<={RGX_ANSWER})(\. ?)(?=[\s\S])", regex.MULTILINE)
        text = regex.sub(pattern, r") ", text)

        # Split answers
        DELIMITER = "\n@\n@\n@\n"
        pattern = regex.compile(fr"({RGX_ANSWER})({RGX_SPLITTER}.*$)", regex.MULTILINE)
        stext = regex.sub(pattern, rf"{DELIMITER}\1\2", text)
        raw_blocks = stext.split(DELIMITER)

    # Remove hyphens excepts if it's a number
    blocks_cleaned = []
    for i, b in enumerate(raw_blocks):
        b_id, content = get_block_id(utils.remove_whitespace(b), is_question=bool(i == 0))
        # Remove punctuation and whispaces except last character
        content_clean = regex.sub(r"^([\p{posix_punct}\s]*)(?=[\p{posix_punct}])", '', content)
        # Remove the rest of the punctuation except if it is a set of special character
        content_clean = regex.sub(r"^([\p{posix_punct}\s]*)(?=[\-\+\¿¡\"\'<>=]|>=|<=|==|\p{Latin})", '', content_clean)
        # Remove minus and pluses if it's not a number
        content_clean = regex.sub(r"^([\-\+]*)(?=\D)", '', content_clean)  # Remove hyphens
        if content_clean.strip():
            blocks_cleaned.append((b_id, content_clean))
    return blocks_cleaned


def normalize_question(text, sentence_case=True):
    # Remove space before quotation mark or colons
    text = regex.sub(r"([\s,;:\-\.\?\"\']*)([\?:\"\'])(\s*)$", r"\2", text)

    # Generic normalization
    text = normalize_generic(text, sentence_case)
    return text


def normalize_answer(text, sentence_case=True):
    # Remove final period
    text = regex.sub(r"([\s\.]*)$", "", text)

    # Generic normalization
    text = normalize_generic(text, sentence_case)
    return text


def normalize_generic(text, sentence_case=True):
    # Reserved words to not change
    si_prefixes = ['', 'Y', 'Z', 'E', 'P', 'T', 'G', 'M', 'k', 'h', 'd', 'c', 'm', 'μ', 'n', 'p', 'f', 'a', 'z', 'y']
    si_units = ['s', 'm', 'k', 'a', 'k', 'mol', 'cd']
    si_units_der = ['rad', 'sr', 'Hz', 'N', 'Pa', 'J', 'W', 'C', 'V', 'F', 'Ω', 'S', 'Wb', 'T', 'H', '°C', 'lm', 'lx',
                    'Bq', 'Gy', 'Sv', 'kat'
                                      'l', 'eV', 'º', 'm2', 'm3', 'm²', 'm³']
    possible_units = set([f"{p}{u}" for p in si_prefixes for u in si_units + si_units_der])
    RESERVED_WORDS = possible_units

    # Remove whitespaces
    text = utils.remove_whitespace(text)

    # First letter upper case
    if sentence_case and len(text) > 2:
        first_word = text.split()[0] if text else ""
        text = text[0].upper() + text[1:] if first_word not in RESERVED_WORDS else text

    # Remove broken line hyphens
    text = regex.sub(r"(?<=\p{Latin}+)([\-\u2012\u2013\u2014\u2015\u2053]+\s+)(?=\p{Latin}+)", '', text)

    # Remove space before/after a parentheses, quotation mark, etc
    text = regex.sub(r"(?<=[\(\[\{\¿\¡\"\']+)(\s+)", '', text)
    text = regex.sub(r"(\s+)(?=[\)\]\}\?\!\"\'\,\.]+)", '', text)

    # Metric rules (remove ampere "a" to avoid problems)
    rgx_metrics = regex.compile(r"(?<=\d+)(\s*)(?=(K|H|D|Da|d|c|m)?(m|s|g|hz|w|v|k|t|min|h|n|Pa|bar)(2|3|²|³)?(?!\p{Latin}))", regex.IGNORECASE|regex.MULTILINE)
    text = regex.sub(rgx_metrics, '', text)

    # Number signs
    rgx_num_signs = regex.compile(r"(?<=\+|\-)(\s*)(?=\d+)", regex.IGNORECASE | regex.MULTILINE)
    text = regex.sub(rgx_num_signs, '', text)

    # Other number signs (>, <, >=, <=)
    rgx_percentage = regex.compile(r"(?<=<|<=|>|>=)(\s*)(?=[\+|\-]?\d+)", regex.IGNORECASE | regex.MULTILINE)
    text = regex.sub(rgx_percentage, '', text)

    # Percentage
    rgx_percentage = regex.compile(r"(?<=\d+)(\s*)%(\s*)(?!\w)", regex.IGNORECASE | regex.MULTILINE)
    text = regex.sub(rgx_percentage, '%', text)

    # Temperature 1
    rgx_temp = regex.compile(r"(?<=\d+)(\s*)º(\s*)C(?!\w)", regex.IGNORECASE|regex.MULTILINE)
    text = regex.sub(rgx_temp, 'ºC', text)

    # Temperature 2
    rgx_temp = regex.compile(r"(\s*)T(\s*)ª(?!\w)", regex.IGNORECASE|regex.MULTILINE)
    text = regex.sub(rgx_temp, ' Tª', text)
    return text.strip()


def q_summary(item, length=50):
    text = "{}) {}".format(*item)
    text = utils.remove_whitespace(text)
    text = text if len(text) < length else text[:length] + "..."
    return text


def build_quiz(questions, solutions=None):
    quiz = {}

    # Add questions
    for q in questions:
        question, answers = q
        quiz[question[0]] = {
            'id': question[0],
            'question': question[1],
            'answers': [ans[1] for ans in answers],
            'correct_answer': None
        }

    # Add answers
    if solutions:
        for ans in solutions:
            id_question, answer = ans
            if id_question in quiz:
                quiz[id_question]['correct_answer'] = answer
            else:
                pass
                # It's already notified aboved
                #print("\t- [WARNING] Missing question for answer '{}'".format(id_question))
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
        # Get missing questions/answers
        q_ids = set([str(q[0][0]) for q in questions])
        sol_ids = set([str(sol[0]) for sol in solutions])

        # Get differences
        missing_questions = sol_ids - q_ids
        missing_ans = q_ids - sol_ids
        missing_questions_str = ", ".join(missing_questions)
        missing_ans_str = ", ".join(list(missing_ans))

        print(f"\t- [WARNING] The number of questions ({len(questions)}) and solutions ({len(solutions)}) do not match")
        print(f"\t\t- Questions missing ({len(missing_questions)}): [{missing_questions_str}]")
        print(f"\t\t- Questions with missing answers ({len(missing_ans)}): [{missing_ans_str}]")

    # Build quiz
    quiz = build_quiz(questions, solutions)
    return quiz


def parse_questions(txt, num_expected_answers=None, mode="auto", *args, **kwargs):
    if mode == "auto":
        return parse_questions_auto(txt, num_expected_answers, single_line=False)
    elif mode == "single-line":
        return parse_questions_auto(txt, num_expected_answers, single_line=True)
    else:
        raise ValueError(f"Unknown question mode: '{mode}'")


def parse_questions_auto(text, num_expected_answers, single_line, *args, **kwargs):
    questions = []

    # Split questions
    raw_questions = preprocess_questions_block(text)

    # Parse questions
    for i, raw_question in enumerate(raw_questions, 1):
        # Split block of answers
        q_blocks = preprocess_answers_block(raw_question, single_line=single_line)
        if q_blocks:
            # Infer question blocks
            q_blocks = infer_question_blocks(q_blocks, single_line, num_expected_answers, *args, **kwargs)

            if q_blocks:
                # Normalize question items
                question, answers = parse_normalize_question(q_blocks, suggested_id=i)
                questions.append([question, answers])
    return questions


def infer_question_blocks(blocks, single_line, num_expected_answers,
                          infer_question=True, skip_on_error=False, *args, **kwargs):
    # Remove empty lines
    q_blocks = []
    for b_id, content in blocks:
        content = content.strip()
        q_blocks.append([b_id, content]) if content else None

    # Infer questions/answers
    # Join questions and answers if needed (IDs must be already normalized)
    if single_line or not infer_question:
        new_blocks = q_blocks
        new_blocks[0][0] = None
    else:  # or (num_expected_answers and len(blocks) == num_expected_answers+1)
        new_blocks = [q_blocks[0]]
        for i, (b_id, b_text) in enumerate(q_blocks[1:]):
            # No words nor numbers
            if not regex.search("(\p{Latin}|\d)", b_text):
                continue

            # Infer blocks
            idx_last = len(new_blocks) - 1
            if b_id is None:  # Join with previous
                new_blocks[idx_last][1] += " " + b_text
            elif len(b_id) == 1 and string.ascii_lowercase[idx_last] != b_id:  # ej: ("a", "una casa")
                new_blocks[idx_last][1] += f" {b_id} {b_text}"
            else:  # Correct or weird IDs (3.2a, 12.b, etc)
                new_blocks.append([b_id, b_text.strip()])

    # Check number of items
    if len(new_blocks) < 2 + 1:
        print(f'\t- [INFO] Block with less than two answers. Skipping block: [Q: "{q_summary(new_blocks[0])}"]')
        return None

    # Check correctness
    q_error = False
    extra_answers = []
    if num_expected_answers:
        # Too many answers
        if len(new_blocks) > num_expected_answers + 1:
            q_error = True
            print(f"\t- [WARNING] More answers ({len(new_blocks) - 1}) than expected ({num_expected_answers}). "
                  f"[Q: \"{q_summary(new_blocks[0])}\"]")

        # Too few answers
        elif len(new_blocks) < num_expected_answers + 1:
            q_error = True
            # Auto-fill answers?
            missing_ans_txt = kwargs.get("fill_missing_answers")
            if missing_ans_txt:
                num_missing_ans = (num_expected_answers + 1) - len(new_blocks)
                extra_answers = [[None, missing_ans_txt] for _ in range(num_missing_ans)]

            filling_str = f"Filling {len(extra_answers)} missing answers. " if extra_answers else ""
            print(f"\t- [WARNING] Less answers ({len(new_blocks) - 1}) than expected ({num_expected_answers}). "
                  f'{filling_str}[Q: "{q_summary(new_blocks[0])}"]')

    # Skip question?
    if q_error and skip_on_error:
        print(f"\t- [WARNING] Skipping question. [Q: \"{q_summary(new_blocks[0])}\"]")
        return None

    # Add extra block
    new_blocks += extra_answers
    return new_blocks


def parse_normalize_question(blocks, suggested_id):
    # Normalize question
    question = blocks[0]
    question[0] = question[0] if question[0] else suggested_id
    question[1] = normalize_question(question[1])

    # Normalize answer
    answers = blocks[1:]
    for i, ans in enumerate(answers):
        ans[0] = string.ascii_lowercase[i]
        ans[1] = normalize_answer(ans[1])

    return question, answers


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


