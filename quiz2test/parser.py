import re
import regex
import string

from quiz2test.utils import *

digits = re.compile(r'(\d+)')
letters = re.compile(r'([a-zA-Z]+)')

rgx_block_question = re.compile(r'(^\d+[\s]*[\.\-\)\t]+[\S\s]*?)(?=^\d+[\s]*[\.\-\)\t]+[\S\s]*?)', re.MULTILINE)  # question to question
rgx_question = re.compile(r'^(\d+)[\s]*[\.\-\)\s]+([\S\s]*?)(?=^[a-zA-Z]{1}[\s]*[\.\-\)\t]+[\S\s]*?$)', re.MULTILINE)  # question to answer
rgx_question_single = re.compile(r'^(\d+)[\s]*[\.\-\)\s]+([\S\s]*?)$')
rgx_answer = re.compile(r'^([a-zA-Z]{1})[\s]*[\.\-\)\t]+([\S\s]*?)(?=^.*[\s]*[\.\-\)\t]+[\S\s]*?)', re.MULTILINE)  # answer to answer
rgx_answer_single = re.compile(r'^([a-zA-Z]{1})[\s]*[\.\-\)\t]+([\S\s]*?)$')
rgx_block_correct_answer = re.compile(r'(^\d+\D*)', re.MULTILINE)


def parse_exams(input_dir, output_dir, answer_token=None, banned_file=None, single_line=False, num_answers=None):
    # Get files
    files = check_input(input_dir)

    # Check output
    check_output(output_dir)

    # Get banned words
    banned_words = get_banned_words(banned_file)

    # Parse exams
    for i, filename in enumerate(files, 1):
        # Read file
        txt_questions, txt_answers = read_file(filename, banned_words, answer_token)

        # Parse questions and correct answers
        questions = parse_questions(txt_questions, single_line, num_answers)
        correct_answers = parse_correct_answers(txt_answers, letter2num=True) if answer_token else None

        # Check number of questions and answers
        if correct_answers and len(questions) != len(correct_answers):
            raise IOError("The number of questions ({}) and correct answers ({}) does not match"
                          .format(len(questions), len(correct_answers)))

        # Build quiz
        quiz = build_quiz(questions, correct_answers)

        # Save file
        fname, extension = os.path.splitext(os.path.basename(filename))
        savepath = os.path.join(output_dir, "{}.json".format(fname))
        save_quiz(quiz, savepath)
        print("{}. Quiz '{}' saved!".format(i, fname))


def read_file(filename, banned_words, answer_token):
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
    txt = clean_text(txt, banned_words)

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
            print("[WARNING] No answer section found. Check delimiter")
    return txt_questions.strip(), txt_answers.strip()


def clean_text(text, banned_words=None, only_latin=False):
    if banned_words is None:
        banned_words = []

    # Remove unwanted characters
    text = text \
        .replace("\n.", ".") \
        .replace(" .", ".") \
        .replace(" º", "º") \
        .replace('“', '').replace('”', '').replace("'", '') \
        .replace("€)", 'c)') \
        .replace("``", '\"') \
        .replace("´´", '\"') \
        .replace("\ufeff", '')
    text = re.sub(r"[ ]{2,}", ' ', text)  # two whitespaces

    # Remove banned words
    banned_regex = "|".join(banned_words)
    text = re.sub(r"{}".format(banned_regex), '', text)

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


def remove_whitespace(text):
    text = re.sub(r"\s", " ", text)
    text = re.sub(r'[ ]{2,}', ' ', text)  # two whitespaces
    return text.strip()


def parse_questions(txt, single_line, num_answers=None):
    questions = []

    # Split block of questions
    txt += '\n\n0. blabla'  # trick for regex
    question_blocks = rgx_block_question.findall(txt)
    for i, q_block in enumerate(question_blocks):

        if single_line:
            lines = q_block.split("\n")
            id_question, question = (remove_whitespace(v) for v in rgx_question_single.match(lines[0]).groups())
            answers = [remove_whitespace(ans) for ans in lines[1:]]
        else:
            q_block += "\n\nz) blablabal"  # trick for regex
            id_question, question = (remove_whitespace(v) for v in rgx_question.findall(q_block)[0])
            answers = [remove_whitespace(ans[1]) for ans in rgx_answer.findall(q_block)]

        # Review answers
        answers = [ans for ans in answers if ans]  # Add non-empty answers

        # Check number of answers
        if num_answers and len(answers) != num_answers:
            raise IOError("The number of answers expected ({}) does not match the number of answers found ({}). "
                          "Question: #{}".format(num_answers, len(answers), id_question))
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
