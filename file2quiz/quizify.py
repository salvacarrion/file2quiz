import os
import regex
import string
from operator import itemgetter

from file2quiz import reader
from file2quiz import utils

RGX_SPLITTER = r"[ ]*[\.\)\-\]\t]+" #r"[\)\-\]\t ]+"  # Exclude "dots" as they can appear in the ID.
RGX_QUESTION = r"^[\(\[ ]*(?:\d+\.)*\d+"
RGX_ANSWER = r"^[\(\[ ]*?(?:(?:\d+\.)*\d+)*[a-zA-Z]{1}"
DELIMITER = "\n@\n@\n@\n"


def preprocess_text(text, blacklist=None, mode="auto", from_ocr=False):
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
        .replace('·º', 'º') \
        .replace('\ufeff', '')

    # Only latin characters + numbers + punctuation + whitespaces. (this also includes emojis)
    text = utils.normalize_text(text)

    # Strip whitespace line-by-line
    lines = [l.strip() for l in text.split('\n')]
    text = "\n".join(lines)

    # Specific pre-processing
    if mode == "auto":
        # # Remove breaklines for problematic non-id numbers ("el\n155 art. blablabla")
        # pattern = regex.compile(r"(?<![\n\?\:]|\.\.\.)[\t ]*\n[\t ]*(?=\d+[\d\.]*[\,\; ]+)", regex.MULTILINE)
        # text = regex.sub(pattern, " ", text)

        # Remove empty lines
        lines = [l for l in text.split('\n') if l.strip()]
        text = "\n".join(lines)
    else:
        text = regex.sub(r"\n{2,}", "\n\n", text)

    # Remove blacklisted words
    text = utils.replace_words(text, blacklist, replace="") if blacklist else text

    # Broken lines
    broken_lines = regex.compile(r"(?<=\p{Latin}+)( *[\-\u2012\u2013\u2014\u2015\u2053]+\s+)(?=\p{Latin}+)", regex.MULTILINE)
    text = regex.sub(broken_lines, r"", text)

    if from_ocr:
        text = text \
            .replace("*C", "ºC") \
            .replace("*F", "ºF") \
            .replace("*K", "ºK") \
            .replace("Cc", "c")

        # Fix answers
        p_ans0 = regex.compile(r"^.{,4}?\) *", regex.MULTILINE)
        text = regex.sub(p_ans0, "z) ", text)

        p_ans0 = regex.compile(r"^[abcdeABCDE][\)\.\-] *", regex.MULTILINE)
        text = regex.sub(p_ans0, "z) ", text)

        p_ans0 = regex.compile(r"^[bcdeBCDE][\W ] *", regex.MULTILINE)
        text = regex.sub(p_ans0, "z) ", text)

        p_ans0 = regex.compile(r"^[a] (?=[A-Z])", regex.MULTILINE)
        text = regex.sub(p_ans0, "z) ", text)

        p_ans0 = regex.compile(r"^([ÁÉÍÓÚaéíóú]|dy|0) ", regex.MULTILINE)
        text = regex.sub(p_ans0, "z) ", text)

        # Do some cleaning
        text = text.replace("z) z)", "z)")

        # Fix typical errors
        p_ans1 = regex.compile(r"(?<=[ABCD])y(?=[ABCD]( |$))", regex.MULTILINE)
        text = regex.sub(p_ans1, " y ", text)

        # Sentences must finish with an normal character
        p_ans2 = regex.compile(r"[^\w\,\.\:\?\%]*$", regex.MULTILINE)
        text = regex.sub(p_ans2, "", text)

        # Fix questions (order is important, needs to be after the answers)
        p_q0 = regex.compile(r"^([^\-\+a-zA-Z]*?)(\d+)", regex.MULTILINE)
        text = regex.sub(p_q0, r"\2", text)

        # Fix questions (order is important, needs to be after the answers)
        p_q0 = regex.compile(r'^(\d+)\W +(?=[A-Z\¿]+)', regex.MULTILINE)
        text = regex.sub(p_q0, r"\1. ", text)

        # To ease debugging (and for the below code)
        add_breaklines = regex.compile(r"^(\d+)", regex.MULTILINE)
        text = regex.sub(add_breaklines, r"\n\n\1", text)

        # Fix pages numbers
        p_gen0 = regex.compile(r"\n\n\d+\n", regex.MULTILINE)
        text = regex.sub(p_gen0, r"\n\n", text)

    return text


