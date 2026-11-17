import unittest

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import configuracao as cfg
from process.Aritmetica import Aritmetica
from process.AnaliseMecanica import AnaliseMecanica
from process.Dados import Dados
from process.Graficos import Graficos


def dados_sinteticos(x, y):
    """
    Cria um objeto Dados sem precisar gerar um arquivo CSV.

    A coluna 0 representa tensão.
    A coluna 1 representa deformação.
    """
    dados = Dados.__new__(Dados)

    dados.local_dos_dados = pd.DataFrame({
        'sigma': np.asarray(y, dtype=float),
        'epsilon': np.asarray(x, dtype=float)
    })

    return dados


class TestAritmetica(unittest.TestCase):

    def test_reta_perfeitamente_linear(self):
        """
        Para y = 2x + 3, a regressão deve recuperar exatamente
        coeficiente angular 2, intercepto 3 e R² = 1.
        """
        x = np.arange(5, dtype=float)
        y = 2 * x + 3

        aritmetica = Aritmetica(
            dados_sinteticos(x, y)
        )

        resultado = aritmetica.ajuste(
            inicio=0,
            fim=5
        )

        self.assertAlmostEqual(
            resultado['slope_mpa'],
            2.0
        )

        self.assertAlmostEqual(
            resultado['intercept_mpa'],
            3.0
        )

        self.assertAlmostEqual(
            resultado['r2'],
            1.0
        )

        self.assertAlmostEqual(
            resultado['rmse'],
            0.0
        )

        self.assertAlmostEqual(
            resultado['sse'],
            0.0
        )

        self.assertAlmostEqual(
            resultado['E_gpa'],
            0.002
        )

    def test_validacao_com_scipy_se_disponivel(self):
        """
        Compara nossa implementação com scipy.stats.linregress.
        """
        try:
            from scipy.stats import linregress
        except ImportError:
            self.skipTest(
                'SciPy não está instalado.'
            )

        x = np.linspace(0, 1, 100)
        y = 17 * x + np.sin(x * 20) * 0.1

        resultado = Aritmetica(
            dados_sinteticos(x, y)
        ).ajuste()

        referencia = linregress(x, y)

        self.assertAlmostEqual(
            resultado['slope_mpa'],
            referencia.slope
        )

        self.assertAlmostEqual(
            resultado['intercept_mpa'],
            referencia.intercept
        )

        self.assertAlmostEqual(
            resultado['r2'],
            referencia.rvalue ** 2
        )

    def test_intervalos_invalidos(self):
        x = np.arange(10, dtype=float)
        y = x ** 2

        aritmetica = Aritmetica(
            dados_sinteticos(x, y)
        )

        intervalos_invalidos = [
            (0, 0),
            (-1, 5),
            (5, 4),
            (0, 11),
            (0, 1)
        ]

        for inicio, fim in intervalos_invalidos:
            with self.assertRaises(ValueError):
                aritmetica.ajuste(
                    inicio,
                    fim
                )

    def test_deformacao_constante(self):
        x = np.ones(5)
        y = np.arange(5)

        aritmetica = Aritmetica(
            dados_sinteticos(x, y)
        )

        with self.assertRaises(ValueError):
            aritmetica.ajuste()

    def test_tensao_constante_produz_r2_nan(self):
        x = np.arange(5, dtype=float)
        y = np.ones(5)

        resultado = Aritmetica(
            dados_sinteticos(x, y)
        ).ajuste()

        self.assertTrue(
            np.isnan(resultado['r2'])
        )


class TestDados(unittest.TestCase):

    def test_media_movel_nao_altera_dados_originais(self):
        x = np.arange(10, dtype=float)
        y = 2 * x + 3

        dados = dados_sinteticos(x, y)

        original = dados.local_dos_dados.copy(
            deep=True
        )

        x_mm, y_mm = dados.media_movel(3)

        self.assertTrue(
            x_mm.iloc[:2].isna().all()
        )

        self.assertTrue(
            y_mm.iloc[:2].isna().all()
        )

        self.assertAlmostEqual(
            x_mm.iloc[2],
            1.0
        )

        pd.testing.assert_frame_equal(
            original,
            dados.local_dos_dados
        )

    def test_numero_de_pontos_validos_com_media_movel(self):
        x = np.arange(10, dtype=float)
        y = 2 * x + 3

        dados = dados_sinteticos(x, y)

        resultado = Aritmetica(dados).ajuste(
            0,
            10,
            janela=3
        )

        # MM3 gera dois NaN iniciais.
        self.assertEqual(
            resultado['n'],
            8
        )


