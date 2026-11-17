import unittest
import numpy as np
import pandas as pd
from process.Dados import Dados
from process.AnaliseMecanica import AnaliseMecanica


def curva(E=200000., transicao=.0018, ruido=0., discretizar=False, acomodacao=False):
    x = np.linspace(0, .008, 801)
    y = E * np.minimum(x, transicao) + 2000 * np.maximum(x - transicao, 0)
    if acomodacao:
        y += 12 * np.exp(-x / .00006)
    y += np.random.default_rng(42).normal(0, ruido, len(x))
    if discretizar:
        x = np.round(x, 4)
    d = Dados.__new__(Dados)
    d.local_dos_dados = pd.DataFrame({'sigma': y, 'epsilon': x})
    return d


class TestMetodo(unittest.TestCase):
    def test_reta_ruidosa_nao_inventa_transicao(self):
        r = AnaliseMecanica(curva(transicao=1, ruido=.8)).executar()
        self.assertEqual(r['status'], 'parcial')
        self.assertLess(abs(r['referencia']['E_gpa'] / 200 - 1), .05)
        self.assertEqual(r['transicao']['status'], 'inconclusivo')
        self.assertEqual(r['escoamento']['status'], 'inconclusivo')

    def test_acos_proximos_mesmos_parametros(self):
        for E, transicao in [(185000, .0015), (200000, .0018), (215000, .0021)]:
            with self.subTest(E=E):
                r = AnaliseMecanica(curva(E, transicao, ruido=.8)).executar()
                self.assertLess(abs(r['referencia']['E_gpa'] * 1000 / E - 1), .05)
                self.assertEqual(r['transicao']['status'], 'estimado')
                faixa = r['transicao']['deformacao']
                self.assertLessEqual(faixa[0], transicao + .0001)
                self.assertGreaterEqual(faixa[1], transicao)
                self.assertLess(faixa[1] - faixa[0], .0006)
                # Intersecao analitica com reta deslocada em 0.002.
                esperado = E * transicao + 2000 * E * .002 / (E - 2000)
                self.assertAlmostEqual(r['escoamento']['tensao_mpa'], esperado, delta=3)

    def test_discretizacao_e_acomodacao(self):
        for kwargs in [dict(discretizar=True), dict(acomodacao=True)]:
            r = AnaliseMecanica(curva(ruido=.8, **kwargs)).executar()
            self.assertIsNotNone(r['referencia'])
            self.assertLess(abs(r['referencia']['E_gpa'] / 200 - 1), .05)

    def test_constante_retorna_inconclusivo(self):
        d = curva()
        d.local_dos_dados.iloc[:, 1] = 0
        r = AnaliseMecanica(d).executar()
        self.assertEqual(r['status'], 'inconclusivo')
        self.assertIsNone(r['referencia'])

    def test_janelas_comparadas_no_mesmo_suporte(self):
        a = AnaliseMecanica(curva(ruido=.8))
        original = a.aritmetica.conjunto_de_dados.copy(deep=True)
        r = a.executar(comparar_janelas=True)
        mm = r['medias_moveis']
        self.assertEqual([v['janela'] for v in mm], [1, 3, 5, 7])
        self.assertEqual(len({v['n_comum'] for v in mm}), 1)
        self.assertGreater(mm[1]['reducao_oscilacao'], 0)
        self.assertIn('compativel_deformacao', mm[1])
        pd.testing.assert_frame_equal(original, a.aritmetica.conjunto_de_dados)
        self.assertEqual(r, a.executar(comparar_janelas=True))

    def test_quantidade_um_e_respeitada(self):
        a = AnaliseMecanica(curva())
        tabela = a.gerar_regressoes([0, 10], [80, 100])
        self.assertEqual(len(a.melhores_candidatas(tabela, quantidade=1)), 1)

    def test_parametros_invalidos(self):
        import configuracao as cfg
        from process.MetodoTracao import MetodoTracao
        for chave, valor in [('persistencia_blocos', 0), ('r2_min', 2),
                             ('bloco_n_min', 0), ('variacao_e_max', float('nan'))]:
            with self.subTest(chave=chave), self.assertRaises(ValueError):
                MetodoTracao(curva(), dict(cfg.PARAMETROS, **{chave: valor}))

    def test_deslocamento_de_origem_nao_muda_modulo_ou_offset(self):
        d = curva(ruido=.8)
        r1 = AnaliseMecanica(d).executar()
        d.local_dos_dados.iloc[:, 1] += .01
        r2 = AnaliseMecanica(d).executar()
        self.assertAlmostEqual(r1['referencia']['E_gpa'], r2['referencia']['E_gpa'])
        self.assertAlmostEqual(r1['escoamento']['tensao_mpa'], r2['escoamento']['tensao_mpa'])

    def test_json_sem_interface(self):
        import subprocess, sys, json
        p = subprocess.run([sys.executable, '-B', 'main.py', '--json'],
                           capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertIn('parametros', r)
        self.assertEqual(r['janela'], 1)

    def test_comparacao_exige_referencia_original(self):
        with self.assertRaises(ValueError):
            AnaliseMecanica(curva()).executar(janela=3, comparar_janelas=True)

    def test_ampliacao_e_sensibilidade_registradas(self):
        r = AnaliseMecanica(curva()).executar()
        self.assertGreater(len(r['ampliacoes']), 2)
        self.assertGreater(r['ampliacoes'][-1]['variacao_E'], .05)
        self.assertEqual(len(r['transicoes_candidatas']), len(r['candidatas']))

    def test_linear_multiplas_sementes(self):
        for seed in range(5):
            d = curva(transicao=1)
            d.local_dos_dados.iloc[:, 0] += np.random.default_rng(seed).normal(0, 3, 801)
            r = AnaliseMecanica(d).executar()
            self.assertIsNotNone(r['referencia'])
            self.assertEqual(r['transicao']['status'], 'inconclusivo')

    def test_dados_curtos_inconclusivos(self):
        d = curva()
        d.local_dos_dados = d.local_dos_dados.iloc[:20]
        self.assertEqual(AnaliseMecanica(d).executar()['status'], 'inconclusivo')

    def test_referencia_e_centro_que_sustenta_familia(self):
        from process.MetodoTracao import MetodoTracao
        import configuracao as cfg
        m = MetodoTracao(curva(), cfg.PARAMETROS)
        candidatas = [dict(E_gpa=e, inicio=0, fim=100, n=100) for e in (194.2, 200, 205.8)]
        familia = m.familia(candidatas)
        self.assertEqual(familia[0]['E_gpa'], 200)
        for c in familia:
            self.assertLessEqual(abs(c['E_gpa']/familia[0]['E_gpa']-1), .03)

    def test_pico_isolado_nao_vira_transicao(self):
        d = curva(transicao=1, ruido=.8)
        d.local_dos_dados.iloc[400, 0] += 100
        r = AnaliseMecanica(d).executar()
        self.assertEqual(r['transicao']['status'], 'inconclusivo')

    def test_menos_pontos_mesmo_material(self):
        d = curva(ruido=.8)
        d.local_dos_dados = d.local_dos_dados.iloc[::2].reset_index(drop=True)
        r = AnaliseMecanica(d).executar()
        self.assertIsNotNone(r['referencia'])
        self.assertLess(abs(r['referencia']['E_gpa'] / 200 - 1), .05)
        self.assertEqual(r['transicao']['status'], 'estimado')

    def test_a500_referencia_externa(self):
        import configuracao as cfg
        r = AnaliseMecanica(Dados(cfg.ARQUIVO_DADOS)).executar()
        self.assertLess(abs(r['referencia']['E_gpa']/186.62677695922228-1), .05)
        self.assertLess(abs(r['escoamento']['tensao_mpa']/371.8-1), .02)
        self.assertEqual(r['transicao']['status'], 'estimado')
        self.assertLessEqual(np.ptp(r['transicao']['deformacao']), cfg.PARAMETROS['faixa_largura_max'])


if __name__ == '__main__':
    unittest.main()
