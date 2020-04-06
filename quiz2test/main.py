import os
import argparse
import quiz2test


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--action', help="shows output", default="parse")
    parser.add_argument('-i', '--input', help="Folder to search for the raw exams", default=None)
    parser.add_argument('-o', '--output', help="Folder to save for the parsed exams", default=None)
    parser.add_argument('-t', '--token', help="Token used to split questions and answers", default=None)

    args = parser.parse_args()

    if args.action:
        input_dir = args.input if args.input else os.path.abspath(os.path.join(os.getcwd(), "raw"))
        output_dir = args.output if args.output else os.path.abspath(os.path.join(os.path.dirname(input_dir), "parsed"))

        if args.action == "parse":
            quiz2test.parser.parse_exams(input_dir, output_dir, args.token)
        elif args.action == "quiz":
            pass
        else:
            raise KeyError("Unknown option")

        print("Done!")


if __name__ == '__main__':
    main()