class TestAnaliseMecanica(unittest.TestCase):

    def setUp(self):
        """
        Curva perfeitamente linear simulando E = 200 GPa.
        """
        self.x = np.linspace(
            0,
            0.003,
            550
        )

        self.y = (
            200000 * self.x + 3
        )

        self.dados = dados_sinteticos(
            self.x,
            self.y
        )

        self.analise = AnaliseMecanica(
            self.dados
        )

    def test_geracao_de_regressoes(self):
        tabela = self.analise.gerar_regressoes(
            inicios=[0, 10, 20],
            fins=[100, 150, 200]
        )

        self.assertFalse(
            tabela.empty
        )

        colunas_esperadas = {
            'inicio',
            'fim',
            'n',
            'slope_mpa',
            'E_gpa',
            'intercept_mpa',
            'r2',
            'rmse',
            'sse'
        }

        self.assertTrue(
            colunas_esperadas.issubset(
                tabela.columns
            )
        )

        self.assertTrue(
            (tabela['n'] >= cfg.N_MIN).all()
        )

    def test_modulo_em_curva_linear(self):
        tabela = self.analise.gerar_regressoes(
            inicios=[0, 10, 20],
            fins=[100, 150, 200]
        )

        for valor in tabela['E_gpa']:
            self.assertAlmostEqual(
                valor,
                200.0,
                places=8
            )

    def test_selecao_de_duas_candidatas(self):
        tabela = self.analise.gerar_regressoes(
            cfg.INICIOS,
            cfg.FINS
        )

        candidatas = (
            self.analise.melhores_candidatas(
                tabela,
                quantidade=2
            )
        )

        self.assertEqual(
            len(candidatas),
            2
        )

    def test_candidatas_nao_sao_praticamente_iguais(self):
        tabela = self.analise.gerar_regressoes(
            cfg.INICIOS,
            cfg.FINS
        )

        candidatas = (
            self.analise.melhores_candidatas(
                tabela,
                quantidade=2
            )
        )

        self.assertGreaterEqual(
            len(candidatas),
            2
        )

        c1 = candidatas.iloc[0]
        c2 = candidatas.iloc[1]

        diferenca_inicio = abs(
            int(c1.inicio) -
            int(c2.inicio)
        )

        diferenca_fim = abs(
            int(c1.fim) -
            int(c2.fim)
        )

        self.assertTrue(
            diferenca_inicio
            >= cfg.DISTANCIA_MIN_CANDIDATAS
            or
            diferenca_fim
            >= cfg.DISTANCIA_MIN_CANDIDATAS
        )

    def test_candidatas_passam_pelos_criterios_basicos(self):
        tabela = self.analise.gerar_regressoes(
            cfg.INICIOS,
            cfg.FINS
        )

        candidatas = (
            self.analise.melhores_candidatas(
                tabela,
                quantidade=2
            )
        )

        for _, candidata in candidatas.iterrows():

            self.assertGreaterEqual(
                candidata['n'],
                cfg.N_MIN
            )

            self.assertGreater(
                candidata['slope_mpa'],
                0
            )

            self.assertGreaterEqual(
                candidata['r2'],
                cfg.R2_MIN
            )

            self.assertLessEqual(
                candidata['rmse'],
                cfg.RMSE_MAX_MPA
            )

            self.assertGreaterEqual(
                candidata['robustez'],
                cfg.FRACAO_ROBUSTA_MIN
            )


