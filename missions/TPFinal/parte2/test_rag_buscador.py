"""Pruebas del contrato del buscador con normas cambiantes."""

import tempfile
import unittest
from pathlib import Path

from rag_buscador import construir_buscador


class BuscadorNormasTest(unittest.TestCase):
    def test_toma_los_parametros_de_la_carpeta_recibida(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporal:
            ruta = Path(temporal)
            (ruta / "NOR-ADM-01.md").write_text(
                "## NOR-ADM-01 · Registro\n\n§1. El nivel de triage para entrar al box antes del registro "
                "es el parámetro P-ADM-1.", encoding="utf-8")
            parametros = ruta / "parametros.yaml"
            for nivel in (2, 4):
                parametros.write_text(
                    f"parametros:\n- codigo: P-ADM-1\n  valor: {nivel}\n  unidad: nivel\n",
                    encoding="utf-8")
                buscador = construir_buscador(ruta)
                hallados = buscador.recuperar("nivel de triage para box", 2)
                self.assertEqual(len(hallados), 1)
                self.assertIn(f"P-ADM-1 = nivel {nivel}", hallados[0].texto)

    def test_respeta_k(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporal:
            ruta = Path(temporal)
            (ruta / "parametros.yaml").write_text("parametros: []\n", encoding="utf-8")
            for numero in (1, 2, 3):
                (ruta / f"NOR-ADM-0{numero}.md").write_text(
                    f"## NOR-ADM-0{numero}\n\n§1. Regla de registro {numero}.", encoding="utf-8")
            buscador = construir_buscador(ruta)
            self.assertEqual(buscador.recuperar("registro", 0), [])
            self.assertEqual(len(buscador.recuperar("registro", 2)), 2)


if __name__ == "__main__":
    unittest.main()
