#! /usr/bin/env python3
# Merge duplicated Wikipedia references/citations. Written by davidhcefx, 2022.4.10.
from typing import Dict, List, Tuple, Set, Optional, Pattern, Match, Any
from string import digits
import re
import json
from hashlib import md5
import requests
try:
    import readline  # for filename autocompletion
    readline.parse_and_bind('tab: complete')  # type: ignore[attr-defined]
except ModuleNotFoundError:
    pass

REF_PATTERN = re.compile(r'<ref\b(?P<name>[^>]*)(?<!/)>(?P<pay>.*?)</ref>', re.DOTALL)
NAME_ATTR_PATTERN = re.compile(r'name\s*=\s*(\w+|"[^"]*?")', re.DOTALL)  # name attribute in <ref>
# https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
URL_PATTERN = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)')
TEMPLATE_NAMES: Optional[Pattern[str]] = None
TEMPLATE_PARAMS: Optional[Pattern[str]] = None


class CitationDatabase:
    """
    Associate citation-payloads with its short-names.
    A citation-payload is the part enclosed by <ref></ref>.
    """
    def __init__(self) -> None:
        self.shortnames: Dict[str, str] = dict()  # map a payload to its short name

    def add(self, payload: str, shortname: str) -> None:
        assert shortname not in self.shortnames.values(), \
            f"Name collision '{shortname}'. Check the article or try adding more hash digits."
        self.shortnames[payload] = shortname

    def has(self, payload: str) -> bool:
        # we simply query with the exact text here, but one can extend to other logics
        # such as URL/DOI detection or to ignore whitespace differences.
        return payload in self.shortnames

    def get_shortname(self, payload: str) -> str:
        return self.shortnames[payload] if self.has(payload) else ''


def generate_short_name(payload: str) -> str:
    """Generate wiki-accepted short-names from citation-payloads."""
    global TEMPLATE_NAMES
    if TEMPLATE_NAMES is None:
        temp_names = 'book|arXiv|AV media|AV media notes|bioRxiv|conference|encyclopedia|episode|interview|magazine|mailing list|journal|map|news|newsgroup|podcast|press release|report|serial|sign |speech|techreport|thesis|web'
        TEMPLATE_NAMES = re.compile(r'[cC]ite ({})'.format(temp_names))

    global TEMPLATE_PARAMS
    if TEMPLATE_PARAMS is None:
        temp_params = 'access-date|agency|archive-date|archive-url|arxiv|asin|asin-tld|at|author|author-link|author-link1|author-link2|author-link3|author-link4|author-link5|author-mask|author-mask1|author-mask2|author-mask3|author-mask4|author-mask5|author2|authors|bibcode|bibcode-access|biorxiv|book-title|cartography|chapter|chapter-format|chapter-url|chapter-url-access|citeseerx|class|conference|conference-url|credits|date|department|display-authors|display-editors|display-translators|docket|doi|doi-access|doi-broken-date|edition|editor|editor-first|editor-first1|editor-first2|editor-first3|editor-first4|editor-first5|editor-last|editor-last1|editor-last2|editor-last3|editor-last4|editor-last5|editor-link|editor-link1|editor-link2|editor-link3|editor-link4|editor-link5|editor-mask1|editor-mask2|editor-mask3|editor-mask4|editor-mask5|editor1-first|editor1-last|editor1-link|editor2-first|editor2-last|editor2-link|editor3-first|editor3-last|editor3-link|editor4-first|editor4-last|editor4-link|editor5-first|editor5-last|editor5-link|editors|eissn|encyclopedia|episode|episode-link|eprint|event|first|first1|first2|first3|first4|first5|format|hdl|hdl-access|host|id|inset|institution|interviewer|isbn|ismn|issn|issue|jfm|journal|jstor|jstor-access|language|last|last1|last2|last3|last4|last5|lccn|location|magazine|mailing-list|map|map-url|medium|message-id|minutes|mode|mr|name-list-style|network|newsgroup|no-pp|number|oclc|ol|ol-access|orig-date|osti|osti-access|others|page|pages|people|pmc|pmc-embargo-date|pmid|postscript|publication-date|publication-place|publisher|quote|quote-page|quote-pages|ref|registration|rfc|s2cid|s2cid-access|sbn|scale|script-chapter|script-quote|script-title|season|section|sections|series|series-link|series-no|ssrn|station|subject|subject-link|subject-link2|subject-link3|subject-link4|subject2|subject3|subject4|time|title|title-link|trans-chapter|trans-quote|trans-title|transcript|transcript-url|translator-first1|translator-first2|translator-first3|translator-first4|translator-first5|translator-last1|translator-last2|translator-last3|translator-last4|translator-last5|translator-link1|translator-link2|translator-link3|translator-link4|translator-link5|translator-mask1|translator-mask2|translator-mask3|translator-mask4|translator-mask5|type|url|url-access|url-status|via|volume|website|work|year|zbl|zbl'
        TEMPLATE_PARAMS = re.compile(r'\|\s*({})\s*='.format(temp_params))

    # remove urls, wiki template names and template parameters
    s = TEMPLATE_PARAMS.sub('', TEMPLATE_NAMES.sub('', URL_PATTERN.sub('', payload)))
    words = ''.join(re.findall(r'\w', s))
    # compute md5 to avoid collisions (11 - 8 = 3 hash digits)
    name = words[:8] + md5(payload.encode()).hexdigest()

    return '{}{}'.format('_' if name[0] in digits else '', name[:11])