def get_block_id(block, is_question):
    block = block.replace('\n', ' ')  # Remove break lines (this regex has problems with it)

    ID_RGX = RGX_QUESTION if is_question else RGX_ANSWER
    pattern = regex.compile(fr"^({ID_RGX})({RGX_SPLITTER}?)(.*)")
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


def preprocess_questions_block(text, single_line=False, length_thres=30):
    if single_line:
        new_raw_questions = text.split("\n\n")
        new_raw_questions = [q.strip() for q in new_raw_questions if len(q.strip()) > length_thres]
    else:
        # Detect start of question
        # pattern = regex.compile(fr"(?<={RGX_QUESTION})([\t ]+)(?=[¿]+)", regex.MULTILINE)
        # text = regex.sub(pattern, r") ", text)
        #
        # # Detect end of question
        # rgx_fix_question = regex.compile(fr"(?<={RGX_QUESTION})([\t ]+)(.*)(?=[?:]$|\.\.\.$)", regex.MULTILINE)
        # text = regex.sub(rgx_fix_question, r") \2", text)

        # Split block of questions
        pattern = regex.compile(fr"({RGX_QUESTION})({RGX_SPLITTER}.*$)", regex.MULTILINE)
        text = regex.sub(pattern, rf"{DELIMITER}\1\2", text)
        raw_questions = text.split(DELIMITER)
        raw_questions = raw_questions[1:] if raw_questions else []  # Ignore first chunk (delimiter)

        # Look potential answers detected as questions => 12a, 23.3abu
        pattern_semians = regex.compile(fr"({RGX_ANSWER})", regex.MULTILINE)

        # Join short questions
        new_raw_questions = []
        for i, q in enumerate(raw_questions):
            q = q.strip()
            q_id, content = get_block_id(q, is_question=True)

            if regex.match(pattern_semians, q):  # 6.1a, 5.3b
                last_idx = len(new_raw_questions) - 1
                new_raw_questions[last_idx] += f"\n{q}"
            elif i > 0 and len(content) < length_thres:  # eg.: 50.000
                # Block too short.
                last_idx = len(new_raw_questions) - 1
                new_raw_questions[last_idx] += f"\n{q}"

                # Print action
                print(f"\t- [WARNING] Question too short. Inferred as answer chunk [chunk: '{q_summary(('###', q))}']")
            else:
                new_raw_questions.append(q)

    return new_raw_questions


def split_id_from_text(item, is_question):
    b_id, content = get_block_id(item, is_question)
    # Remove punctuation and whispaces except last character
    content_clean = regex.sub(r"^([\p{posix_punct}\s]*)(?=[\p{posix_punct}])", '', content)
    # Remove the rest of the punctuation except if it is a set of special character
    content_clean = regex.sub(r"^([\p{posix_punct}\s]*)(?=[\-\+\¿¡\"\'<>=]|>=|<=|==|\p{Latin})", '', content_clean)
    # Remove minus and pluses if it's not a number
    content_clean = regex.sub(r"^([\-\+]*)(?! *\d)", '', content_clean)  # Remove hyphens
    return b_id, content_clean


