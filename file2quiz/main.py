import os
import argparse
import file2quiz


def main():
    parser = argparse.ArgumentParser()

    # Mandatory parameters
    CHOICES = ["file2quiz", "file2text", "text2quiz", "quiz2text", "quiz2anki"]
    parser.add_argument('--action', help="Actions to perform", choices=CHOICES)
    parser.add_argument('--input', help="Input file or directory", default=None)
    parser.add_argument('--output', help="Output file or directory", default=None)

    # Quizzes
    QUESTION_MODES = ["auto", "single-line"]
    parser.add_argument('--mode', help="Mode used to detect questions", choices=QUESTION_MODES, default=QUESTION_MODES[0])
    parser.add_argument('--blacklist', help="Blacklist file with the excluded words or patterns (regex)", default=None)
    parser.add_argument('--token-answer', help="(regex) Token used to split the file between questions and answers", default=None)
    parser.add_argument('--show-answers', help="Show correct answer", default=False, action="store_true")
    parser.add_argument('--num-answers', help="Number of answers per question", default=None, type=int)
    parser.add_argument('--save-txt', help="Save quizzes in txt", default=False, action="store_true")

    # Tesseract
    parser.add_argument('--use-ocr', help="Use an OCR to extract text from the PDFs", default=False, type=bool)
    parser.add_argument('--lang', help="[Tesseract] Specify language(s) used for OCR", default="eng")
    parser.add_argument('--dpi', help="[Tesseract] Specify DPI for input image", default=300, type=int)
    parser.add_argument('--psm', help="[Tesseract] Specify page segmentation mode", default=3, type=int)
    parser.add_argument('--oem', help="[Tesseract] Specify OCR Engine mode", default=3, type=int)

    args = parser.parse_args()

    # Minor format
    args.action = args.action.lower().strip() if isinstance(args.action, str) else None
    if args.action == "file2text":
        # Set default paths
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "raw"))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.getcwd()))

        # Extract text
        file2quiz.extract_text(input_dir, output_dir, args.use_ocr, args.lang, args.dpi, args.psm, args.oem,
                               save_files=True)
        print("Done!")

    elif args.action in {"file2quiz", "text2quiz"}:
        # Set default paths
        input_folder = "raw" if args.action == "file2quiz" else "text2quiz"
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), input_folder))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.getcwd()))
        blacklist = os.path.abspath(args.output) if args.blacklist else os.path.abspath(os.path.join(os.getcwd(), "blacklist.txt"))

        # Parse raw files
        if args.action == "file2quiz":
            file2quiz.extract_text(input_dir, output_dir, args.use_ocr, args.lang, args.dpi, args.psm, args.oem,
                                   save_files=True)

        # Parse quizzes
        input_dir = os.path.join(output_dir, "txt")
        file2quiz.parse_quiz(input_dir, output_dir, blacklist, args.token_answer, args.num_answers,
                             args.mode, save_files=True)

        # Convert to txt
        if args.save_txt:
            input_dir = os.path.join(output_dir, "quizzes/json")
            output_dir = os.path.abspath(os.path.join(output_dir, "quizzes"))
            file2quiz.convert_quiz(input_dir, output_dir, file_format="text", save_files=True,
                                   show_answers=args.show_answers)

        print("Done!")

    elif args.action in {"quiz2text", "quiz2anki"}:
        # Set default paths
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "quizzes/json"))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.getcwd(), "quizzes"))

        # Select format
        if args.action == "quiz2anki":
            file_format = "anki"
        else:
            file_format = "text"
        file2quiz.convert_quiz(input_dir, output_dir, file_format=file_format, save_files=True,
                               show_answers=args.show_answers)
        print("Done!")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
