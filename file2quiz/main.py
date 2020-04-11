import os
import argparse
import file2quiz


def main():
    parser = argparse.ArgumentParser()

    # Mandatory parameters
    CHOICES = {"file2text", "text2quiz", "quiz2text", "quiz2anki"}
    parser.add_argument('--action', help="Actions to perform", choices=CHOICES)
    parser.add_argument('--input', help="Input file or directory", default=None)
    parser.add_argument('--output', help="Output file or directory", default=None)

    # Quizzes
    parser.add_argument('--blacklist', help="Blacklist file with the excluded words or patterns (regex)", default=None)
    parser.add_argument('--token-answer', help="(regex) Token used to split the file between questions and answers", default=None)
    parser.add_argument('--single-line', help="Use single line to split elements", default=False, type=bool)
    parser.add_argument('--show-answers', help="Show correct answer", default=False, action="store_true")
    parser.add_argument('--num-answers', help="Number of answers per question", default=None, type=int)

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
        file2quiz.extract_text(input_dir, output_dir, args.use_ocr, args.lang, args.dpi, args.psm, args.oem, save_files=True)
        print("Done!")

    elif args.action == "text2quiz":
        # Set default paths
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "txt"))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.getcwd()))
        blacklist = os.path.abspath(args.output) if args.blacklist else os.path.abspath(os.path.join(os.getcwd(), "blacklist.txt"))

        # Parse quizzes
        file2quiz.parse_quiz(input_dir, output_dir, blacklist, args.token_answer, args.single_line, args.num_answers, save_files=True)
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
