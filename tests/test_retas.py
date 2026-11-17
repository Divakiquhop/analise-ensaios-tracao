import unittest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from process.Retas import desenhar_regressao


class TestRetas(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_prolongamento_preserva_segmento_e_enquadramento(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 3])
        limites = (ax.get_xlim(), ax.get_ylim())
        desenhar_regressao(ax, [0.1, 0.2], [0.2, 0.4], prolongar=True, color='red')
        self.assertEqual(len(ax.lines), 3)
        np.testing.assert_allclose(ax.get_xlim(), limites[0])
        np.testing.assert_allclose(ax.get_ylim(), limites[1])
        np.testing.assert_allclose(ax.lines[-2].get_xdata(), [0.1, 0.2])
        self.assertEqual(type(ax.lines[-1]).__name__, 'AxLine')

    def test_segmento_sem_prolongamento(self):
        fig, ax = plt.subplots()
        desenhar_regressao(ax, [0, 1], [1, 3], prolongar=False)
        self.assertEqual(len(ax.lines), 1)
