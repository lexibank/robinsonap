# coding=utf-8
from __future__ import unicode_literals, print_function

from clldutils.path import Path
from clldutils.text import split_text, strip_brackets

from clldutils.path import Path
from pylexibank.dataset import Metadata
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank.lingpy_util import getEvoBibAsBibtex

import re

class Dataset(BaseDataset):
    dir = Path(__file__).parent
    DEST = ['AP_lexicon_coded.txt']

    def cmd_install(self, **kw):
        # read data from 'AP_lexicon_coded.txt' and collect it; self.raw has no
        # DictReader method, so we need to emulate it (read the header to get field names, etc);
        # given the file structure of double lines, we keep an internal account of
        # which line we are in (form or cogid), in order to make the loop simple to
        # understand
        vocabulary = {}
        rows = self.raw.read_tsv('AP_lexicon_coded.txt')
        header = True
        in_form = True # switching from form/cogid
        for row in rows:
            if header:
                fields = row
                header = False
                continue

            # using the English gloss as key; replacing commas in the
            # English gloss by slashes, in order to use CSV without quoting,
            # and lowering
            if in_form:
                # build a dictionary of the forms for the entry
                entry = {k:{'form':v} for k, v in zip(fields, row)}

                # remove non Alor-Pantar fields (keeping the English one as gloss)
                [entry.pop(key) for key in ['Number', '']]

                # fix/normalize the gloss
                gloss = entry.pop('English')['form']
                gloss = gloss.replace(',', '/')
                gloss = gloss.lower().strip()

                # append to vocabulary
                vocabulary[gloss] = entry

                # next line is not forms (it is cogids)
                in_form = False
            else:
                # build a dictionary of the cogids for the entry
                entry = {k:v for k, v in zip(fields, row)}

                # remove non Alor-Pantar fields and update the data with the cogids
                [entry.pop(key) for key in ['English', 'Number', '']]

                # update the vocabulary/data
                for lang, cogid in entry.items():
                    vocabulary[gloss][lang]['cogid'] = cogid

                # next line is not cogids (it is forms)
                in_form = True

        with self.cldf as ds:
            ds.add_sources(self.raw.read('sources.bib'))

            # add languages to dataset
            for lang in self.languages:
                ds.add_language(
                    ID=lang['NAME'], # will add the 'robinsonap-' prefix
                    glottocode=lang['GLOTTOCODE'],
                    name=lang['GLOTTOLOG_NAME'])

            # add concepts to the dataset
            for concept_id in self.conceptlist.concepts:
                concept = self.conceptlist.concepts[concept_id]
                ds.add_concept(
                    ID=concept.english, # will add the prefix
                    conceptset=concept.concepticon_id,
                    gloss=concept.english,
                    concepticon_gloss=concept.concepticon_gloss)

            # add forms
            for concept in sorted(vocabulary):
                for lang in vocabulary[concept]:
                    # replace commas by slashes (so we don't need lots of
                    # escaping and quoting) and correct bad entries;
                    # lexibank `value` is actually `form` in the source
                    value = vocabulary[concept][lang]['form'].replace(',', '/')
                    if value in self.lexemes:
                        value = self.lexemes[value]

                    for form in split_text(value, separators='/'):
                        # replace single quote characters
                        form = form.replace("‘", "'")
                        form = form.replace("’", "'")

                        # remove the reconstruction mark (for proto-alor-pantar)
                        if form.startswith('*'):
                            form = form[1:]

                        # strip brackets, parentheses, etc.
                        form = strip_brackets(form, brackets={'[':']', '{':'}', '(':')'})

                        # strip glosses (between single quotes); strip_brackets() can't be
                        # used here because in case of unclosed brackets it strips away
                        # all the contents until the end of the string, which makes sense
                        # for parentheses and the like but can't be used here, as the
                        # single quote can be a glottal stop and as a word can (potentially)
                        # have more than one glottal stop (and this would strip all the
                        # sounds in the middle)
                        if form.endswith("'"):
                            gloss_quotes = re.compile(r"'.*?'", re.UNICODE)
                            form = re.sub(gloss_quotes, '', form)

                        # remove multiple spaces, plurs leading&trailing spaces
                        form = re.sub('\s+', ' ', form).strip()

                        # if the stripped form starts and ends with a slash, it is a leftover
                        # from a transcription, let's clean it (it could be done with the
                        # orthographic profile, but this could hide errors in parsing
                        # multiple forms, and in any case this is more adequate as we get
                        # the correct value)
                        if form.startswith('/') and form.endswith('/'):
                            form = form[1:-1]

                        # skip over empty of invalid forms
                        if not form:
                            continue
                        if form in ['-', '--']:
                            continue

                        tokens = self._tokenizer('IPA', form)
                        for row in ds.add_lexemes(
                            Language_ID=lang,
                            Parameter_ID=concept,
                            Value=form,
                            Source=['Robinson2012'],
                            Segments=tokens):
                            ds.add_cognate(
                                lexeme=row,
                                Cognateset_ID='%s-%s' % (concept, vocabulary[concept][lang]['cogid']),
                                Cognate_source=['Robinson2012'],
                                Alignment_source=['List2014e'])

            ds.align_cognates()


    def cmd_download(self, **kw):
        if not self.raw.exists():
            self.raw.mkdir()
        self.raw.download_and_unpack(
            'http://booksandjournals.brillonline.com/upload/'
            'robinson_10.116322105832-20120201.zip?itemId='
            '/content/journals/10.1163/22105832-20120201&mimeType=application/octet-stream',
            *[Path(f) for f in self.DEST],
            log=self.log)

        self.raw.write('sources.bib', getEvoBibAsBibtex('Robinson2012', 'List2014e', **kw))
