"""Le prompt système contient l'aide-mémoire grandMA3 et l'index du show."""
import config


def test_prompt_contient_memo_et_index():
    t = config.texte_systeme("SECTION MACROS : 2002=\"Test\"")
    assert "AIDE-MÉMOIRE GRANDMA3" in t and "Preset 4.12" in t
    assert t.rstrip().endswith('2002="Test"')
    assert "{memo}" not in t and "{index}" not in t


def test_bloc_systeme_mis_en_cache():
    blocs = config.bloc_systeme("SECTION MACROS : 1=\"A\"")
    assert len(blocs) == 2 and all(b["cache_control"] == {"type": "ephemeral"} for b in blocs)
    assert "AIDE-MÉMOIRE" in blocs[0]["text"] and "INDEX" not in blocs[0]["text"]
    assert blocs[1]["text"].startswith("INDEX DU SHOWFILE") and '1="A"' in blocs[1]["text"]
    # Le bloc fixe ne dépend pas de l'index : il reste en cache après un Rescan.
    assert config.bloc_systeme("autre index")[0]["text"] == blocs[0]["text"]


def test_limiter_historique():
    msgs = [{"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(50)]
    r = config.limiter_historique(msgs, 20)
    assert len(r) == 20 and r[0]["role"] == "user" and r[-1]["content"] == "49"
    r = config.limiter_historique(msgs, 5)          # commencerait par un message assistant
    assert r[0]["role"] == "user" and len(r) == 4
    assert config.limiter_historique(msgs[:3], 20) == msgs[:3]