class TestInterface(unittest.TestCase):

    def tearDown(self):
        plt.close('all')

    @staticmethod
    def criar_painel_linear():
        """
        Painel sintético com E = 200 GPa.
        """
        x = np.linspace(
            0,
            0.003,
            550
        )

        y = 200000 * x + 3

        return Graficos(
            dados_sinteticos(x, y)
        )

    def test_analise_automatica_ao_criar_painel(self):
        """
        Graficos.__init__ deve executar analisar()
        automaticamente.
        """
        painel = self.criar_painel_linear()

        self.assertIn(
            'variaveis',
            painel.resultados
        )

        self.assertFalse(
            painel.resultados[
                'variaveis'
            ].empty
        )

        self.assertGreaterEqual(
            len(
                painel.candidatas_selecionadas
            ),
            2
        )

    def test_labels_c1_e_c2_sao_atualizados(self):
        painel = self.criar_painel_linear()

        textos = [
            label.get_text()
            for label
            in painel.seletores_candidatas.labels
        ]

        self.assertTrue(
            textos[0].startswith('C1:')
        )

        self.assertTrue(
            textos[1].startswith('C2:')
        )

        self.assertNotIn(
            'aguardando',
            textos[0]
        )

        self.assertNotIn(
            'aguardando',
            textos[1]
        )

    def test_regressao_principal_e_candidata_avaliada(self):
        painel = self.criar_painel_linear()

        c1 = (
            painel.candidatas_selecionadas[0]
        )

        c2 = (
            painel.candidatas_selecionadas[1]
        )

        inicio_esperado = c1['inicio']
        fim_esperado = c1['fim']

        inicio_atual, fim_atual = map(
            int,
            painel.intervalo.val
        )

        self.assertEqual(
            inicio_atual,
            inicio_esperado
        )

        self.assertEqual(
            fim_atual,
            fim_esperado
        )

    def test_c1_aparece_quando_checkbox_e_marcado(self):
        painel = self.criar_painel_linear()

        # Inicialmente C1 está desmarcada.
        self.assertFalse(
            painel.seletores_candidatas
            .get_status()[0]
        )

        # Marca C1.
        painel.seletores_candidatas.set_active(0)

        labels = [
            linha.get_label()
            for linha in painel.ax.lines
        ]

        self.assertTrue(
            any(
                label.startswith('C1 ')
                for label in labels
            )
        )

    def test_c2_aparece_quando_checkbox_e_marcado(self):
        painel = self.criar_painel_linear()

        painel.seletores_candidatas.set_active(1)

        labels = [
            linha.get_label()
            for linha in painel.ax.lines
        ]

        self.assertTrue(
            any(
                label.startswith('C2 ')
                for label in labels
            )
        )

    def test_c1_e_c2_podem_aparecer_simultaneamente(self):
        painel = self.criar_painel_linear()

        painel.seletores_candidatas.set_active(0)
        painel.seletores_candidatas.set_active(1)

        labels = [
            linha.get_label()
            for linha in painel.ax.lines
        ]

        self.assertTrue(
            any(
                label.startswith('C1 ')
                for label in labels
            )
        )

        self.assertTrue(
            any(
                label.startswith('C2 ')
                for label in labels
            )
        )

    def test_desmarcar_c1_remove_sua_reta(self):
        painel = self.criar_painel_linear()

        painel.seletores_candidatas.set_active(0)

        self.assertTrue(
            any(
                linha.get_label().startswith('C1 ')
                for linha in painel.ax.lines
            )
        )

        painel.seletores_candidatas.set_active(0)

        self.assertFalse(
            any(
                linha.get_label().startswith('C1 ')
                for linha in painel.ax.lines
            )
        )

    def test_regressao_interativa_existe(self):
        painel = self.criar_painel_linear()

        labels = [
            linha.get_label()
            for linha in painel.ax.lines
        ]

        self.assertTrue(
            any(
                label.startswith('Atual ')
                for label in labels
            )
        )

        self.assertIsNotNone(
            painel.atual
        )

    def test_adicionar_e_limpar_regressao_manual(self):
        painel = self.criar_painel_linear()

        self.assertEqual(
            len(painel.salvas),
            0
        )

        painel.adicionar()

        self.assertEqual(
            len(painel.salvas),
            1
        )

        painel.limpar()

        self.assertEqual(
            len(painel.salvas),
            0
        )

    def test_media_movel_personalizada(self):
        painel = self.criar_painel_linear()

        painel.definir_personalizada('12')

        self.assertEqual(
            painel.mm_personalizada,
            12
        )

        self.assertIn(
            12,
            painel.medias_visiveis()
        )

    def test_fonte_de_analise_e_trocada_e_invalida_e_preservada(self):
        painel = self.criar_painel_linear()
        painel.definir_fonte('3')
        self.assertEqual(painel.janela, 3)
        self.assertEqual(painel.metodo['janela'], 3)
        self.assertEqual(painel.fonte, 'MM3')
        self.assertAlmostEqual(painel.atual['E_gpa'], 200)
        painel.definir_fonte('0')
        self.assertEqual(painel.janela, 3)

    def test_comparacao_abre_tabela(self):
        painel = self.criar_painel_linear()
        painel.comparar_medias()
        self.assertEqual(len(plt.get_fignums()), 2)
        ax = plt.figure(plt.get_fignums()[-1]).axes[0]
        self.assertEqual(len(ax.tables), 1)

    def test_media_movel_invalida_nao_substitui_valida(self):
        painel = self.criar_painel_linear()

        painel.definir_personalizada('12')

        for invalida in [
            '0',
            '1',
            '-3',
            '2.5',
            'texto',
            '100000'
        ]:
            painel.definir_personalizada(
                invalida
            )

            self.assertEqual(
                painel.mm_personalizada,
                12
            )

    def test_limites_do_ensaio(self):
        dados = dados_sinteticos(
            [0, 0.1, 0.2, 0.3],
            [0, 200, 150, 30]
        )

        analise = AnaliseMecanica(dados)

        limites = analise.limites_ensaio()

        self.assertEqual(
            limites['maximo'],
            {
                'indice': 1,
                'tensao_mpa': 200.0,
                'deformacao': 0.1
            }
        )

        self.assertEqual(
            limites['ultimo'],
            {
                'indice': 3,
                'tensao_mpa': 30.0,
                'deformacao': 0.3
            }
        )


class TestIntegracaoArquivoReal(unittest.TestCase):

    def tearDown(self):
        plt.close('all')

    @unittest.skipUnless(
        cfg.ARQUIVO_DADOS.exists(),
        'Arquivo real do ensaio não encontrado.'
    )
    def test_fluxo_com_dataset_real(self):
        """
        Teste de integração.

        Verifica se o CSV real passa por:
        Dados -> Graficos -> regressões -> candidatas.
        """
        dados = Dados(
            cfg.ARQUIVO_DADOS
        )

        painel = Graficos(dados)

        self.assertIn(
            'variaveis',
            painel.resultados
        )

        self.assertFalse(
            painel.resultados[
                'variaveis'
            ].empty
        )

        self.assertIsNotNone(
            painel.atual
        )

        self.assertGreater(
            len(
                painel.candidatas_selecionadas
            ),
            0
        )


if __name__ == '__main__':
    unittest.main()
