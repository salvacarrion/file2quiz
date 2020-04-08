import os
import shutil
import string

from quiz2test import utils


def pdf2image(filename, savepath, dpi=300):
    # This requires: ImageMagick
    cmd = f'convert -density {dpi} "{filename}" -depth 8 -strip -background white -alpha off {savepath}/page-%0d.jpg'
    os.system(cmd)


def image2text(filename, savepath, lang="eng", dpi=300, psm=3, oem=3):
    cmd = f"tesseract {filename} {savepath} -l {lang} --dpi {dpi} --psm {psm} --oem {oem}"
    os.system(cmd)


def convert2anki(input_dir, output_dir):
    # Get files
    files = utils.check_input(input_dir, extensions={"json"})

    # Check output
    utils.create_folder(output_dir)

    # Parse files
    for i, filename in enumerate(files, 1):
        # Load quiz
        quiz = utils.load_quiz(filename)

        # Load text
        text = quiz2anki(quiz)

        # Save file
        fname, extension = os.path.splitext(os.path.basename(filename))
        savepath = os.path.join(output_dir, "{}.txt".format(fname))
        utils.save_text(text, savepath)
        print("{}. Anki '{}' saved!".format(i, fname))


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
    files = utils.check_input(path, extensions="json")
    for filename in files:
        fname, extension = os.path.splitext(os.path.basename(filename))

        # Load quiz and text
        quiz = utils.load_quiz(filename)
        quiz_txt = quiz2txt(quiz, show_correct)

        texts.append((fname, quiz_txt))
    return texts
