#! /usr/bin/env python3
# Merge duplicated Wikipedia references/citations. Written by davidhcefx, 2022.4.10.
import re
import readline
from typing import Dict, List, Tuple, Set
from hashlib import md5

REF_PATTERN = re.compile(r'<ref\b(?P<name>[^>]*)(?<!/)>(?P<pay>.*?)</ref>', re.DOTALL)
NAME_ATTR_PATTERN = re.compile(r'name\s*=\s*"?(\w+)"?', re.DOTALL)  # name attribute in <ref>
WORD_PATTERN = re.compile(r'\w')


class CitationDatabase:
    """
    Associate citation-payloads with its short names.
    A citation-payload is the part enclosed by <ref></ref>.
    """
    def __init__(self):
        self.shortnames: Dict[str, str] = dict()  # map a payload to its short name

    def add(self, payload: str, shortname: str):
        """Please ensure that each shortname is unique."""
        self.shortnames[payload] = shortname

    def has(self, payload: str) -> bool:
        # we simply query with the exact text here, but one can extend to other logics
        # such as URL/DOI detection or to ignore whitespace differences.
        return payload in self.shortnames

    def get_shortname(self, payload: str) -> str:
        return self.shortnames[payload] if self.has(payload) else ''


def generate_short_name(payload: str) -> str:
    """Generate wiki-accepted short-names from citation-payloads."""
    # compute md5 to avoid collisions
    n = ''.join(WORD_PATTERN.findall(payload)[:5]) + md5(payload.encode()).hexdigest()
    return 'c-{}'.format(n[:8])

def get_duplicated_refs(article: str, db: CitationDatabase) -> Set[str]:
    """Return a set of duplicated citation-payloads; Update db along the way."""
    result = set()
    idx = 0
    while ref := REF_PATTERN.search(article, idx):
        name_str, payload = ref.group('name', 'pay')
        if db.has(payload):
            result.add(payload)
        else:
            # parse or generate shortname
            shortname = n.group(1) if (n := NAME_ATTR_PATTERN.search(name_str)) \
                        else generate_short_name(payload)
            db.add(payload, shortname)

        idx = ref.end()

    return result

def has_name_attribute(ref: re.Match) -> bool:
    return NAME_ATTR_PATTERN.search(ref.group('name')) is not None

def merge(article: str) -> Tuple[str, List[str]]:
    """
    Merge duplicated refs in wiki source; return new article and a list of duplicated refs.
    There are five kinds of refs: (we aim to merge the 2nd and 5th)
      1) no name unique payload: <ref>a</ref>
      2) no name duplicated payload: <ref>a</ref><ref>a</ref>
      3) has name no payload (SKIPPED): <ref name="n" />
      4) has name has unique payload: <ref name="n">a</ref>
      5) has name has duplicated payload: <ref name="n">a</ref><ref name="n">a</ref>
    """
    new_article = []
    db = CitationDatabase()
    duplicated_refs: Set[str] = get_duplicated_refs(article, db)
    seen: Set[str] = set()
    idx = 0
    while ref := REF_PATTERN.search(article, idx):
        new_article.append(article[idx:ref.start()])  # output the previous segment
        idx = ref.end()
        payload = ref.group('pay')
        if payload not in duplicated_refs:
            # no modification needed when unique
            new_article.append(ref.group())
            continue

        if payload in seen:
            # ignore duplicated payload body
            new_article.append('<ref name="{}" />'.format(db.get_shortname(payload)))
        else:
            if not has_name_attribute(ref):
                new_article.append(
                    '<ref name="{}">{}</ref>'.format(db.get_shortname(payload), payload)
                )
            else:
                new_article.append(ref.group())

            seen.add(payload)

    new_article.append(article[idx:])  # the last segment
    return (''.join(new_article), list(duplicated_refs))

def menu(prompt: str, default: int, options: List[str]) -> int:
    """Return choice or throw SystemExit, 1 <= choice <= len(options)."""
    print(prompt)
    for i, op in enumerate(options):
        print('[{}] {}{}'.format(i + 1, op, ' (default)' if i + 1 == default else ''))

    if not 1 <= (choice := int(input('> ') or default)) <= len(options):
        raise SystemExit('Invalid choice!')
    return choice

def main():
    print('{:=<40}\n{:^40}\n{:=<40}'.format('', 'Wikipedia Duplicated Citations Merger', ''))
    ch = menu('\nHow do you wish to provide the input?', 2,
            ['Load from file ...', 'Paste it here directly.'])
    file_input = input('Please provide the file name to load: ') if ch == 1 else 0
    # TODO: file completion?

    ch = menu('\nHow do you wish to get the result?', 3,
            ['Save the result to \'result.txt\'.',
                'Save the result to ...',
                'Display it here directly.'])
    file_output = 'result.txt' if ch == 1 \
                else input('Please provide the file name to save: ') if ch == 2 \
                else ''

    if file_input == 0:
        print('\nPaste your wiki article source code here:')
        print('Press CTRL + D when completed.')
        print('{:=<40}'.format(''))

    new_article, merged_refs = merge(open(file_input).read())
    if file_output:
        open(file_output, 'w').write(new_article)
    else:
        print('\n\nHere\'s the result:\n{:=<40}'.format(''))
        print(new_article)

    print('{:=<40}'.format(''))
    if len(merged_refs) == 0:
        print('No duplicated references detected.')
    else:
        print('Successfully merged {} refs:'.format(len(merged_refs)))
        print("- '{}'".format("'\n- '".join(merged_refs)))


if __name__ == '__main__':
    main()



# Testcases:
"""
'<ref></ref>'
'<ref> a < << </ </r </re </ref <ref>a<ref>a </ref>'
'<ref> a </ref><ref> b </ref>'
'<ref n = 1 name = NAME > a </ref>'
'<ref name="NAME">a</ref>'
'<ref name = "NAME" />'
'<ref name = "NAME" /><ref></ref>'
'aa aa<ref>content 1</ref>bb bb<ref name=N1>content 2</ref>cc cc<ref>content 1</ref>dd dd<ref name=N2 />ee ee<ref>content 2</ref>ff ff<ref name=N1>content 2</ref>gg gg<ref name=N3>content 3</ref>hh hh<ref>content 4</ref>ii ii'
"""

# Old pattern:
#REF_PATTERN = re.compile(r'<ref\b([^>]*)(?<!/)>(([^<]|<(?!/ref>))*)</ref>', re.DOTALL)
