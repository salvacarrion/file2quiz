import os
import string

from file2quiz import utils, reader


def convert_quiz(input_dir, output_dir, file_format, save_files=False, *args, **kwargs):
    print(f'##############################################################')
    print(f'### QUIZ CONVERTER')
    print(f'##############################################################\n')

    # Get files
    files = utils.get_files(input_dir, extensions={'json'})

    # Create quizzes folder
    convert_dir = os.path.join(output_dir, f"quizzes/{file_format}")
    utils.create_folder(convert_dir, empty_folder=True) if save_files else None

    # Set format
    FILE_FORMATS = {"text": "txt", "anki": "txt"}
    file_format = str(file_format).lower().strip().replace('.', '')  # parse formats
    output_ext = FILE_FORMATS.get(file_format, None)

    # Fallback for unknown extension
    if output_ext is None:
        file_format = "text"
        print(f'\t- [ERROR] No method to save "{output_ext}" files (fallback to "txt")')

    # Convert quizzes
    fquizzes = []
    total_questions = 0
    total_answers = 0
    for i, filename in enumerate(files, 1):
        tail, basedir = utils.get_tail(filename)
        fname, ext = utils.get_fname(filename)

        print("")
        print(f'==============================================================')
        print(f'[INFO] ({i}/{len(files)}) Converting quiz to "{file_format}": "{tail}"')
        print(f'==============================================================')

        # Read file
        quiz = reader.read_json(filename)
        solutions = sum([1 for q_id, q in quiz.items() if q.get('correct_answer') is not None])
        total_answers += solutions
        total_questions += len(quiz)

        try:
            fquiz = _convert_quiz(quiz, file_format, *args, **kwargs)
        except ValueError as e:
            print(f'\t- [ERROR] {e}. Skipping quiz "{tail}"')
            continue

        # Add formatted quizzes
        fquizzes.append((fquiz, filename))

        # Show info
        if len(fquiz.strip()) == 0:
            print(f"\t- [WARNING] No quiz were found ({tail})")
        print(f"\t- [INFO] Conversion done! {len(quiz)} questions were found; {solutions} with solutions. ({tail})")

        # Save quizzes
        if save_files:
            print(f"\t- [INFO] Saving file... ({tail}.txt)")
            reader.save_txt(fquiz, os.path.join(convert_dir, f"{fname}.{output_ext}"))

    # Check result
    if not fquizzes:
        print("\t- [WARNING] No quiz was converted successfully")

    print("")
    print("--------------------------------------------------------------")
    print("SUMMARY")
    print("--------------------------------------------------------------")
    print(f"- [INFO] Quizzes converted: {len(fquizzes)}")
    print(f"- [INFO] Questions found: {total_questions} (with solutions: {total_answers})")
    print("--------------------------------------------------------------\n\n")
    return fquizzes


def _convert_quiz(quiz, file_format, *args, **kwargs):
    # Select format
    if file_format == "anki":
        return quiz2anki(quiz)
    else:  # Fallback to txt
        return quiz2txt(quiz, *args, **kwargs)


def pdf2image(filename, savepath, dpi=300, img_format="tiff", **kwargs):
    # This requires: ImageMagick
    cmd = f'convert -density {dpi} "{filename}" -depth 8 -strip -background white -alpha off "{savepath}/page-%0d.{img_format}"'
    os.system(cmd)


def image2text(filename, savepath, lang="eng", dpi=300, psm=3, oem=3, **kwargs):
    # This requires: Tesseract
    # Tesseract needs the save path without the extensions
    basedir, tail = os.path.split(savepath)
    fname, ext = os.path.splitext(tail)

    # Run command
    #sub_cmds = 'tessedit_char_whitelist="0123456789 abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYñÑçÇáéíóúÁÉíÓÚüÜ()¿?,;.:/-\"\'ºª%-+Ø=<>*"'
    cmd = f'tesseract "{filename}" "{basedir}/{fname}" -l {lang} --dpi {dpi} --psm {psm} --oem {oem} letters' #-c {sub_cmds}
    os.system(cmd)


def quiz2anki(quiz, **kwargs):
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


def quiz2txt(quiz, show_answers, answer_table=False, **kwargs):
    txt = ""
    txt_answers = ""

    # Sort questions by key
    keys = sorted(quiz.keys(), key=utils.tokenize)
    for i, id_question in enumerate(keys):
        question = quiz[id_question]

        # Format question
        txt += "{}. {}\n".format(id_question, question['question'])

        # Format answers
        for j, ans in enumerate(question['answers']):
            marker = ""
            ans_id = string.ascii_lowercase[j].lower()

            # Show correct answer?
            if show_answers:
                if j == question.get("correct_answer"):  # correct answer
                    if answer_table:
                        txt_answers += f"{id_question} - {ans_id}\n"
                    else:
                        marker = "*"
            txt += "{}{}) {}\n".format(marker, ans_id, ans)
        txt += "\n"

    # Add answer table at the end of the file if requested
    if show_answers and answer_table:
        txt += "\n\n\n=========\n\n\n" + txt_answers
    return txt.strip()


def json2text(path, *args, **kwargs):
    texts = []
    files = utils.get_files(path, extensions="json")
    for filename in files:
        fname, extension = os.path.splitext(os.path.basename(filename))

        # Load quiz and text
        quiz = reader.read_json(filename)
        quiz_txt = quiz2txt(quiz, *args, **kwargs)

        texts.append((fname, quiz_txt))
    return texts


def _pdf2word(filename, savepath, word_client=None):
    try:
        import win32com.client
        import pywintypes
    except ImportError as e:
        raise ImportError("'pywin32' missing. You need to install it manually (only Windows): pip install pywin32")

    # Create a Word client if there isn't any
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
        print(f"- [ERROR] There was an error converting the PDF file to DOCX. Skipping file. ({e})")


def pdf2word(input_dir, output_dir):
    try:
        import win32com.client
    except ImportError as e:
        raise ImportError("'pywin32' missing. You need to install it manually (only Windows): pip install pywin32")

    # Get files
    files = utils.get_files(input_dir, extensions={"pdf"})

    # Create output dir
    output_dir = os.path.join(output_dir, "docx-word")
    utils.create_folder(output_dir, empty_folder=True)

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
