import unittest
import os

import file2quiz


# global variables
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../"))


class TestQuizify(unittest.TestCase):

    def test_quiz_parser(self):
        # Get paths
        input_dir = os.path.join(ROOT_DIR, "examples/raw")
        output_dir = os.path.join(ROOT_DIR, "examples")
        token_answer = "SolUtiOns"  # Check case insensitivity // There are problems with this token: "==="
        extensions = {".txt", ".pdf", ".rtf", ".docx", ".html", ".jpg"}

        # Parse raw files
        print("Extracting text...")
        texts_extracted = file2quiz.extract_text(input_dir, output_dir, extensions=extensions)

        # Parse texts into quizzes
        print("Parsing quizzes...")
        quizzes = []
        for text, filename in texts_extracted:
            quiz = file2quiz.parse_quiz_txt(text, token_answer=token_answer)
            quizzes.append((quiz, filename))

        # Check texts extracted and quizzes
        self.assertEqual(len(quizzes), len(texts_extracted))

        # Check quizzes
        print("Checking quizzes...")
        for quiz, filename in quizzes:
            basedir, tail = os.path.split(filename)
            print(f'Testing quiz: "{tail}"...')

            # General checks
            self.assertEqual(len(quiz), 3)  # Num. questions

            # Check question IDs
            self.assertTrue(quiz.get("1").get('id') == "1")
            self.assertTrue(quiz.get("2").get('id') == "2")
            self.assertTrue(quiz.get("3").get('id') == "3")

            # Check question lengths (characters)
            self.assertTrue(len(quiz.get("1").get('question')) > 30)
            self.assertTrue(len(quiz.get("2").get('question')) > 30)
            self.assertTrue(len(quiz.get("3").get('question')) > 30)

            # Check question answers
            self.assertEqual(len(quiz.get("1").get('answers')), 4)
            self.assertEqual(len(quiz.get("2").get('answers')), 4)
            self.assertEqual(len(quiz.get("3").get('answers')), 4)

            # Check correct answers
            self.assertEqual(quiz.get("1").get('correct_answer'), 0)
            self.assertEqual(quiz.get("2").get('correct_answer'), 1)
            self.assertEqual(quiz.get("3").get('correct_answer'), 3)


if __name__ == '__main__':
    unittest.main()
