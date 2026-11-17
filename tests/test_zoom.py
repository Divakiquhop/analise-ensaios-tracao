import unittest
import matplotlib
matplotlib.use('Agg')
from matplotlib.backend_bases import NavigationToolbar2
import matplotlib.pyplot as plt
import numpy as np
import configuracao as cfg
from process.Dados import Dados
from process.Graficos import Graficos


class TestZoom(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_segundo_clique_restaura_curva(self):
        p = Graficos(Dados(cfg.ARQUIVO_DADOS))
        original = (p.ax.get_xlim(), p.ax.get_ylim())
        p.ampliar()
        self.assertLess(np.ptp(p.ax.get_xlim()), np.ptp(original[0]))
        p.ampliar()
        np.testing.assert_allclose(p.ax.get_xlim(), original[0])
        np.testing.assert_allclose(p.ax.get_ylim(), original[1])

    def test_home_restaura_apos_ampliacao_e_atualizacao(self):
        p = Graficos(Dados(cfg.ARQUIVO_DADOS))
        toolbar = NavigationToolbar2(p.fig.canvas)
        original = (p.ax.get_xlim(), p.ax.get_ylim())
        p.ampliar()
        p.atualizar()
        toolbar.home()
        np.testing.assert_allclose(p.ax.get_xlim(), original[0])
        np.testing.assert_allclose(p.ax.get_ylim(), original[1])
