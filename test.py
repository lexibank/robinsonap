def test_valid(cldf_dataset, cldf_logger):
    assert cldf_dataset.validate(log=cldf_logger)


# "From the 400-item list we removed obvious recent introductions (such as
# 'corn') and known loans from non-Alor-Pantar languages (such as
# proto-Austronesian *takaw 'to steal'). We also removed several items for
# which data were missing for more than half of the twelve languages in the
# sample or which were largely redundant (e.g., we only included 'dolphin'
# and not 'whale' because the two were the same for most languages). The
# remaining 351 lexical items were coded numerically for cognacy as described
# above. Crucially, detectable intra- family borrowings were coded as distinct
# cognate classes as described above. In addition to these twelve languages,
# we also included proto-Alor-Pantar as a distinct taxon, coding each of the 97
# lexical items in the dataset for which pAP forms have been reconstructed.
# Each lexical item that is a regular reflex of a pAP reconstruction was
# coded as belonging to the same cognate class as the pAP reconstruction.
# This process resulted in a 13 × 351 matrix (13 × 351 = 4,563 character
# states)."


def test_parameters(cldf_dataset):
    # Should be 331 words in the downloadable datafile but the conception
    # wordlist has 398 because the authors removed words from the dataset for
    # various reasons (see above). AND we have 7 duplicate words, so the count
    # reduces further
    assert len(list(cldf_dataset["ParameterTable"])) == 398

    params = {c["Parameter_ID"] for c in cldf_dataset["FormTable"]}
    assert len(params) == 398


def test_languages(cldf_dataset):
    assert len(list(cldf_dataset["LanguageTable"])) == 13


def test_forms(cldf_dataset):
    # check that overrides in lexeme.csv are taken into account
    f = [
        f for f in cldf_dataset["FormTable"] if f["Form"] == 'alumanεmε'
    ]

    assert len(f) == 1
    assert f[0]["Parameter_ID"] == "56_civetcat"
    assert f[0]["Language_ID"] == "adang"
    assert f[0]["Form"] == "alumanεmε"


def test_cognates(cldf_dataset):
    cogsets = [
        c for c in cldf_dataset["CognateTable"] if c['Cognateset_ID'] == '100_fat-0'
    ]
    assert len(cogsets) == 2
