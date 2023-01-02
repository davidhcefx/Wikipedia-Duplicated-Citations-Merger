from typing import List, Pattern, Match
import wikipedia_duplicated_citations_merger as merger


COMPLEX_REF = """aa aa<ref>content 1</ref>bb bb<ref name="N1">content N1</ref>cc cc<ref>content
1</ref>dd dd<ref name="N2" />ee ee<ref>content N1</ref>ff ff<ref name="N1">content N1
</ref>gg gg<ref name="N3">content N3</ref>hh hh<ref>content 4</ref>ii ii"""


def find_all_matches(pattern: Pattern[str], text: str) -> List[Match[str]]:
    """Find all matches in text using pattern."""
    res: List[Match[str]] = []
    idx = 0
    while m := pattern.search(text, idx):
        res.append(m)
        idx = m.end()

    return res

def test_ref_regex():
    """Test the regex of ref tags."""
    refs = [
        ('<ref></ref>', [(0, 11)]),   # empty payload
        ('<ref>+</ref>', [(0, 12)]),  # non-empty payload
        ('<ref name="NA M E!$%&()*,-.:;@[]^_`{|}~">a</ref>', [(0, 48)]),  # name attr
        ('<ref name="">a</ref>', [(0, 20)]),   # empty name attr
        ('<ref  >a</ref>', [(0, 14)]),         # black attr
        ('<ref name="N" />a</ref>', []),   # skipped (self-contained)
        ('<referen_ce >a</ref>', []),  # fake ref
        ('<ref>a</ref>b</ref>', [(0, 12)]),                   # multiple end tag
        ('<ref>a</ref> <ref>b</ref>', [(0, 12), (13, 25)]),   # multiple refs
        (COMPLEX_REF, [(5, 25), (30, 61), (66, 86),
                       (113, 134), (139, 171),  # second line
                       (176, 207), (212, 232)]),  # third line
    ]
    for text, result in refs:
        matches = find_all_matches(merger.REF_PATTERN, text)
        assert result == list(map(lambda m: m.span(), matches)), 'Failed for {}'.format(text)

def test_name_regex():
    """Test the regex for extracting name attribute within ref tags."""
    refs = [
        # quoted
        ('<ref name="NA M E!$%&()*,-.:;@[]^_`{|}~">a</ref>', ['"NA M E!$%&()*,-.:;@[]^_`{|}~"']),
        ('<ref name="" group="G">a</ref>', ['""']),  # quoted empty with group
        ('<ref name=N group=G>a</ref>', ['N']),       # unquoted
        ('<ref name = N group = G >a</ref>', ['N']),  # unquoted with spaces
        ('<ref name = "NAME" /><ref></ref>', [None]),  # skipped
        (COMPLEX_REF, [None, '"N1"', None, None, '"N1"', '"N3"', None]),
    ]
    for text, result in refs:
        names = map(
            lambda n_str: m.group(1) if (m := merger.NAME_ATTR_PATTERN.search(n_str)) else None,
            map(
                lambda match: match.group('name'),
                find_all_matches(merger.REF_PATTERN, text)))
        assert result == list(names), 'Failed for {}'.format(text)
