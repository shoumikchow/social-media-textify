import argparse


def stringify_boolean(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    elif isinstance(v, bool):
        return v
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


parser = argparse.ArgumentParser(description='Add clap between words')
parser.add_argument('-t', '--text', help='enter text to clappify')
parser.add_argument('-s',
                    '--shout',
                    default=True,
                    type=stringify_boolean,
                    help='convert all text to uppercase')
parser.add_argument('-e',
                    '--emoji',
                    default='👏',
                    help='replace clap withs another emoji?')

args = parser.parse_args()

text = args.text
clap = args.emoji
shout = args.shout

text_split = text.split(" ")
clapped = []

for i, word, in enumerate(text_split):
    if shout:
        clapped.append(word.upper())
    else:
        clapped.append(word.lower())
    if i == len(text_split) - 1:
        continue
    clapped.append(clap)

print(" ".join(clapped))