import unittest
import tempfile
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import configuracao as cfg
from process.Comparacao import Comparacao


class TestComparacao(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_paineis_independentes_e_escalas_compativeis(self):
        p = Comparacao(cfg.ARQUIVO_DADOS)
        p.carregar(1, cfg.ARQUIVO_DADOS)
        self.assertAlmostEqual(p.resultados[0]['referencia']['E_gpa'], 186.2974, places=3)
        self.assertEqual(p.axes[0].get_xlim(), p.axes[1].get_xlim())
        p.definir_janela(1, '3')
        self.assertEqual(p.janelas, [1, 3])
        self.assertIn('Offset', p.resumos[0].get_text())
        anterior = p.resultados[1]
        p.definir_janela(1, '0')
        self.assertIs(p.resultados[1], anterior)

    def test_coordenadas_e_falha_preservam_ensaio(self):
        p = Comparacao(cfg.ARQUIVO_DADOS)
        p.carregar(1, cfg.ARQUIVO_DADOS)
        p.definir_tipo(1, 'Engenharia')
        self.assertIn('independentes', p.status.get_text())
        anterior = p.resultados[1]
        p.carregar(1, 'arquivo_inexistente.csv')
        self.assertIs(p.resultados[1], anterior)

    def test_curva_curta_nao_exibe_propriedades_inventadas(self):
        p = Comparacao(cfg.ARQUIVO_DADOS)
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'curta.csv'
            arquivo.write_text('sigma,epsilon\n0,0\n100,0.0005\n200,0.001\n', encoding='utf-8')
            p.carregar(1, arquivo)
        self.assertIsNone(p.resultados[1]['referencia'])
        self.assertIn('Inconclusivo', p.resumos[1].get_text())
        p.alternar()
        p.alternar_faixa()
        self.assertFalse(any(l.get_label() == 'Regressão' for l in p.axes[1].lines))


if __name__ == '__main__':
    unittest.main()
