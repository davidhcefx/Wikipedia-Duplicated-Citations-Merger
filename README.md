# Wikipedia Duplicated Citations Merger

[![Test](https://github.com/davidhcefx/Wikipedia-Duplicated-Citations-Merger/actions/workflows/python-test.yml/badge.svg)](https://github.com/davidhcefx/Wikipedia-Duplicated-Citations-Merger/actions/workflows/python-test.yml)

[The free encyclopedia][wikipedia] already stated that:

> "If you simply copy exactly the same reference and citation, the citation will become **duplicated**."

Unfortunately, it's common to spot **duplicated citations** in the wild, for example within the page [David Green][] and [國旗][]. The best way to resolve this issue is by using [named references][duplicated], which is exactly how this tool works!

For example, it would transfrom the following Wikitext:
```wikitext
These are two<ref>{{cite book|title=LibreOffice for Starters|edition=First|publisher=Flexible Minds|location=Manchester|year=2002|p=18}}</ref>
citations<ref>{{cite book|title=LibreOffice for Starters|edition=First|publisher=Flexible Minds|location=Manchester|year=2002|p=18}}</ref>.
```
to
```wikitext
These are two<ref name="LibreOff56c">{{cite book|title=LibreOffice for Starters|edition=First|publisher=Flexible Minds|location=Manchester|year=2002|p=18}}</ref>
citations<ref name="LibreOff56c" />.
```

which not only reduces some text, but also prevents the *reference list* from bloating.


## Usage

<img src="https://user-images.githubusercontent.com/23246033/163454251-ff1f05a2-5909-450b-81b4-573497347575.png" alt="screenshot" width=75%>

> Requires [Python 3.8][] or later.


## Limitations

- Can only do *exact match* on `<ref>` tags, i.e. it's not smart enough to merge two references having a high similarity.
  - However, it's quite easy to provide such feature by extending the `CitationDatabase` class.


[wikipedia]: https://en.wikipedia.org/wiki/Wikipedia
[duplicated]: https://en.wikipedia.org/wiki/Template:Duplicated_citations
[Python 3.8]: https://www.python.org/downloads/release/python-380/
[David Green]: https://en.wikipedia.org/w/index.php?title=David_Green_(social_entrepreneur)&oldid=936659277
[國旗]: https://zh.wikipedia.org/w/index.php?title=%E5%9B%BD%E6%97%97&oldid=71148025
