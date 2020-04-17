import file2quiz
import regex

if __name__ == '__main__':
    text = """
        34 ¿ this is a question!
        a ans A
        b ans b
        ans c
        d ans d
        23 this question too?
        a asdas
        b asdasd
        c asdasd
        
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
    text = file2quiz.preprocess_text(text)
    text2 = file2quiz.preprocess_questions_block(text)
    # text2 = regex.sub(r"[\p{Latin}\p{posix_alnum}\p{posix_punct}\s]", '', text)

    print(f"Text1 ({len(text)}):" + text)
    print('-------------------------------')
    print(f"Text2 ({len(text2)}):" + text2)
    wer=8
