from typing import List, Tuple, Pattern, Match
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
        ('<ref></ref>', [(0, 11)]),  # empty payload
        ('<ref> a < << </ </r </re </ref <ref>a<ref>a </ref>', [(0, 50)]),  # confusing end tag
        ('<ref name="NA M E+" group="G">a</ref>', [(0, 37)]),  # ref with name attribute
        ('<ref name = "NAME" /><ref></ref>', [(21, 32)]),      # skipped ref tag
        ('<ref>a</ref> <ref>b</ref>', [(0, 12), (13, 25)]),    # multiple refs
        (COMPLEX_REF, [(5, 25), (30, 61), (66, 86),
                       (113, 134), (139, 171),  # second line
                       (176, 207), (212, 232)]),  # third line
    ]
    for text, result in refs:
        matches = find_all_matches(merger.REF_PATTERN, text)
        assert result == list(map(lambda m: m.span(), matches))

def test_name_regex():
    """Test the regex for extracting name attribute within ref tags."""
    refs = [
        ('<ref n = 1 name = NAME _name = 2 >a</ref>', ['NAME']),  # unquoted with spaces
        ('<ref name=NA M E+ group="G">a</ref>', ['NA']),          # unquoted, leaving spaces outside
        ('<ref name="NA M E+" group="G">a</ref>', ['"NA M E+"']),  # quoted
        ('<ref name = "NAME" /><ref></ref>', [None]),              # skipped ref tag
        (COMPLEX_REF, [None, '"N1"', None, None, '"N1"', '"N3"', None]),
    ]
    for text, result in refs:
        names = map(
            lambda n_str: m.group(1) if (m := merger.NAME_ATTR_PATTERN.search(n_str)) else None,
            map(
                lambda match: match.group('name'),
                find_all_matches(merger.REF_PATTERN, text)))
        assert result == list(names)
