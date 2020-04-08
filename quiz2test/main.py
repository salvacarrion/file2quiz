import os
import argparse
import quiz2test


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--action', help="shows output", choices=['parse', 'read', 'convert2anki'])
    parser.add_argument('-i', '--input', help="File or folder to search for the raw exams", default=None)
    parser.add_argument('-o', '--output', help="File or folder to save for the parsed exams", default=None)
    parser.add_argument('-t', '--token', help="Token used to split questions and answers", default=None)
    parser.add_argument('-s', '--show_correct', help="Show correct answer", default=True, action='store_true')
    parser.add_argument('-e', '--exclude_words', help="File with excluded words", default=None)
    parser.add_argument('--single_line', help="Use single line to split elements", default=False, action='store_true')
    parser.add_argument('--num_answers', help="Number of answers per question", default=None, type=int)
    parser.add_argument('--use_ocr', help="Use an OCR (tesseract) to extract the text from the PDF", default=False, action='store_true')
    parser.add_argument('--lang', help="[Tesseract] Specify language(s) used for OCR", default="eng")
    parser.add_argument('--dpi', help="[Tesseract] Specify DPI for input image", default=300, type=int)
    parser.add_argument('--psm', help="[Tesseract] Specify page segmentation mode", default=3, type=int)
    parser.add_argument('--oem', help="[Tesseract] Specify OCR Engine mode", default=3, type=int)

    args = parser.parse_args()
    if args.action == "parse":
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "raw"))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir), "parsed"))
        blacklist = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir), "blacklist.txt"))

        # Parse quizzes
        quiz2test.parse_exams(input_dir, output_dir, blacklist,
                              args.token, args.single_line, args.num_answers,
                              args.use_ocr, args.lang, args.dpi, args.psm, args.oem)
        print("Done!")

    elif args.action == "read":
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "parsed"))

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

    elif args.action == "convert2anki":
        input_dir = os.path.abspath(args.input) if args.input else os.path.abspath(os.path.join(os.getcwd(), "parsed"))
        output_dir = os.path.abspath(args.output) if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir), "anki"))

        # Convert quizzes
        quiz2test.convert2anki(input_dir, output_dir)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
