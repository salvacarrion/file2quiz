import os
import shutil

from quiz2test.parser import get_files, load_quiz


def convert2anki(input_dir, output_dir):
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
    files = get_files(input_dir, extensions={'json'})

    # Check files
    if not files:
        raise IOError("Not files where found at: {}".format(input_dir))

    # Parse files
    for i, filename in enumerate(files, 1):
        # Load quiz
        quiz = load_quiz(filename)

        # Load text
        text = quiz2anki(quiz)

        # Save file
        fname, extension = os.path.splitext(os.path.basename(filename))
        savepath = os.path.join(output_dir, "{}.txt".format(fname))
        save_text(text, savepath)
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


def save_text(text, filename):
    with open(filename, 'w', encoding="utf8") as f:
        f.write(text)
