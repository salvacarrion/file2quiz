import file2quiz
import regex

if __name__ == '__main__':
    text = """
        has <  +10      mm2 and >=    -10.0    Kg.
        The T    ª is   +10 º        C  .
        234234     m,
        123     Mm2.
        34  \t\t\tm werwerw
        34    \nl.
        233      hg
        234234       ml3
        234234      mlqweqwe
 """
    text2 = file2quiz.normalize_answers(text)
    # text2 = regex.sub(r"[\p{Latin}\p{posix_alnum}\p{posix_punct}\s]", '', text)

    print(f"Text1 ({len(text)}):" + text)
    print('-------------------------------')
    print(f"Text2 ({len(text2)}):" + text2)
    wer=8
