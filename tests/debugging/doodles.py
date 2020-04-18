import file2quiz
import string
import re

exam = file2quiz.read_txt("doodles.txt")
lines = exam.split('\n')

exams = []

prev_line = 0
is_first=True
for i, l in enumerate(lines):
    m = re.search(r"^1\.[\- ]+", l)
    if m:
        if is_first:
            is_first=False
        else:
            new_exam = lines[prev_line:i-6]
            exams.append(new_exam)
            prev_line=i-6

# Add last exam
new_exam = lines[prev_line:]
exams.append(new_exam)

path ="/Users/salvacarrion/Desktop/examples/txt"
for i, e in enumerate(exams):
    with open(f"{path}/Recopilación exámenes Málaga.pdf_{i}.txt", 'w', encoding="utf8") as f:
        text = "\n".join(e)
        text = text.replace("CORRECTOR", "=====")
        f.write(text)



asda = 3