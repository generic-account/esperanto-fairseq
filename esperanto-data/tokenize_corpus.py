# tokenize_corpus.py

import os, tempfile, segmentation_utils
from pathlib import Path

from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import WhitespaceSplit
from tokenizers.decoders import BPEDecoder

TAGGER = 'EsperantoWordSegmenter'
# SEP, TAG_SEP, SPACE, SPECIAL, NOTHING = "点", "分", "空", "特", "無"

SOS, EOS, UNK = "<s>", "</s>", "<unk>"

SEP, TAG_SEP, AFFIX, ENDING, SPECIAL, SPACE = "点", "分", "接", "終", "特", "空"

#3670 in eo corpus
def tokenize_generic(train, valid, test, vocab_size, output_dir, language, append_eos_bos=False):
    tokenizer = Tokenizer(BPE(unk_token=UNK))
    tokenizer.pre_tokenizer = WhitespaceSplit()
    trainer = BpeTrainer(vocab_size=vocab_size, special_tokens=[UNK, SOS, EOS], continuing_subword_prefix = "", end_of_word_suffix = ENDING)
    tokenizer.decoder = BPEDecoder(suffix = ENDING)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    tokenizer.train([train], trainer)
    tokenizer.save(os.path.join(output_dir, f"{language}_tokenizer.json"))

    train_out = open(os.path.join(output_dir, f"train.{language}"), 'w')
    for line in open(train, 'r'):
        line = line.strip()
        if append_eos_bos:
            tokens = ' '.join(tokenizer.encode(SOS + " " + line + " " + EOS).tokens)
        else:
            tokens = ' '.join(tokenizer.encode(line).tokens)
        train_out.write(tokens + '\n')
    train_out.close()

    test_out = open(os.path.join(output_dir, f"test.{language}"), 'w')
    for line in open(test, 'r'):
        line = line.strip()
        if append_eos_bos:
            tokens = ' '.join(tokenizer.encode(SOS + " " + line + " " + EOS).tokens)
        else:
            tokens = ' '.join(tokenizer.encode(line).tokens)
        test_out.write(tokens + '\n')
    test_out.close()

    valid_out = open(os.path.join(output_dir, f"valid.{language}"), 'w')
    for line in open(valid, 'r'):
        line = line.strip()
        if append_eos_bos:
            tokens = ' '.join(tokenizer.encode(SOS + " " + line + " " + EOS).tokens)
        else:
            tokens = ' '.join(tokenizer.encode(line).tokens)
        valid_out.write(tokens + '\n')
    valid_out.close()

    return tokenizer


diacritics = list(zip(("ĉ", "ĝ", "ĥ", "ĵ", "ŝ", "ŭ", "ĉ"), ("cx", "gx", "hx", "jx", "sx", "ux", "cx")))
def diacritic_replacer(text):
    for (o, n) in diacritics:
        text = text.replace(o, n) 
    return text

def extract_all_words(path):
    s = set()
    for line in open(path, 'r'):
        line = line.strip()
        s.update(line.split())
    return s

def extract_segmentations(words):
    tempin, tempout = tempfile.NamedTemporaryFile(), tempfile.NamedTemporaryFile()
    with open(tempin.name, 'w') as f:
        for s in words:
            f.write(f'{s}\n')


    cur_dir = os.getcwd()
    os.chdir('EsperantoWordSegmenter/experiments')
    os.system(f"scala -cp ../bin/ WordSegmenter.WordSegmenter train.txt ../morphemesByType/sets/ -t < {tempin.name} > {tempout.name}")
    os.chdir(cur_dir)

    segs = {}
    for (idx, line) in enumerate(tempout):
        if idx % 10000 == 0: print(f"LINE {idx}")
        if line.decode('utf-8').strip().endswith("点点"):
            word,*_ = line.decode('utf-8').strip().split('点')
            segs[word] = ('', '')
        else:

            word,seg,tags = line.decode('utf-8').strip().split('点')
            if word in segmentation_utils.special_words:
                segs[word] = (word, ("SPECIAL",))
            else:
                segs[word] = segmentation_utils.wordsegtonew(seg, tuple(segmentation_utils.convert_tags(tags.split(TAG_SEP))))
        
    return segs

def assign_marker(tag):
    if tag == "ENDING":
        return ENDING
    elif tag == "AFFIX":
        return AFFIX
    elif tag == "SPECIAL":
        return SPECIAL
    else:
        return ''

