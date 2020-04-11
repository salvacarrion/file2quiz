import file2quiz

if __name__ == '__main__':
    text1 = "   text\twith        many    whitespaces"
    text2 = file2quiz.remove_whitespace(text1)
    print("Text1: " + text1)
    print("Text2: " + text2)
