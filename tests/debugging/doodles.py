import re
with open("doodles.txt") as f:
    text = f.read()

    pattern = re.compile(r"Respuesta correcta:\s*([a-zA-Z])", re.MULTILINE)
    values = re.findall(pattern, text)
    for i, v in enumerate(values, 1):
        print(f"{i}: {v}")
    asdad = 33