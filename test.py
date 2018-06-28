# coding: utf-8
from __future__ import unicode_literals


def test_valid(cldf_dataset, cldf_logger):
    assert cldf_dataset.validate(log=cldf_logger)

# "From the 400-item list we removed obvious recent introductions (such as
# 'corn') and known loans from non-Alor-Pantar languages (such as
# proto-Austro- nesian *takaw 'to steal'). We also removed several items for
# which data were missing for more than half of the twelve languages in the
# sample or which were largely redundant (e.g., we only included 'dolphin'
# and not 'whale' because the two were the same for most languages). The
# remaining 351 lexical items were coded numerically for cognacy as described
# above. Crucially, detectable intra- family borrowings were coded as distinct
# cognate classes as described above. In addition to these twelve languages, we
# also included proto-Alor-Pantar as a dis- tinct taxon, coding each of the 97
# lexical items in the dataset for which pAP forms have been reconstructed. Each
# lexical item that is a regular reflex of a pAP recon- struction was coded as
# belonging to the same cognate class as the pAP recon- struction. Tis process
# resulted in a 13 × 351 matrix (13 × 351 = 4,563 character states)."

def test_parameters(cldf_dataset, cldf_logger):
    # Should be 331 words in the downloadable datafile but the conception
    # wordlist has 398 because the authors removed words from the dataset for
    # various reasons (see above). AND we have 7 duplicate words, so the count
    # reduces further
    assert len(list(cldf_dataset['ParameterTable'])) == 398

    params = {c['Parameter_ID'] for c in cldf_dataset['FormTable']}
    assert len(params) == 398

def test_languages(cldf_dataset, cldf_logger):
    assert len(list(cldf_dataset['LanguageTable'])) == 13

def test_cognates(cldf_dataset, cldf_logger):
    # not matching what is described in the paper
    assert len(list(cldf_dataset['CognateTable'])) == 4086

    cogsets = {c['Cognateset_ID'] for c in cldf_dataset['CognateTable']}
    assert len(cogsets) == 2377
