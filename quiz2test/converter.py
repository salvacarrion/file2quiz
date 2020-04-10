import os
import shutil
import string

from quiz2test import utils, reader


def convert_quiz(input_dir, output_dir, file_format, save_files=False):
    # Get files
    files = utils.get_files(input_dir, extensions={'.json'})

    # Create quizzes folder
    convert_dir = os.path.join(output_dir, file_format)
    utils.create_folder(convert_dir) if save_files else None

    # Set format
    formats_table = {"anki": "txt"}
    format_extension = formats_table.get(file_format)

    # Convert quizzes
    quizzes = []
    for i, filename in enumerate(files, 1):

        # Read file
        quiz = reader.read_json(filename)

        try:
            # Select format
            if file_format == "anki":
                quiz = quiz2anki(quiz)
            else:
                raise ValueError(f"Unknown format: {file_format}")
        except ValueError as e:
            print(f"[ERROR] {e}. Skipping quiz")
            continue

        # Build quiz
        quizzes.append((quiz, filename))

    # Save quizzes
    if save_files:
        for i, (quiz, filename) in enumerate(quizzes):
            fname, ext = utils.get_fname(filename)
            reader.save_json(quiz, os.path.join(convert_dir, f"{fname}.{format_extension}"))

    # Check result
    if not quizzes:
        print("[WARNING] No quiz was converted successfully")

    return quizzes


def pdf2image(filename, savepath, dpi=300, format="jpg"):
    # This requires: ImageMagick
    cmd = f'convert -density {dpi} "{filename}" -depth 8 -strip -background white -alpha off "{savepath}/page-%0d.{format}"'
    os.system(cmd)


def image2text(filename, savepath, lang="eng", dpi=300, psm=3, oem=3):
    # This requires: Tesseract
    # Tesseract needs the save path without the extensions
    basedir, tail = os.path.split(savepath)
    fname, ext = os.path.splitext(tail)

    # Run command
    cmd = f'tesseract "{filename}" "{basedir}/{fname}" -l {lang} --dpi {dpi} --psm {psm} --oem {oem}'
    os.system(cmd)


def quiz2anki(quiz):
    text = ""

    # Sort questions by key
    keys = sorted(quiz.keys(), key=lambda x: int(x))
    for i, id_question in enumerate(keys):
        question = quiz[id_question]

        # Check if the there is a correct answer
        if question.get('correct_answer') is None:
            raise ValueError("No correct answer was given.")

        # Format fields
        fields = ["{}. {}".format(id_question, question['question']), str(int(question['correct_answer'])+1)] + question['answers']
        text += "{}\n".format("\t".join(fields))
    return text.strip()


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


def json2text(path, show_correct):
    texts = []
    files = utils.get_files(path, extensions=".json")
    for filename in files:
        fname, extension = os.path.splitext(os.path.basename(filename))

        # Load quiz and text
        quiz = reader.read_json(filename)
        quiz_txt = quiz2txt(quiz, show_correct)

        texts.append((fname, quiz_txt))
    return texts
