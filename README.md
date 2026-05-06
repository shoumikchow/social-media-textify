# social-media-textify


## Clappify

### Usage
> python clappify.py -t "Tweets with claps between the words are annoying"

outputs:

> TWEETS 👏 WITH 👏 CLAPS 👏 BETWEEN 👏 THE 👏 WORDS 👏 ARE 👏 ANNOYING

Optional arguments for the command include `-s` which is a boolean (true by default) to shout/capitalize all the letters and `-e` which lets you replace the clap emoji with any other unicode emoji.

## Spongebob

### Usage
> python spongebob.py -t "Don't use that weird spongebob mocking meme"

outputs:

> DoN'T UsE ThAt wEiRd sPoNgEbOb mOcKiNg mEmE


## Emojify

Inserts semantically-related emojis after content words, similar to
[Emojifier bot on Reddit](https://www.reddit.com/user/EmojifierBot). Word/emoji
relevance is scored with sentence-transformer embeddings of the emoji name
catalogue (cached on first run).

### Setup
> uv sync

### Usage
> uv run python emojify.py -t "What is this new trend with the emojis in between the text?"

outputs (sample):

> What is this new 🧵 trend with the emojis ❗ in between 👶 the text? 🏷

Optional arguments: `-n` max emojis per word (default 1), `-k` size of the
top-similar pool sampled from (default 5), `--threshold` minimum cosine
similarity for a word to get any emoji (default 0.4), `--keep-stopwords` to
also try emojifying common stop words, and `--seed` for reproducible output.
Picks within the top-K pool are weighted by similarity, so the strongest match
is favored.