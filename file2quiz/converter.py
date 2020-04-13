import os
import shutil
import string

from file2quiz import utils, reader


def convert_quiz(input_dir, output_dir, file_format, save_files=False, show_answers=True):
    # Get files
    files = utils.get_files(input_dir, extensions={'.json'})

    # Create quizzes folder
    convert_dir = os.path.join(output_dir, file_format)
    utils.create_folder(convert_dir) if save_files else None

    # Set format
    FILE_FORMATS = {"text": "txt", "anki": "txt"}
    file_format = str(file_format).lower().strip().replace('.', '')  # parse formats
    output_ext = FILE_FORMATS.get(file_format, None)

    # Fallback for unknown extension
    if output_ext is None:
        file_format = "text"
        print(f'\t- [ERROR] No method to save "{output_ext}" files (fallback to "txt")')

    # Convert quizzes
    quizzes = []
    for i, filename in enumerate(files, 1):
        tail, basedir = utils.get_tail(filename)

        # Read file
        quiz = reader.read_json(filename)

        try:
            quiz = convert_quiz_json(quiz, file_format, show_answers)
        except ValueError as e:
            print(f'\t- [ERROR] {e}. Skipping quiz "{tail}"')
            continue

        # Build quiz
        quizzes.append((quiz, filename))

        # Show info
        if len(quiz) == 0:
            print(f"\t- [WARNING] No quiz were found ({tail})")
        print(f"\t- [INFO] Converting to '{file_format}' done! ({tail})")

    # Save quizzes
    if save_files:
        for i, (quiz, filename) in enumerate(quizzes):
            fname, ext = utils.get_fname(filename)
            reader.save_txt(quiz, os.path.join(convert_dir, f"{fname}.{output_ext}"))

    # Check result
    if not quizzes:
        print("\t- [WARNING] No quiz was converted successfully")

    return quizzes


def convert_quiz_json(quiz, file_format, show_answers=True):
    # Select format
    if file_format == "anki":
        return quiz2anki(quiz)
    else:  # Fallback to txt
        return quiz2txt(quiz, show_answers)


def pdf2image(filename, savepath, dpi=300, img_format="tiff"):
    # This requires: ImageMagick
    cmd = f'convert -density {dpi} "{filename}" -depth 8 -strip -background white -alpha off "{savepath}/page-%0d.{img_format}"'
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
    keys = sorted(quiz.keys(), key=utils.tokenize)
    for i, id_question in enumerate(keys):
        question = quiz[id_question]

        # Check if the there is a correct answer
        if question.get('correct_answer') is None:
            raise ValueError("No correct answer was given.")

        # Format fields
        fields = ["{}. {}".format(id_question, question['question']), str(int(question['correct_answer'])+1)] + question['answers']
        text += "{}\n".format("\t".join(fields))
    return text.strip()


def quiz2txt(quiz, show_answers):
    txt = ""

    # Sort questions by key
    keys = sorted(quiz.keys(), key=utils.tokenize)
    for i, id_question in enumerate(keys):
        question = quiz[id_question]

        # Format question
        txt += "{}. {}\n".format(id_question, question['question'])

        # Format answers
        for j, ans in enumerate(question['answers']):
            is_correct = "*" if show_answers and j == question.get("correct_answer") else ""
            txt += "{}{}) {}\n".format(is_correct, string.ascii_lowercase[j].lower(), ans)
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


def _pdf2word(filename, savepath, word_client=None):
    import win32com.client
    import pywintypes

    if not word_client:
        # Load word client
        word_client = win32com.client.Dispatch("Word.Application")
        word_client.visible = 0

    try:
        # Open word file
        wb = word_client.Documents.Open(filename)

        # File format for .docx
        # https://docs.microsoft.com/en-us/office/vba/api/word.wdsaveformat
        wb.SaveAs2(savepath, FileFormat=16)
        wb.Close()
    except pywintypes.com_error as e:
        print(f"[ERROR] There was an error converting the PDF file to DOCX. Skipping file. ({e})")


def pdf2word(input_dir, output_dir):
    import win32com.client

    # Get files
    files = utils.get_files(input_dir, extensions={".pdf"})

    # Create output dir
    output_dir = os.path.join(output_dir, "docx-word")
    utils.create_folder(output_dir)

    # Load word client
    word_client = win32com.client.Dispatch("Word.Application")
    word_client.visible = 0

    # Walk through files
    for i, filename in enumerate(files, 1):
        # Parse path
        tail, basedir = utils.get_tail(filename)
        fname, ext = utils.get_fname(filename)
        print(f"#{i}. Converting *.pdf to *.docx ({tail})")

        # Create save path
        savepath = os.path.abspath(os.path.join(output_dir, f"{fname}.docx"))

        # Convert pdf
        _pdf2word(filename, savepath, word_client)
