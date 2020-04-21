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

    # Extract text
    parser.add_argument('--blacklist', help="Blacklist file with the excluded words or patterns (regex)", default=None)
    parser.add_argument('--extract-bold', help="Extract bold text from the documents", default=False, action="store_true")

    # Quizzes
    QUESTION_MODES = ["auto", "single-line"]
    parser.add_argument('--mode', help="Mode used to detect questions", choices=QUESTION_MODES, default=QUESTION_MODES[0])
    parser.add_argument('--token-answer', help="(regex) Token used to split the file between questions and answers", default=None)
    parser.add_argument('--show-answers', help="Show correct answer", default=False, action="store_true")
    parser.add_argument('--fill-missing-answers', help="Texto used to fill missing answers", default=None)
    parser.add_argument('--num-answers', help="Number of answers per question", default=None, type=int)
    parser.add_argument('--save-txt', help="Save quizzes in txt", default=False, action="store_true")
    parser.add_argument('--answer-table', help="Show correct answer as a table", default=False, action="store_true")

    # Tesseract
    parser.add_argument('--use-ocr', help="Use an OCR to extract text from the PDFs", default=False, type=bool)
    parser.add_argument('--lang', help="[Tesseract] Specify language(s) used for OCR", default="spa")
    parser.add_argument('--dpi', help="[Tesseract] Specify DPI for input image", default=300, type=int)
    parser.add_argument('--psm', help="[Tesseract] Specify page segmentation mode", default=3, type=int)
    parser.add_argument('--oem', help="[Tesseract] Specify OCR Engine mode", default=3, type=int)

    args = parser.parse_args()
    input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd()))
    output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.getcwd()))
    blacklist_path = os.path.abspath(args.blacklist) if args.blacklist else os.path.abspath(os.path.join(os.getcwd(), "blacklist.txt"))

    # Minor format
    args.action = args.action.lower().strip() if isinstance(args.action, str) else None
    if args.action == "file2text":
        # Extract text
        file2quiz.extract_text(input_dir, output_dir, blacklist_path, args.use_ocr, args.lang, args.dpi, args.psm, args.oem,
                               extract_bold=args.extract_bold,
                               save_files=True)

    elif args.action in {"file2quiz", "text2quiz"}:
        # Parse raw files
        if args.action == "file2quiz":
            file2quiz.extract_text(input_dir, output_dir, blacklist_path,
                                   args.use_ocr, args.lang, args.dpi, args.psm, args.oem,
                                   extract_bold=args.extract_bold, save_files=True)
            input_dir = os.path.join(output_dir, "txt")
        elif args.action == "text2quiz":
            pass

        # Parse quizzes
        file2quiz.parse_quiz(input_dir, output_dir, blacklist_path, args.token_answer, args.num_answers,
                             mode=args.mode, save_files=True,
                             fill_missing_answers=args.fill_missing_answers)

        # Convert to txt
        if args.save_txt:
            _input_dir = os.path.join(output_dir, "quizzes/json")
            file2quiz.convert_quiz(_input_dir, output_dir, file_format="text", save_files=True,
                                   show_answers=args.show_answers, answer_table=args.answer_table)

    elif args.action in {"quiz2text", "quiz2anki"}:
        # Select format
        if args.action == "quiz2anki":
            file_format = "anki"
        else:
            file_format = "text"
        file2quiz.convert_quiz(input_dir, output_dir, file_format=file_format, save_files=True,
                               show_answers=args.show_answers)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