def preprocess_answers_block(text, single_line=False, num_expected_answers=None):
    # Get blocks
    raw_blocks = text.split('\n')
    raw_blocks = [b for b in raw_blocks if b.strip()]

    if single_line:  # auto
        if len(raw_blocks) > num_expected_answers + 1 or len(raw_blocks) > 8:
            print(f"\t- [WARNING] Too many answers ({len(raw_blocks)-1}). Skipping question [Q: {q_summary(('###', text))}]")
            return None
    else:  # auto
        pattern_ans = regex.compile(fr"({RGX_ANSWER})({RGX_SPLITTER}.*$)", regex.MULTILINE)

        # Check if the answers contains IDs "a) b) c)..."
        # Add them if there is none answer id
        if num_expected_answers and num_expected_answers+1 == len(raw_blocks):
            for i, item in enumerate(raw_blocks[1:]):
                match = regex.match(pattern_ans, item)
                if not match:
                    raw_blocks[i+1] = f"{string.ascii_lowercase[i]}) {item}"

        # Join text
        text = "\n".join(raw_blocks)

        # Detect start of answer
        # pattern_space = regex.compile(fr"(?<={RGX_ANSWER})(\. ?)(?=[\s\S])", regex.MULTILINE)
        # text = regex.sub(pattern_space, r") ", text)

        # Split answers
        stext = regex.sub(pattern_ans, rf"{DELIMITER}\1\2", text)
        raw_blocks = stext.split(DELIMITER)

    # Remove hyphens excepts if it's a number
    blocks_cleaned = []
    for i, b in enumerate(raw_blocks):
        b_id, content = split_id_from_text(b, is_question=bool(i == 0))
        if content.strip():
            blocks_cleaned.append((b_id, content))
    return blocks_cleaned


def normalize_question(text, sentence_case=True):
    # Remove space before quotation mark or colons
    text = regex.sub(r"([\s,;:\-\.\?]*)([\?:])(\s*)$", r"\2", text)

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

    # Remove space before/after a parentheses, quotation mark, etc
    text = regex.sub(r"(?<=[\(\[\{\¿\¡]+)(\s+)", '', text)
    text = regex.sub(r"(\s+)(?=[\)\]\}\?\!\,\.]+)", '', text)

    # Metric rules (remove ampere "a" to avoid problems)
    rgx_metrics = regex.compile(r"(?<=\d+)(\s*)(?=(K|H|D|Da|d|c|m)?(m|s|g|hz|w|v|k|t|min|h|n|Pa|bar)(2|3|²|³)?(?!\p{Latin}))", regex.IGNORECASE|regex.MULTILINE)
    text = regex.sub(rgx_metrics, '', text)

    # Number signs
    rgx_num_signs = regex.compile(r"(?<=\+|\-)(\s*)(?=\d+)", regex.IGNORECASE | regex.MULTILINE)
    text = regex.sub(rgx_num_signs, '', text)

    # Other number signs (>, <, >=, <=)
    rgx_percentage = regex.compile(r"(?<=<|<=|>|>=)(\s*)(?=[\+|\-]?\d+)", regex.IGNORECASE | regex.MULTILINE)
    text = regex.sub(rgx_percentage, r'', text)

    # Percentage
    rgx_percentage = regex.compile(r"(\d+) *%", regex.IGNORECASE | regex.MULTILINE)
    text = regex.sub(rgx_percentage, r'\1%', text)

    # Temperature 1
    rgx_temp = regex.compile(r"(\d+) *º *([CKF])", regex.IGNORECASE|regex.MULTILINE)
    text = regex.sub(rgx_temp, r'\1º\2', text)

    # Temperature 2
    rgx_temp = regex.compile(r" +T *ª", regex.MULTILINE)
    text = regex.sub(rgx_temp, r' Tª', text)
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
        q_id = question[0]

        # Look for collitions
        if q_id not in quiz:
            quiz[q_id] = {
                'id': question[0],
                'question': question[1],
                'answers': [ans[1] for ans in answers],
                'correct_answer': None
            }
        else:
            print(f"\t- [WARNING] Question ID collition. [Q: {q_summary(question)}")

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


