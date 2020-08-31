import re

from fuzzysearch import find_near_matches


def match_replace(pattern, replacement, text):
  regex = re.compile(pattern, re.IGNORECASE)
  return regex.sub(replacement, text)


def normalize_string(string):
  string = match_replace('[^\w]', ' ', string)
  string = match_replace('\s+', ' ', string)

  return string.lower().strip()


def contains_words(text, words, require_all=True):
  for word in words:
    if word in text:
      if not require_all:
        return True
    elif require_all:
      return False

  return require_all


class FuzzyMatch(object):

  def __init__(self, text):
    self.score = -1
    self.query = ''
    self.value = normalize_string(text)

  def set_query(self, query):
    if bool(query) and query != self.query:
      self.query = query
      self.score = self.get_score(query)

  def get_score(self, query):
    query = normalize_string(query)
    words = query.split(' ')

    if not contains_words(self.value, words):
      return -1

    fuzzy = find_near_matches(query, self.value, max_l_dist=1)
    score = sum(map(lambda m: m.dist, fuzzy))

    return score
