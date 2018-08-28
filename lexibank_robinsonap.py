# coding=utf-8
from __future__ import unicode_literals, print_function

from clldutils.path import Path
from clldutils.text import split_text, strip_brackets
from clldutils.misc import slug

from pylexibank.dataset import Metadata
from pylexibank.dataset import Dataset as BaseDataset
from pylexibank.util import getEvoBibAsBibtex

import re

class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = 'robinsonap'
    DEST = ['AP_lexicon_coded.txt', 'AP_lexicon.txt']

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

        # Read data from 'AP_lexicon.txt', collecting information for concepts that were
        # manually excluded by the authors from 'AP_lexicon_coded.txt'
        rows = self.raw.read_tsv('AP_lexicon.txt')
        header = True
        for row in rows:
            if header:
                fields = row
                header = False
                continue

            # build a dictionary of the forms for the entry
            entry = {k:{'form':v} for k, v in zip(fields, row)}

            # remove non Alor-Pantar fields (keeping the English one as gloss)
            entry.pop('Number')

            # fix/normalize the gloss
            gloss = entry.pop('English')['form']
            gloss = gloss.replace(',', '/')
            gloss = gloss.lower().strip()

            # append to vocabulary if missing
            if gloss not in vocabulary:
                vocabulary[gloss] = entry

        # remove problematic gloss
        vocabulary.pop('chase away')

        with self.cldf as ds:
            ds.add_sources()
            ds.add_languages()
            ds.add_concepts(id_factory=lambda c: slug(c.label))

            # add forms
            for concept in sorted(vocabulary):
                for lang in sorted(vocabulary[concept]):
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

                        # if the stripped form starts and ends with a slash, it is a
                        # leftover from a transcription, let's clean it (it could be
                        # done with the orthographic profile, but this could hide errors
                        # in parsing multiple forms, and in any case this is more adequate
                        # as we get the correct value)
                        if form.startswith('/') and form.endswith('/'):
                            form = form[1:-1]

                        # skip over empty of invalid forms
                        if not form:
                            continue
                        if form in ['-', '--']:
                            continue

                        for row in ds.add_lexemes(
                            Local_ID=lang,
                            Language_ID=lang,
                            Parameter_ID=slug(concept),
                            Value=form,
                            Source=['Robinson2012'],
                        ):
                            if 'cogid' in vocabulary[concept][lang]:
                                ds.add_cognate(
                                    lexeme=row,
                                    Cognateset_ID='%s-%s' % (slug(concept), vocabulary[concept][lang]['cogid']),
                                    Source=['Robinson2012'],
                                    Alignment_Source='List2014e')

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