def cache_canonical_segmentation(segs):
    canonical = {}
    for s in segs:
        parts, tags = segs[s]
        if (parts, tags) == ('', ''):
            canonical[s] = s+SPACE
        elif tags == ("ROOT",):
            canonical[s] = s+SPACE
        else:
            parts = parts.split(TAG_SEP)
            # canonical[s] = ' '.join(p+NOTHING if t == "ROOT" else p+SPECIAL for (p, t) in zip(parts, tags))
            canonical[s] = ' '.join(p+assign_marker(t) for (p, t) in zip(parts, tags))
    return canonical

# check if it is marked with an esperanto specific tag
# roots (e.g., hund) and non-esperanto (e.g. computer) return false
def is_esperanto_marked_token(token):
    return any(marker in token for marker in (AFFIX, ENDING, SPECIAL))

def is_marked_token(token):
    return any(marker in token for marker in (AFFIX, ENDING, SPECIAL, SPACE))

def train_tokenizer(corpus_path, out_path, vocab_size = 3000):
    words = extract_all_words(corpus_path)
    segs = extract_segmentations(words)
    canonical = cache_canonical_segmentation(segs)

    # chars = set()
    # for s in canonical:
    #     for c in canonical[s]:
    #         chars.add(c)

    # special_tokens = []
    # for c in chars:
    #     if c not in [SEP, TAG_SEP, SPACE, SPECIAL, NOTHING]:
    #         special_tokens.append(c+SPACE)
    #         special_tokens.append(c+NOTHING)

    tokenizer = Tokenizer(BPE(unk_token=UNK))
    tokenizer.pre_tokenizer = WhitespaceSplit()
    trainer = BpeTrainer(vocab_size=vocab_size, special_tokens=[UNK, SOS, EOS], continuing_subword_prefix = "", end_of_word_suffix = "")
    
    filteredcorpus = tempfile.NamedTemporaryFile()
    with open(filteredcorpus.name, 'w') as f:
        for (idx, line) in enumerate(open(corpus_path)):
            line = line.strip().split()
            line = ' '.join(canonical.get(t, t) for t in line).split(' ')
            # filtered = [t for t in line if SPACE in t or NOTHING in t]
            filtered = [t for t in line if not is_esperanto_marked_token(t)]
            f.write(f'{" ".join(filtered)}\n')

    
    tokenizer.train([filteredcorpus.name], trainer)
    tokenizer.save("data/eo_tokenizer.json")
    
    with open(out_path, 'w') as f:
        for (idx, line) in enumerate(open(corpus_path, 'r')):
            # print(line.strip())
            line = line.strip().split()
            
            line = ' '.join(list(canonical.get(t, t) for t in line)).split()
            # print(line)
            # tokenized = ' '.join([' '.join(tokenizer.encode(t).tokens) if (SPACE in t or NOTHING in t) else t for t in line])
            tokenized = ' '.join([' '.join(tokenizer.encode(t).tokens) if not is_esperanto_marked_token(t) else t for t in line])
            # print(tokenized)

            # f.write(f'{tokenized.replace(" "+SPACE, SPACE).replace(" "+NOTHING, NOTHING)}\n')
            f.write(f'{tokenized.replace(" "+SPACE, SPACE)}\n')
    return tokenizer

