#! /usr/bin/env python3
# Merge duplicated Wikipedia references/citations. Written by davidhcefx, 2022.4.10.
import re
import readline
from typing import Dict, List, Tuple, Set
from hashlib import md5

REF_PATTERN = re.compile(r'<ref\b(?P<name>.*?)(?<!/)>(?P<pay>.*?)</ref>', re.DOTALL)
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

.    def get_shortname(self, payload: str) -> str:
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
    Merge duplicated refs in wiki source; return new article and a list of merged refs.
    There are five kinds of refs: (we merge the 2nd and 4th)
      1) no name unique payload
      2) no name duplicated payload
      3) has name has unique payload
      4) has name has duplicated payload
      5) has name no payload (skipped)
    """
    new_article = []
    merged_refs = []
    db = CitationDatabase()
    duplicated_refs: Set[str] = get_duplicated_refs(article, db)
    seen: Set[str] = set()
    idx = 0
    while ref := REF_PATTERN.search(article, idx):
        new_article.append(article[idx:ref.start()])  # output the previous segment
        idx = ref.end()
        payload = ref.group('pay')
        # unique: no modifications needed
        if payload not in duplicated_refs:
            new_article.append(ref.group())
            continue

        if payload in seen:
            # ignore duplicated payload body
            new_article.append('<ref name="{}" />'.format(db.get_shortname(payload)))
            merged_refs.append(payload)
        else:
            if not has_name_attribute(ref):
                new_article.append(
                    '<ref name="{}">{}</ref>'.format(db.get_shortname(payload), payload)
                )
            else:
                new_article.append(ref.group())

            seen.add(payload)

    new_article.append(article[idx:])  # the last segment
    return (''.join(new_article), merged_refs)

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

    ch = menu('\nHow do you wish to get the result?', 3
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

    new_article, merge_count, new_name_count = merge(open(file_input).read())
    if file_output:
        open(file_output, 'w').write(new_article)
    else:
        print('\n\nHere\'s the result:\n{:=<40}'.format(''))
        print(new_article)

    print('{:=<40}'.format(''))
    print('Merged {} refs, added {} new name attributes.'.format(merge_count, new_name_count))


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
'aa aa<ref>no name</ref>bb bb<ref name=n1>has name</ref>cc cc<ref>no name</ref>dd dd<ref name=n2 />other ref<ref>has name</ref>ee ee<ref name=n1>has name</ref>ff ff<ref name=n3 />gg gg<ref>no name2</ref>hh hh'
"""

# Old pattern:
#REF_PATTERN = re.compile(r'<ref\b([^>]*)(?<!/)>(([^<]|<(?!/ref>))*)</ref>', re.DOTALL)
