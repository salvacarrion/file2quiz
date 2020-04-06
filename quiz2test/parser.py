import os
import re
import shutil
import regex
import json
import string

digits = re.compile(r'(\d+)')
letters = re.compile(r'([a-zA-Z]+)')
rgx_block_question = re.compile(r'(^\d+[ \t]*[\.\-\)\t]+)([\s\S]*?)(?=^\d+[ \t]*[\.\-\)\t]+[^,;])', re.MULTILINE)
rgx_question = re.compile(r'(^\d+[ \t]*[\.\-\)\t]+)([\s\S]*?)(?=^[a-zA-Z][ \t]*(?:\)|(?:\.?\-)))', re.MULTILINE)
rgx_answer = re.compile(r'(^[a-zA-Z][ \t]*(?:\)|(?:\.?\-)))([\s\S]*?)(?=^[a-zA-Z][ \t]*(?:\)|(?:\.?\-)))', re.MULTILINE)
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
        .replace("\ufeff", '')
    text = re.sub(r'[ ]{2,}', ' ', text)  # two whitespaces

    # Only latin characters
    text = regex.sub('\p{Latin}\p{posix_punct}]+', '', text)

    lines = []
    for l in text.split('\n'):
        lines.append(l) if l else None
    text = "\n".join(lines)

    return text


def parse_questions(txt):
    questions = []

    # Split block of questions
    txt += '\n\n0. blabla'  # trick for regex
    m = rgx_block_question.findall(txt)
    for num, question in m:
        # Get ID question
        id_question = str(digits.search(num)[0]).strip().lower()

        # Get question
        block = num + question + "\n\nz) blablabla"  # trick for regex
        question = rgx_question.findall(block)[0][1].strip()

        # Get answers
        answers = [ans[1].strip() for ans in rgx_answer.findall(block)]

        # Add questions
        questions.append([id_question, question, answers])
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


def print_questions(questions, file):
    letters = "abcdefghijklmnopqrstuvwxyz"

    counter = 0
    with open(file, 'w') as f:
        for i, q in enumerate(questions, 1):
            question, answers = q
            if len(answers) >= 2:
                counter += 1

                # Write question
                f.write(f"{counter}. {question}\n")

                # Write answers
                for j, ans in enumerate(answers, 0):
                    f.write(f"{letters[j%len(letters)]}) {ans}\n")

                # Write additional lines
                f.write('\n\n')
