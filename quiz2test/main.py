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

    args = parser.parse_args()
    if args.action == "parse":
        input_dir = args.input if args.input else os.path.abspath(os.path.join(os.getcwd(), "raw"))
        output_dir = args.output if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir), "parsed"))
        banned_words = args.output if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir), "banned.txt"))
        quiz2test.parse_exams(input_dir, output_dir, args.token, banned_words)
        print("Done!")

    elif args.action == "read":
        input_dir = args.input if args.input else os.path.abspath(os.path.join(os.getcwd(), "parsed"))
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
        input_dir = args.input if args.input else os.path.abspath(os.path.join(os.getcwd(), "parsed"))
        output_dir = args.output if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir), "anki"))
        quiz2test.convert2anki(input_dir, output_dir)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
