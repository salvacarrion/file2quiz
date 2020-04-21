import unittest
import os

import file2quiz


# global variables
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../"))


class TestQuizify(unittest.TestCase):

    def test_file2quiz(self):
        # Get paths
        input_dir = os.path.join(ROOT_DIR, "examples/raw/")
        output_dir = os.path.join(ROOT_DIR, "examples/")
        blacklist_path = os.path.join(ROOT_DIR, "examples/blacklist.txt")
        token_answer = "^(===|solUtIoNs:)"  # Check case insensitivity // There are problems with this token: "==="
        extensions = {".txt", ".pdf", ".rtf", ".docx", ".html", ".png"}

        # Parse raw files
        print("Extracting text...")
        texts_extracted = file2quiz.extract_text(input_dir, output_dir, blacklist_path, extensions=extensions,
                                                 save_files=True)

        # Parse texts into quizzes
        print("Parsing quizzes...")
        quizzes = []
        blacklist = file2quiz.reader.read_blacklist(blacklist_path)
        for text, text_selected, filename in texts_extracted:
            quiz = file2quiz.parse_quiz_txt(text, blacklist, token_answer=token_answer)
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
            self.assertTrue(quiz.get("3.1").get('id') == "3.1")

            # Check question lengths (characters)
            self.assertTrue(len(quiz.get("1").get('question')) > 30)
            self.assertTrue(len(quiz.get("2").get('question')) > 30)
            self.assertTrue(len(quiz.get("3.1").get('question')) > 30)

            # Check question answers
            self.assertEqual(len(quiz.get("1").get('answers')), 4)
            self.assertEqual(len(quiz.get("2").get('answers')), 4)
            self.assertEqual(len(quiz.get("3.1").get('answers')), 4)

            # Check correct answers
            self.assertEqual(quiz.get("1").get('correct_answer'), 0)
            self.assertEqual(quiz.get("2").get('correct_answer'), 1)
            self.assertEqual(quiz.get("3.1").get('correct_answer'), 3)

    def test_text2quiz(self):
        txt = """
            text to ignore
            text to ignore
            text to ignore


            1---- -2 degrees is the...
            a\t1
            b.1.2
            c-------1.3 negative number

            2. Missing one answer and id:
            a) Example answer #1
            b) Example answer #2

            3 Testing normalization   ???  
            a) the T    ª is   -    10 º        C  .
            (b) has <  10      mm2 and >=    -  10.0    Kg.
            ( c ) the discount is + 12   %

            4\t¿Testing broken question from
            1923?\t
            a\t   \t  Example answer #1
            b\t Example answer #2
            c\t     Example answer #3

            5 ))) 5 is a number, and
            question
            is

            also broken  :
            a) Example answer #1
            b) Example answer #2
            c) Example answer #3
            a this is part of the 3rd question

            6.1 ))) This question is 6.1 and
            is quite hard :
            6.1a) Example answer #1
            6b) Example answer #2
            c) Example answer #3

            7. this question is also is tricky because of this
            10.0b, and this
            a:
            a) Example answer
            number 1
            b) More answers 2
            c) More answers 3
            e do not confuse with a answer id
            d) Last answer
            a nd this neither

            ===

            1-A 2.b
            3    // C
            4 b 5A,(6.1b)
            7.c
            """

        # Parse quiz
        quizzes = file2quiz.parse_quiz_txt(txt, token_answer="===")

        # General checks
        self.assertEqual(len(quizzes), 7)  # Num. questions

        # Check question IDs
        self.assertTrue(quizzes.get("1").get('id') == "1")
        self.assertTrue(quizzes.get("2").get('id') == "2")
        self.assertTrue(quizzes.get("3").get('id') == "3")
        self.assertTrue(quizzes.get("4").get('id') == "4")
        self.assertTrue(quizzes.get("5").get('id') == "5")
        self.assertTrue(quizzes.get("6.1").get('id') == "6.1")
        self.assertTrue(quizzes.get("7").get('id') == "7")

        # Check question answers
        self.assertEqual(len(quizzes.get("1").get('answers')), 3)
        self.assertEqual(len(quizzes.get("2").get('answers')), 2)
        self.assertEqual(len(quizzes.get("3").get('answers')), 3)
        self.assertEqual(len(quizzes.get("4").get('answers')), 3)
        self.assertEqual(len(quizzes.get("5").get('answers')), 3)
        self.assertEqual(len(quizzes.get("6.1").get('answers')), 3)
        self.assertEqual(len(quizzes.get("7").get('answers')), 4)

        # Check question lengths (characters)
        self.assertTrue(quizzes.get("1").get('answers')[0] == "1")
        self.assertTrue(quizzes.get("1").get('answers')[1] == "1.2")
        self.assertTrue(quizzes.get("1").get('answers')[2] == "-1.3 negative number")

        self.assertTrue(quizzes.get("3").get('question') == "Testing normalization?")
        self.assertTrue(quizzes.get("3").get('answers')[0] == "The Tª is -10ºC")
        self.assertTrue(quizzes.get("3").get('answers')[1] == "Has <10mm2 and >=-10.0Kg")
        self.assertTrue(quizzes.get("3").get('answers')[2] == "The discount is +12%")

        self.assertTrue(quizzes.get("5").get('answers')[2] == "Example answer #3 a this is part of the 3rd question")
        self.assertTrue(quizzes.get("7").get('answers')[2] == "More answers 3 e do not confuse with a answer id")

        # Check correct answers
        self.assertEqual(quizzes.get("1").get('correct_answer'), 0)
        self.assertEqual(quizzes.get("2").get('correct_answer'), 1)
        self.assertEqual(quizzes.get("3").get('correct_answer'), 2)
        self.assertEqual(quizzes.get("4").get('correct_answer'), 1)
        self.assertEqual(quizzes.get("5").get('correct_answer'), 0)
        self.assertEqual(quizzes.get("6.1").get('correct_answer'), 1)
        self.assertEqual(quizzes.get("7").get('correct_answer'), 2)


if __name__ == '__main__':
    # Test single test
    suite = unittest.TestSuite()
    suite.addTest(TestQuizify("test_text2quiz"))
    runner = unittest.TextTestRunner()
    runner.run(suite)

    # Test all
    unittest.main()