def get_duplicated_refs(article: str, db: CitationDatabase) -> Set[str]:
    """Return a set of duplicated citation-payloads; update db along the way."""
    result = set()
    idx = 0
    while ref := REF_PATTERN.search(article, idx):
        name_str, payload = ref.group('name', 'pay')
        if db.has(payload):
            result.add(payload)
        else:
            # parse or generate shortname
            shortname = n.group(1).strip('"') if (n := NAME_ATTR_PATTERN.search(name_str)) \
                else generate_short_name(payload)
            db.add(payload, shortname)

        idx = ref.end()

    return result

def has_name_attribute(ref: Match[str]) -> bool:
    return NAME_ATTR_PATTERN.search(ref.group('name')) is not None

def merge(article: str) -> Tuple[str, int, List[str]]:
    """
    Merge duplicated refs in wiki source code.
    Return new article, merge counts and a list of duplicated refs.
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
    merge_count = 0
    idx = 0
    while ref := REF_PATTERN.search(article, idx):
        new_article.append(article[idx:ref.start()])  # output the previous segment
        idx = ref.end()
        payload = ref.group('pay')
        if payload not in duplicated_refs:
            # no modification needed if it's unique
            new_article.append(ref.group())
            continue

        if payload in seen:
            # ignore duplicated payload body
            new_article.append('<ref name="{}" />'.format(db.get_shortname(payload)))
            merge_count += 1
        else:
            if not has_name_attribute(ref):
                new_article.append(
                    '<ref name="{}">{}</ref>'.format(db.get_shortname(payload), payload)
                )
            else:
                new_article.append(ref.group())

            seen.add(payload)

    new_article.append(article[idx:])  # the last segment
    return (''.join(new_article), merge_count, list(duplicated_refs))

def extract_wikitext(url: str) -> str:
    """Extract Wikitext from a wiki url."""
    if not (match := re.fullmatch(r'(?P<host>.+)/wiki/(?P<page>.+)', url)):
        raise SystemExit('Invalid or unrecognized wiki URL.')
    query = {
        'action': 'parse',
        'prop': 'wikitext',
        'format': 'json',
        'formatversion': '2',
        'page': requests.utils.unquote(match.group('page')),  # type: ignore
    }
    if r := requests.get(match.group('host') + '/w/api.php', query, timeout=5):
        return str(json.loads(r.text)['parse']['wikitext'])
    return ''

def menu(prompt: str, default: int, options: List[str]) -> int:
    """Return choice or throw SystemExit, 1 <= choice <= len(options)."""
    print(prompt)
    for i, op in enumerate(options):
        print('[{}] {}{}'.format(i + 1, op, ' (default)' if i + 1 == default else ''))

    if not 1 <= (choice := int(input('> ') or default)) <= len(options):
        raise SystemExit('Invalid choice!')
    return choice

def main() -> None:
    print('{:=<40}\n{:^40}\n{:=<40}'.format('', 'Wikipedia Duplicated Citations Merger', ''))
    ch = menu('\nHow do you wish to provide the input?', 3,
              ['Fetch from wikipedia', 'Load from file ...', 'Paste it here directly.'])
    src_input: Tuple[str, Any] = ('u', input('URL of the wiki page: ')) if ch == 1 \
        else ('f', input('Please provide the file name to load: ')) if ch == 2 \
        else ('0', 0)

    ch = menu('\nHow do you wish to get the result?', 3,
              ['Save the result to \'result.txt\'.',
               'Save the result to ...',
               'Display it here directly.'])
    file_output = 'result.txt' if ch == 1 \
        else input('Please provide the file name to save: ') if ch == 2 \
        else ''

    if src_input[0] == '0':
        print('\nPaste your wiki article source code here:')
        print('Press CTRL + D (or CTRL + Z plus Enter) when completed.\n{:=<40}'.format(''))

    article = extract_wikitext(src_input[1]) if src_input[0] == 'u' else open(src_input[1]).read()
    new_article, merge_count, duplicated_refs = merge(article)

    if file_output:
        open(file_output, 'w').write(new_article)
    else:
        print('\n\nHere\'s the result:\n{:=<40}'.format(''))
        print(new_article)

    print('{:=<40}'.format(''))
    if merge_count == 0:
        print('No duplicated references detected.')
    else:
        print('Successfully merged {} references. Duplicated ones are:'.format(merge_count))
        print("- '{}'".format("'\n- '".join(duplicated_refs)))


if __name__ == '__main__':
    main()


# Testcases:
"""
<ref></ref>
<ref> a < << </ </r </re </ref <ref>a<ref>a </ref>
<ref> a </ref><ref> b </ref>
<ref n = 1 name = NAME > a </ref>
<ref name="NA M E">a</ref>
<ref name=NA M E ></ref>
<ref name = "NAME" />
<ref name = "NAME" /><ref></ref>
aa aa<ref>content 1</ref>bb bb<ref name=N1>content 2</ref>cc cc<ref>content 1</ref>dd
  dd<ref name=N2 />ee ee<ref>content 2</ref>ff ff<ref name=N1>content 2</ref>gg
  gg<ref name=N3>content 3</ref>hh hh<ref>content 4</ref>ii ii
"""

# Old patterns:
#REF_PATTERN = re.compile(r'<ref\b([^>]*)(?<!/)>(([^<]|<(?!/ref>))*)</ref>', re.DOTALL)
#OTHER_IGNORES = re.compile(r'(https?|www\.|\.(org|com)|(web\.)?archive|cgi|youtube|google|isbn)')