def parse_quiz(input_dir, output_dir, token_answer=None, num_answers=None, mode="auto",
               save_files=False, *args, **kwargs):
    print(f'##############################################################')
    print(f'### QUIZ PARSER')
    print(f'##############################################################\n')

    # Get files
    files = utils.get_files(input_dir, extensions={'txt'})

    # Get blacklist
    blacklist = reader.read_blacklist(os.path.join(output_dir, "blacklist.txt"))

    # Create quizzes folder
    quizzes_dir = os.path.join(output_dir, "quizzes/json")
    utils.create_folder(quizzes_dir, empty_folder=True) if save_files else None

    # Create txt preprocessed
    preprocessed_dir = kwargs.get("save_txt_preprocessed")
    if preprocessed_dir:
        preprocessed_dir = os.path.join(output_dir, "txt_preprocessed")
        utils.create_folder(preprocessed_dir, empty_folder=True) if save_files else None

    # Check answer token
    if token_answer and utils.has_regex(token_answer):
        print("\t- [INFO] Your answer token contains regular expressions. Regex knowledge is required.")

    # Parse exams
    quizzes = []
    total_questions = 0
    total_answers = 0
    for i, filename in enumerate(files, 1):
        tail, basedir = utils.get_tail(filename)
        fname, ext = utils.get_fname(filename)

        print("")
        print(f'==============================================================')
        print(f'[INFO] ({i}/{len(files)}) Parsing quiz: "{tail}"')
        print(f'==============================================================')

        # Read file
        txt_file = reader.read_txt(filename)

        # Save preprocessed
        savepath_preprocessed = os.path.join(preprocessed_dir, f"{tail}.txt") if preprocessed_dir else None

        # Parse txt quiz
        answer_fname = regex.sub(r"\.\w+\.\w+$", "", tail)
        answers_file = os.path.join(output_dir, f"txt_selector/{answer_fname}.html_selected.txt")
        quiz = parse_quiz_txt(txt_file, blacklist, token_answer, num_answers, mode, answers_file, savepath_preprocessed, *args, **kwargs)

        # Keep count of total questions
        solutions = sum([1 for q_id, q in quiz.items() if q.get('correct_answer') is not None])
        total_answers += solutions
        total_questions += len(quiz)
        quizzes.append((quiz, filename))

        # Show info
        if len(quiz) == 0:
            print(f"\t- [WARNING] No quizzes were found ({tail})")
        print(f"\t- [INFO] Parsing done! {len(quiz)} questions were found; {solutions} with solutions. ({tail})")

        # Save quizzes
        if save_files:
            print(f"\t- [INFO] Saving json... ({fname}.json)")
            reader.save_json(quiz, os.path.join(quizzes_dir, f"{fname}.json"))

    print("")
    print("--------------------------------------------------------------")
    print("SUMMARY")
    print("--------------------------------------------------------------")
    print(f"- [INFO] Documents parsed: {len(quizzes)}")
    print(f"- [INFO] Questions found: {total_questions} (with solutions: {total_answers})")
    print("--------------------------------------------------------------\n\n")
    return quizzes


def get_config(file, max_lines=10):
    params = {}
    last_line=0
    sfile = file.split('\n')
    for i, l in enumerate(sfile):
        # Normalize (just in case)
        l = l.lower().strip()

        # Look for special chars
        if l.startswith("#"):
            l = l[1:]  # remove first character
            l = l.split('=')
            if l and len(l) == 2:
                last_line = i
                key, value = l
                key = key.replace('-', '_')
                value = int(value) if value.isnumeric() else value  # Cast integers

                # Add param
                params[key] = value

        # Break if there is no config
        if last_line != i:
            break

    # Split file from config
    text = '\n'.join(sfile[last_line+1:])
    return text, params


