import argparse

import unicode_codes

parser = argparse.ArgumentParser(description='Add emoji between words')
parser.add_argument('-t', '--text', help='enter text to emojify')

args = parser.parse_args()

text = args.text
