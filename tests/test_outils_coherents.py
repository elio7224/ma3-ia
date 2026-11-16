"""Chaque outil déclaré à l'IA a sa fonction, et l'ancien outil generate_fx_grid a bien disparu."""
import outils


def test_chaque_outil_a_sa_fonction():
    assert {t["name"] for t in outils.TOOLS} == set(outils.FUNCS)


def test_generate_fx_grid_supprime():
    assert "generate_fx_grid" not in outils.FUNCS
