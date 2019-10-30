import re
from pathlib import Path

import attr
from clldutils.misc import slug
# from clldutils.text import split_text, strip_brackets
from pylexibank import Dataset as BaseDataset
from pylexibank import Language as BaseLanguage
from pylexibank import FormSpec


gloss_quotes = re.compile(r"'.*?'", re.UNICODE)


@attr.s
class Language(BaseLanguage):
    # the tokens used as language identifiers by Robinson and Holton
    Token = attr.ib(default=None)


class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "robinsonap"
    language_class = Language

    form_spec = FormSpec(
        brackets={"[": "]", "{": "}", "(": ")"},
        separators=";/,",
        missing_data=('?', '-', '', ''),
        strip_inside_brackets=True
    )
    
    def cmd_makecldf(self, args):
        args.writer.add_sources()

        languages = args.writer.add_languages(
            lookup_factory='Token',
        )

        concepts = args.writer.add_concepts(
            id_factory=lambda c: c.id.split('-')[-1]+ '_' + slug(c.english),
            lookup_factory="Name"
        )

        # read data from AP_lexicon_coded.txt
        seen = []
        for f in ("AP_lexicon_coded.txt", "AP_lexicon.txt"):
            for row in self.raw_dir.read_csv(f, dicts=True, delimiter="\t"):
                concept = row['English'].lower().strip().replace(", ", "/")
                # skip rows in AP_lexicon.txt that we've already seen
                # in AP_lexicon_coded.txt
                if f == 'AP_lexicon.txt' and concept in seen:
                    continue

                # manually catch "chase away". There are two glosses for this:
                #   367   "chase away"
                #   368   "chase away, expel"
                # ...-> 367 looks only partially complete and 368 contains all
                # forms in 367, so ignore 367.
                if row['English'] == 'chase away':
                    continue

                if row['English']:
                    # store lexicon IDs for the cognate row.
                    lexicon_ids = {}

                    for lang in languages:
                        assert concept in concepts, 'bad concept %s' % concept

                        # preprocess value
                        value = row[lang].replace("‘", "'").replace("’", "'")
                        # remove the reconstruction mark (for proto-AP)
                        value = value.lstrip("*")
                        # strip glosses (between single quotes); 
                        # strip_brackets() can't be used here because in 
                        # case of unclosed brackets it strips away all the 
                        # contents until the end of the string, which makes 
                        # sense for parentheses and the like but can't be used 
                        # here, as the single quote can be a glottal stop and 
                        # as a word can (potentially) have more than one 
                        # glottal stop (and this would strip all the sounds in 
                        # the middle)
                        if value.endswith("'"):
                            value = gloss_quotes.sub("", value)

                        # remove leading & trailing spaces
                        value = value.strip().lstrip()

                        # if the stripped form starts and ends with a slash,
                        # it is a leftover from a transcription, let's clean 
                        # it (it could be done with the orthographic profile,
                        # but this could hide errors in parsing multiple 
                        # forms, and in any case this is more adequate as we 
                        # get the correct value)
                        if value.startswith("/") and value.endswith("/"):
                            value = value[1:-1]

                        lex = args.writer.add_forms_from_value(
                            Language_ID=languages[lang],
                            Parameter_ID=concepts[concept],
                            Value=value,
                            Source=["Robinson2012"],
                        )
                        if len(lex) >= 1:
                            # it looks like only the first lexemes of combined 
                            # forms have cognates, so only add the first one.
                            lexicon_ids[lang] = lex[0]

                    seen.append(concept)

                else:  # cognates...
                    lastword = seen[-1]  # find the last word..
                    for lang in languages:
                        # find lexical ids belonging to this language & gloss.
                        lex = lexicon_ids.get(lang)
                        if lex and row[lang]:
                            if int(row[lang]) not in range(0, 12):
                                raise ValueError(
                                    "Invalid cognate id: %s" % row[lang]
                                )
                            args.writer.add_cognate(
                                lexeme=lex,
                                Cognateset_ID="%s-%s" % (concepts[lastword], row[lang]),
                                Source=["Robinson2012"]
                            )


    def cmd_download(self, **kw):
        if not self.raw_dir.exists():
            self.raw_dir.mkdir()
        files = ["AP_lexicon_coded.txt", "AP_lexicon.txt"]
        self.raw_dir.download_and_unpack(
            "http://booksandjournals.brillonline.com/upload/"
            "robinson_10.116322105832-20120201.zip?itemId="
            "/content/journals/10.1163/22105832-20120201&mimeType=application/octet-stream",
            *[Path(f) for f in files],
            log=self.log
        )
