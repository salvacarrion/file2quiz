import file2quiz
import string
import re
from collections import Counter

d = Counter()
with open("doodles.txt", "r", encoding="utf8")as f:
    file = f.read()
    for c in file:
        d[c]+=1

chars = []
for c, freq in d.most_common():
    chars.append(c)
    print(f"{c} - {freq}")

print("Chars:" + "".join(chars))
asdasd = 3



asda = 3