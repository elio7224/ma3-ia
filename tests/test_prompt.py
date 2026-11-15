"""Le prompt système contient l'aide-mémoire grandMA3 et l'index du show."""
import config


def test_prompt_contient_memo_et_index():
    t = config.texte_systeme("SECTION MACROS : 2002=\"Test\"")
    assert "AIDE-MÉMOIRE GRANDMA3" in t and "Preset 4.12" in t
    assert t.rstrip().endswith('2002="Test"')
    assert "{memo}" not in t and "{index}" not in t


def test_bloc_systeme_mis_en_cache():
    bloc = config.bloc_systeme("index")
    assert bloc[0]["cache_control"] == {"type": "ephemeral"}