def tokenize_esperanto_specific(train, valid, test, output_dir, vocab_size = 3000):
    words = extract_all_words(train)
    segs = extract_segmentations(words)
    canonical = cache_canonical_segmentation(segs)
    language = "eo"

    # chars = set()
    # for s in canonical:
    #     for c in canonical[s]:
    #         chars.add(c)

    # special_tokens = []
    # for c in chars:
    #     if c not in [SEP, TAG_SEP, SPACE, SPECIAL, NOTHING]:
    #         special_tokens.append(c+SPACE)
    #         special_tokens.append(c+NOTHING)

    tokenizer = Tokenizer(BPE(unk_token=UNK))
    tokenizer.pre_tokenizer = WhitespaceSplit()
    trainer = BpeTrainer(vocab_size=vocab_size, special_tokens=[UNK, SOS, EOS], continuing_subword_prefix = "", end_of_word_suffix = "")
    
    filteredcorpus = tempfile.NamedTemporaryFile()
    with open(filteredcorpus.name, 'w') as f:
        for (idx, line) in enumerate(open(train)):
            line = line.strip().split()
            line = ' '.join(canonical.get(t, t) for t in line).split(' ')
            # filtered = [t for t in line if SPACE in t or NOTHING in t]
            filtered = [t for t in line if not is_esperanto_marked_token(t)]
            f.write(f'{" ".join(filtered)}\n')

    
    tokenizer.train([filteredcorpus.name], trainer)
    os.path.join(output_dir, f"{language}_tokenizer.json")
    
    with open(os.path.join(output_dir, f"train.{language}"), 'w') as f:
        for (idx, line) in enumerate(open(train, 'r')):
            line = line.strip().split()
            line = ' '.join(list(canonical.get(t, t) for t in line)).split()
            tokenized = ' '.join([' '.join(tokenizer.encode(t).tokens) if not is_esperanto_marked_token(t) else t for t in line])
            f.write(f'{tokenized.replace(" "+SPACE, SPACE)}\n')

    with open(os.path.join(output_dir, f"valid.{language}"), 'w') as f:
        for (idx, line) in enumerate(open(valid, 'r')):
            line = line.strip().split()
            line = ' '.join(list(canonical.get(t, t) for t in line)).split()
            tokenized = ' '.join([' '.join(tokenizer.encode(t).tokens) if not is_esperanto_marked_token(t) else t for t in line])
            f.write(f'{tokenized.replace(" "+SPACE, SPACE)}\n')

    with open(os.path.join(output_dir, f"test.{language}"), 'w') as f:
        for (idx, line) in enumerate(open(test, 'r')):
            line = line.strip().split()
            line = ' '.join(list(canonical.get(t, t) for t in line)).split()
            tokenized = ' '.join([' '.join(tokenizer.encode(t).tokens) if not is_esperanto_marked_token(t) else t for t in line])
            f.write(f'{tokenized.replace(" "+SPACE, SPACE)}\n')

    return tokenizer

# def detokenize(sentence):
#     tokens = sentence.split()
#     out = []
#     idx = 0
#     cur = ''
#     while idx < len(tokens):
#         t = tokens[idx]
#         if SPECIAL in t:
#             cur += t[:-1]
#         else:
#             out.append(cur+SPECIAL)
#             out.append(t)
#             cur = ''
#         idx += 1
#     out = ''.join(out).replace("特", " ").replace("空", " ").replace('  ', ' ').strip()
#     return out


def detokenize(sentence):
    tokens = sentence.split()
    out = []
    idx = 0
    cur = ''
    while idx < len(tokens):
        t = tokens[idx]
        if SPECIAL in t:
            out.append(t)
        elif not is_marked_token(t):
            cur += t
        elif AFFIX in t:
            cur += t[:-1]
        elif ENDING in t or SPACE in t:
            out.append(cur + t)
            cur = ''
        idx += 1
    return ''.join(out).replace(SPECIAL, " ").replace(SPACE, " ").replace(ENDING, ' ').replace('  ', ' ').strip()
        

if __name__ == '__main__':
    
    # words = extract_all_words('data/sample.eo')
    # words = extract_all_words('data/Tatoeba.moses.cleaned.eo')
    # segs = extract_segmentations(words)
    # canonical = cache_canonical_segmentation(segs)

    # train_tokenizer("data/sample.eo")
    # corpus_path = 'data/Tatoeba.moses.cleaned.nodiacritics.eo'
    # words = extract_all_words(corpus_path)
    # segs = extract_segmentations(words)
    # canonical = cache_canonical_segmentation(segs)
    # tokenizer = train_tokenizer(corpus_path, 'data/Tatoeba.moses.cleaned.nodiacritics.tokenized.eo')

    # f = open('data/Tatoeba.moses.cleaned.nodiacritics.tokenized.eo')
    # o = open('data/Tatoeba.moses.cleaned.nodiacritics.tokenized.detokenized.eo', 'w')

    # for line in f:
    #     line = line.strip()
    #     o.write(detokenize(line) + '\n')
    # f.close()
    # o.close()

    en_generic_tok = tokenize_generic("data/train.en", "data/valid.en", "data/test.en", 3500, "data/generic_tokenizer/", "en")
    eo_generic_tok = tokenize_generic("data/train.eo", "data/valid.eo", "data/test.eo", 3500, "data/generic_tokenizer/", "eo")

    en_generic_tok = tokenize_generic("data/train.en", "data/valid.en", "data/test.en", 3500, "data/esperanto_tokenizer/", "en")
    eo_generic_tok = tokenize_esperanto_specific("data/train.eo", "data/valid.eo", "data/test.eo", "data/esperanto_tokenizer/")

