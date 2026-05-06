import argparse
import os
import pickle
import random
import re

import numpy as np
from sentence_transformers import SentenceTransformer

import unicode_codes

MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
CACHE_PATH = os.path.join(os.path.dirname(__file__), '.emoji_embeddings.pkl')

# Skip closed-class words; they tend to attract spurious near-matches and
# real Reddit emojify-style output keeps them bare anyway.
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'being', 'but', 'by',
    'do', 'does', 'did', 'for', 'from', 'had', 'has', 'have', 'he', 'her',
    'here', 'hers', 'him', 'his', 'i', 'if', 'in', 'into', 'is', 'it', 'its',
    'me', 'my', 'no', 'nor', 'not', 'of', 'on', 'or', 'our', 'ours', 'out',
    'over', 'she', 'so', 'some', 'such', 'than', 'that', 'the', 'their',
    'theirs', 'them', 'then', 'there', 'these', 'they', 'this', 'those',
    'to', 'too', 'under', 'until', 'up', 'us', 'was', 'we', 'were', 'what',
    'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with',
    'would', 'you', 'your', 'yours',
}


def humanize(name):
    return name.strip(':').replace('_', ' ').replace('-', ' ')


def build_emoji_table():
    emojis, names = [], []
    for name, code in unicode_codes.EMOJI_UNICODE.items():
        if 'skin_tone' in name or 'selector' in name:
            continue
        emojis.append(code)
        names.append(humanize(name))
    return emojis, names


def build_token_index(names):
    index = {}
    for i, name in enumerate(names):
        for token in name.lower().split():
            t = re.sub(r'[^a-z0-9]', '', token)
            if t:
                index.setdefault(t, []).append(i)
    return index


def lookup_literals(token_index, key):
    # Try the key, then a couple of crude singular forms ("cats" → "cat",
    # "boxes" → "box"). Good enough without pulling in a real stemmer.
    if key in token_index:
        return token_index[key]
    if key.endswith('ies') and len(key) > 3:
        alt = key[:-3] + 'y'
        if alt in token_index:
            return token_index[alt]
    if key.endswith('es') and len(key) > 3:
        alt = key[:-2]
        if alt in token_index:
            return token_index[alt]
    if key.endswith('s') and len(key) > 2:
        alt = key[:-1]
        if alt in token_index:
            return token_index[alt]
    return []


def load_or_build_embeddings(model, names):
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, 'rb') as f:
            cached = pickle.load(f)
        if cached.get('model') == MODEL_NAME and cached.get('names') == names:
            return cached['embeddings']
    embeddings = model.encode(names,
                              normalize_embeddings=True,
                              show_progress_bar=True)
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump({'model': MODEL_NAME, 'names': names, 'embeddings': embeddings}, f)
    return embeddings


parser = argparse.ArgumentParser(description='Add emoji between words')
parser.add_argument('-t', '--text', required=True, help='enter text to emojify')
parser.add_argument('-n',
                    '--max-emojis',
                    type=int,
                    default=1,
                    help='max number of emojis to insert per matched word')
parser.add_argument('-k',
                    '--top-k',
                    type=int,
                    default=5,
                    help='sample picks from this many top-similar emojis per word')
parser.add_argument('--threshold',
                    type=float,
                    default=0.4,
                    help='cosine similarity threshold; words below this get no emoji')
parser.add_argument('--keep-stopwords',
                    action='store_true',
                    help='also try to emojify common stop words (is, the, with, ...)')
parser.add_argument('--seed', type=int, help='random seed for reproducibility')

args = parser.parse_args()

if args.seed is not None:
    random.seed(args.seed)

model = SentenceTransformer(MODEL_NAME)
emojis, names = build_emoji_table()
emoji_embeddings = load_or_build_embeddings(model, names)
token_index = build_token_index(names)

words = args.text.split()
keys = [re.sub(r'[^a-z0-9]', '', w.lower()) for w in words]
skip = set() if args.keep_stopwords else STOP_WORDS
unique_keys = sorted({k for k in keys if k and k not in skip})

if unique_keys:
    key_embeddings = model.encode(unique_keys, normalize_embeddings=True)
    sims = key_embeddings @ emoji_embeddings.T
else:
    sims = None

def weighted_sample_without_replacement(items, weights, k):
    # Efraimidis-Spirakis: assign each item key = u^(1/w), pick top-k.
    # random.random() uses the seeded PRNG so output is reproducible.
    keyed = []
    for item, w in zip(items, weights):
        if w <= 0:
            continue
        u = random.random()
        keyed.append((u ** (1.0 / w), item))
    keyed.sort(reverse=True)
    return [item for _, item in keyed[:k]]


name_token_counts = [len(n.split()) for n in names]

top_per_key = {}
for i, key in enumerate(unique_keys):
    sims_row = sims[i]
    literals = lookup_literals(token_index, key)
    literal_set = set(literals)

    # Literal-match score: cosine + flat bonus - shortness penalty. Shorter
    # names are more iconic (`money_bag` over `money_with_wings`), so they
    # win ties and often outscore higher-cosine but wordier alternatives.
    def literal_score(idx):
        return float(sims_row[idx]) + 0.5 - 0.05 * (name_token_counts[idx] - 1)

    literals_sorted = sorted(literals, key=lambda idx: -literal_score(idx))
    others_order = [int(idx) for idx in np.argsort(-sims_row) if int(idx) not in literal_set]
    combined = (literals_sorted + others_order)[:args.top_k]

    if not literals_sorted and sims_row[others_order[0]] < args.threshold:
        top_per_key[key] = None
        continue

    # ^8 sharpens the distribution so the top candidate wins ~50%+ of the time
    # while still leaving room for variety across seeds.
    weights = []
    for idx in combined:
        s = literal_score(idx) if idx in literal_set else max(0.0, float(sims_row[idx]))
        weights.append(max(s, 0.0) ** 8)
    top_per_key[key] = (combined, weights)

emojified = []
for word, key in zip(words, keys):
    emojified.append(word)
    entry = top_per_key.get(key) if key else None
    if entry is None:
        continue
    indices, weights = entry
    n = random.randint(1, args.max_emojis)
    picks = weighted_sample_without_replacement(indices, weights, min(n, len(indices)))
    emojified.append(''.join(emojis[i] for i in picks))

print(' '.join(emojified))