def parse_quiz_txt(text, blacklist=None, token_answer=None, num_answers=None, mode="auto", answers_file=None,
                   savepath_preprocessed=None, *args, **kwargs):
    # Look for user params and override
    text, config = get_config(text)
    if config:
        print("\t- [INFO] File-specific params detected. Overriding user input.")
        num_answers = config.pop("num_answers", num_answers)
        mode = config.pop("mode", mode)
        kwargs.update(config)

    # Preprocess text
    text = preprocess_text(text, blacklist, mode, from_ocr=kwargs.get("from_ocr"))

    # Save preprocessed
    if savepath_preprocessed:
        reader.save_txt(text, savepath_preprocessed)

    # Split file (questions / answers)
    txt_questions, txt_answers = text, None
    if token_answer:
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

    # Find answers (txt
    solutions_txt = parse_solutions(txt_answers, num_answers, *args, **kwargs)

    # Find answers (selector)
    solutions_sel = []
    if answers_file and os.path.exists(answers_file):
        print("\t- [INFO] Trying to find solutions using a txt selector file...")
        # If we use the blacklist file, we could delete parts of a question
        solutions_sel = find_answers_selector(questions, answers_file, None, mode)

    # Merge solutions
    # Although there can be collitions, they should be exclusive, unless manual editing (priority)
    # solutions_txt = {k: v for k, v in solutions_txt}
    # solutions_sel = {k: v for k, v in solutions_sel}
    # solutions = solutions_sel
    # solutions.update(solutions_sel)  # The solutions from the txt have priority
    solutions = solutions_txt + solutions_sel

    # Notify if solutions where found
    if not solutions:
        print("\t- [WARNING] No solutions were found")

    # Check number of questions and answers
    if solutions and len(questions) != len(solutions):
        # Get missing questions/answers
        q_ids = set([str(q[0][0]) for q in questions])
        sol_ids = set([str(sol[0]) for sol in solutions])

        # Get differences
        missing_questions = list(sol_ids - q_ids)
        missing_ans = list(q_ids - sol_ids)

        # Sort IDs
        missing_questions.sort(key=utils.tokenize)
        missing_ans.sort(key=utils.tokenize)

        # Convert to string (prettify)
        missing_questions_str = ", ".join(missing_questions)
        missing_ans_str = ", ".join(missing_ans)

        print(f"\t- [WARNING] The number of questions ({len(questions)}) and solutions ({len(solutions)}) do not match")
        print(f"\t\t- Questions missing ({len(missing_questions)}): [{missing_questions_str}]")
        print(f"\t\t- Questions with missing answers ({len(missing_ans)}): [{missing_ans_str}]")

    # Build quiz
    quiz = build_quiz(questions, solutions)
    return quiz


def parse_questions(txt, num_expected_answers=None, mode="auto", *args, **kwargs):
    if mode == "auto":
        return parse_questions_auto(txt, num_expected_answers, single_line=False, **kwargs)
    elif mode == "single-line":
        return parse_questions_auto(txt, num_expected_answers, single_line=True , **kwargs)
    else:
        raise ValueError(f"Unknown question mode: '{mode}'")


def parse_questions_auto(text, num_expected_answers, single_line, *args, **kwargs):
    questions = []

    # Split questions
    raw_questions = preprocess_questions_block(text, single_line)

    # Parse questions
    for i, raw_question in enumerate(raw_questions, 1):
        # Split block of answers
        q_blocks = preprocess_answers_block(raw_question, single_line, num_expected_answers)
        if q_blocks:
            # Infer question blocks
            q_blocks = infer_question_blocks(q_blocks, single_line, num_expected_answers, *args, **kwargs)

            if q_blocks:
                # Normalize question items
                question, answers = parse_normalize_question(q_blocks, suggested_id=i)
                questions.append([question, answers])
    return questions


def infer_question_blocks(blocks, single_line, num_expected_answers, *args, **kwargs):
    # User variables
    infer_question = kwargs.get("infer_question", True)
    skip_on_error = kwargs.get("skip_on_error", False)
    ignore_question_key = kwargs.get("ignore_question_key", False)

    # Remove empty lines
    q_blocks = []
    for b_id, content in blocks:
        content = content.strip()
        q_blocks.append([b_id, content]) if content else None

    # Infer questions/answers
    # Join questions and answers if needed (IDs must be already normalized)
    if single_line or not infer_question:
        new_blocks = q_blocks
        new_blocks[0][0] = None if ignore_question_key else new_blocks[0][0]
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


