from backend.api.projects import fuzzy_text_match

def test_search_is_case_insensitive_for_cyrillic():
    assert fuzzy_text_match("алексей", "Алексей")
    assert fuzzy_text_match("АЛЕКСЕЙ", "Алексей")

def test_search_finds_typo():
    assert fuzzy_text_match("фанарик", "фонарик")
    assert fuzzy_text_match("фонариик", "фонарик")

def test_short_queries_stay_prefix_or_substring_only():
    assert fuzzy_text_match("фон", "фонарик")
    assert not fuzzy_text_match("кот", "комод")
