import argparse

parser = argparse.ArgumentParser(description='Add clap between words')
parser.add_argument('-t', '--text', help='enter text to clappify')

args = parser.parse_args()
text = args.text
spongebobbed = []
b = True

for i in text:
    if b:
        spongebobbed.append(i.upper())
    else:
        spongebobbed.append(i.lower())
    b = not b

print("".join(spongebobbed))