import os
import argparse
import quiz2test


def main():
    parser = argparse.ArgumentParser()

    # Mandatory parameters
    CHOICES = {"extract-text", "txt2quiz", "quiz2anki", "read-quiz"}
    parser.add_argument('--action', help="Actions to perform", choices=CHOICES)
    parser.add_argument('--input', help="Input file or directory", default=None)
    parser.add_argument('--output', help="Output directory", default=None)

    # Quizzes
    parser.add_argument('--blacklist', help="Blacklist file with the excluded words or patterns", default=None)
    parser.add_argument('--token_answer', help="Token used to split the file between questions and answers", default=None)
    parser.add_argument('--single-line', help="Use single line to split elements", default=False, type=bool)
    parser.add_argument('--show_correct', help="Show correct answer", default=True, type=bool)
    parser.add_argument('--num_answers', help="Number of answers per question", default=None, type=int)

    # Tesseract
    parser.add_argument('--use_ocr', help="Use an OCR to extract text from the PDFs", default=True, type=bool)
    parser.add_argument('--lang', help="[Tesseract] Specify language(s) used for OCR", default="eng")
    parser.add_argument('--dpi', help="[Tesseract] Specify DPI for input image", default=300, type=int)
    parser.add_argument('--psm', help="[Tesseract] Specify page segmentation mode", default=3, type=int)
    parser.add_argument('--oem', help="[Tesseract] Specify OCR Engine mode", default=3, type=int)

    args = parser.parse_args()

    if args.action == "extract-text":
        # Set default paths
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "raw"))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir)))

        # Extract text
        quiz2test.extract_text(input_dir, output_dir,
                               args.use_ocr, args.lang, args.dpi, args.psm, args.oem, save_files=True)
        print("Done!")

    elif args.action == "txt2quiz":
        # Set default paths
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "txt"))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir)))
        blacklist = os.path.abspath(args.output) if args.blacklist else os.path.abspath(os.path.join(os.path.dirname(input_dir), "blacklist.txt"))

        # Parse quizzes
        quiz2test.parse_quiz(input_dir, output_dir, blacklist,
                             args.token_answer, args.single_line, args.num_answers, save_files=True)
        print("Done!")

    elif args.action == "quiz2anki":
        # Set default paths
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "quizzes"))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir)))

        # Convert quiz to anki
        quiz2test.convert_quiz(input_dir, output_dir, file_format="anki", save_files=True)
        print("Done!")

    elif args.action == "read-quiz":
        # Set default paths
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "quizzes"))

        # Read quizzes
        quiz_txts = quiz2test.json2text(input_dir, args.show_correct)

        # Print quizes
        for i, (name, quiz_txt) in enumerate(quiz_txts, 1):
            print("===========================================")
            print("Quiz #{}: {}".format(i, name))
            print("===========================================")
            print("")
            print(quiz_txt)
            print("\n\n") if i < len(quiz_txts) else None

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
