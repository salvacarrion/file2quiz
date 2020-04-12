import file2quiz
import regex

if __name__ == '__main__':
    text = "1/5 del número legal ."
    text2 = file2quiz.normalize_answers(text)
    # text2 = regex.sub(r"[\p{Latin}\p{posix_alnum}\p{posix_punct}\s]", '', text)

    print(f"Text1 ({len(text)}):" + text)
    print('-------------------------------')
    print(f"Text2 ({len(text2)}):" + text2)
    wer=8