def parse_solutions(txt, num_expected_answers=None, letter2num=True, *args, **kwargs):
    answers = []

    # Check if there is something in the txt
    if not txt:
        return answers

    # Define regex
    rgx_solutions = regex.compile(r'\b(\d+[\d\.]*?)[\W\s]*([a-zA-Z]{1})(?!\w)', regex.MULTILINE)
    solutions = regex.findall(rgx_solutions, txt)

    for i, (id_question, id_answer) in enumerate(solutions):
        # Format question IDs
        id_question = id_question.lower().strip()
        id_question = regex.sub(r"\.*$", "", id_question)

        id_answer = id_answer.lower().strip()
        id_answer = regex.sub(r"\.*$", "", id_answer)

        # Check if the correct answer is in range (a,b,c,d)
        id_answer_num = string.ascii_lowercase.index(id_answer)
        if num_expected_answers and id_answer_num >= num_expected_answers:
            a_ids = string.ascii_lowercase
            range_str = f"{a_ids[0]}-{a_ids[num_expected_answers-1]}"
            print(f"\t- [WARNING] Skipping answer. The correct answer '{id_answer}' is not in the range of "
                  f"possible answers ({range_str})")
            continue

        # Letter to number (a => 0, b => 1, c => 2,...)
        id_answer = id_answer_num if letter2num else id_answer

        # Add questions
        answers.append([id_question, id_answer])
    return answers


def normalize_chunk(text, remove_id=False):
    text = normalize_answer(text)
    text = utils.remove_whitespace(text)
    text = text.lower()
    if remove_id:
        b_id, text = get_block_id(text, is_question=False)  # Remove answer id
    return text.strip()


def find_answers_selector(questions, answers_file, blacklist, mode, thres1=0.90, thres2=0.75, max_jump=10):
    text = None

    # Check if file exists
    try:
        with open(answers_file, 'r', encoding='utf8') as f:
            text = f.read()
    except IOError as e:
        return None

    # Preprocess lines
    text = preprocess_text(text, blacklist, mode)

    lines = []
    for bold_text in text.split('\n'):
        # Normalize selector
        # bold_id, bold_text = get_block_id(bold_text, is_question=True)

        # Remove question
        if bold_text.strip():
            bold_text = normalize_chunk(bold_text, remove_id=True)
            lines.append(bold_text)

    correct_answers = []
    previous_line = 0
    for q, answers in questions:
        # Find question with this answer
        line_ans_score = []
        skip_question = False
        for li, bold_text in enumerate(lines[previous_line:]):
            # Walk through question answers to find the bold text
            scores = []
            for i, (ans_idx, ans_text) in enumerate(answers):
                # This answers have no IDs, and we don't want to remove parts of the answer
                ans_text = normalize_chunk(ans_text, remove_id=False)

                score = utils.fuzzy_text_similarity(ans_text, bold_text)
                scores.append(score)

            # Get answer with maximum score for this bold line
            ans_idx, ans_score = max(enumerate(scores), key=itemgetter(1))
            line_ans_score.append((ans_idx, ans_score, bold_text))

            # Speed-up!!! Set checkpoint on high accuracy.
            # I presume that answers are sorted! Try to use the same correct answer twice
            #  e.g.: 3) b-cheese...... 59) d-cheese)
            if ans_score > thres1:
                previous_line += li
                break

            # If an answer is missing, we don't go to look to further
            if li >= max_jump and previous_line != 0:
                skip_question = True
                break

        # Skip question
        if skip_question:
            print(f"\t [WARNING] Skipping answer (might be missing). Max jump exceeded ({max_jump} lines). [Q: '{q_summary(q)}']")
            continue

        # Get max score
        ans_idx, score, bold_text = max(line_ans_score, key=itemgetter(1))
        if score > thres2:
            correct_answers.append([q[0], ans_idx])
        else:
            print(f"\t- [INFO] Answer discarted (prob.: {int(score*100)}%) [B: '{bold_text[:50]}'; A: '{q_summary(answers[ans_idx])}'; Q: '{q_summary(q)}';]")
    return correct_answers
