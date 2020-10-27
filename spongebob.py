import argparse

parser = argparse.ArgumentParser(description='Add text to mock (like the Spongebob meme)')
parser.add_argument('-t', '--text', help='Enter text to mock')

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