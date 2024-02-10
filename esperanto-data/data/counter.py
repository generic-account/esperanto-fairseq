'''
things to look into:
  - correlatives

https://object.pouta.csc.fi/OPUS-Tatoeba/v2023-04-12/moses/en-eo.txt.zip

'''
import string
import sys

args = sys.argv
vocabfrequency = args[1]

SUBWORD_MARKER = '@'

d = {
    # 'nuntempe': [('nun', 'ROOT'), ('temp', 'ROOT'), ('e', 'ENDING')],
    # 'riprocxindajo':[('riprocx', 'ROOT'), ('ind', 'ROOT'), ('aj', 'ROOT'), ('o', 'ENDING')],
    # 'malpliigi':[('mal', 'AFFIX'), ('pli', 'ROOT'), ('ig', 'AFFIX'), ('i', 'ENDING')]
}

special_words=set(['nenies', 'ĉiel', 'cxiel', 'ĉies', 'iel', 'ĉiam', 'kie',
                   'kiu', 'tiu', 'iom', 'cxiu', 'nenio', 'tiel', 'cxio', 'kiom',
                   'nenie', 'cxia', 'tio', 'ĉiom', 'ial', 'neniu', 'tiam', 'kia',
                   'cxiom', 'ie', 'ĉia', 'kiam', 'cxie', 'io', 'kio', 'tia', 'kiel',
                   'nenial', 'tial', 'ties', 'e', 'tie', 'neniel', 'ies', 'neniom',
                   'ĉie', 'nenia', 'iam', 'ĉio', 'kial', 'tiom', 'an', 'cxial', 'iu',
                   'kies', 'ia', 'ĉial', 'neniam', 'ĉiu', 'cxies', 'cxiam','desur','depost',
                   'disde'])

make_root = set([
  ("AFFIX","AFFIX","ENDING"),
  ("SPECIAL","SPECIAL"),
  ('SPECIAL', 'SPECIAL', 'ENDING'),
  ('AFFIX', 'ROOT'),
  ('ROOT', 'AFFIX')
])

weird = set(string.digits + string.punctuation + "!',-.'?€" + "'" + "„”„”…₫‘’–—»«¨²")

circumflex = {"ŭ": "ux", "ĉ": "cx", "ĝ": "gx", "ĥ": "hx", "ĵ": "jx", "ŝ": "sx"}

SPECIAL = set([
    "expression", "pronoun", "expression", "adverb", "article",
    "conjunction", "preposition"])
AFFIX = set(["prefix", "suffix"])
ENDING = set(["ending"])

def convert_tag(tag):
  # input tag -> output tag
  for affix in AFFIX:
    if affix in tag or tag == "o":
      return "AFFIX"
  if "ending" in tag and tag != "midending":
    return "ENDING"
  elif tag in SPECIAL or tag == "":
    return "SPECIAL"
  return "ROOT"

def convert_tags(tags):
  l = []
  for tag in tags:
    tag = tag.lower()
    converted = convert_tag(tag)
    if ("special" in converted
          or "ending" in tag) and len(l) < len(tags) - 1:
      l.append("ROOT")
    else:
      l.append(converted)
  return l

def wordsegtonew(seg,tags):
  if "SPECIAL" in tags and len(tags) > 1 and tags != ("SPECIAL","ENDING"):
    tagscopy = list(tags)
    for i in range(len(tags)):
      if tagscopy[i] == "SPECIAL":
        tagscopy[i] = "ROOT"
    tags = tuple(tagscopy)
      
  if "ROOT" in tags and tags.count("ROOT")>1:
    firstroot = tags.index("ROOT")
    lastroot = len(tags) - tags[::-1].index("ROOT")
    tags = tags[:firstroot] + tags[lastroot-1:]
    seg = seg.split("_")
    seg = "_".join(seg[:firstroot] + ["".join(seg[firstroot:lastroot])] + seg[lastroot:])

  if tags in make_root:
    tags = ("ROOT",)
    seg = "".join(seg.split())
  
  if seg.split("_")[-1] in ["i","ia","as","os","us","u",
            "o","a","e",
            "on","an","en",
            "oj","aj",
            "ojn","ajn",
            "aŭ"]:
    tagcopy = list(tags)
    tagcopy[-1] = "ENDING"
    tags = tuple(tagcopy)
  return seg,tags

def segmentation_pattern_counter(path=vocabfrequency):
  d = {}
  
  f = open(path,'r')

  for line in f:
    if ',,' not in line:
      surface, seg, tags = line.strip().split(',')

      if surface in special_words:
        tags = ("SPECIAL",)
      else:
        tags = tuple(convert_tags(tags.split('_')))
      
      seg,tags = wordsegtonew(seg,tags)

      if tags not in d:
        d[tags] = [1, set(((surface, seg),))]
      else:
        d[tags][0] += 1
        d[tags][1].add((surface, seg))
  
  f.close()
  return d


if __name__ == '__main__':
  seg_dict = segmentation_pattern_counter()

  for s in sorted(seg_dict, key = lambda s: seg_dict[s][0], reverse=True):
    print(s, seg_dict[s][0])


 # dictionary: morpheme_tag_seq -> (count of the total number of times this appears, set of all (words/segmented_version) that have that segmentation pattern) 

 # (verb, verb_ending) -> (100, set((estas, (est, as)), ...))

# ('PrepPrefix_Noun_VerbSuffix_VerbEnding') = ellitiĝis, alluniĝos, enterigis


'''

>>> seg_dict[("ROOT","ROOT", "AFFIX", "ROOT")]
[1, {'italalingve', 'ital_al_ing_ve'}]

>>> seg_dict[("SPECIAL", "SPECIAL")]
[9, {('naŭdek', 'naux_dek'), ('naŭcent', 'naux_cent'), ('kvindek', 'kvin_dek'), ('dudek', 'du_dek'), ('tridek', 'tri_dek')}]

>>> seg_dict[("ROOT", "ROOT", "ROOT")]
[2, {('itallingve', 'ital_lingv_e'), ('baldaŭmalbaldaŭ', 'baldaux_mal_baldaux')}]
'''