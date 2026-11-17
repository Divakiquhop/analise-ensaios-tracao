import numpy as np
import pandas as pd
import configuracao as cfg
from process.Aritmetica import Aritmetica

COLUNAS = ['inicio', 'fim', 'n', 'slope_mpa', 'E_gpa', 'intercept_mpa', 'r2', 'rmse', 'sse']


class AnaliseMecanica:
    def __init__(self, dados, parametros=cfg):
        self.aritmetica = Aritmetica(dados)
        self.cfg = parametros

    def executar(self, janela=1, comparar_janelas=False):
        from process.MetodoTracao import MetodoTracao
        return MetodoTracao(self.aritmetica.dados, self.cfg.PARAMETROS).executar(
            janela, self.cfg.JANELAS_MM if comparar_janelas else ())

    def gerar_regressoes(self, inicios, fins, janela=1):
        registros = []
        fins = tuple(fins)
        for inicio in inicios:
            for fim in fins:
                if fim <= inicio or fim - inicio < self.cfg.N_MIN:
                    continue
                try:
                    r = self.aritmetica.ajuste(inicio, fim, janela)
                except ValueError:
                    continue
                if r['n'] >= self.cfg.N_MIN:
                    registros.append({c: r[c] for c in COLUNAS})
        return self.estabilidade(pd.DataFrame(registros, columns=COLUNAS))

    def estabilidade(self, tabela):
        tabela = tabela.drop_duplicates(['inicio', 'fim']).copy()
        for eixo, grupo in [('fim', 'inicio'), ('inicio', 'fim')]:
            ordenada = tabela.sort_values([grupo, eixo])
            e = ordenada.groupby(grupo)['E_gpa']
            anterior = e.shift().abs().replace(0, np.nan)
            tabela[f'variacao_E_{eixo}'] = (ordenada['E_gpa'] - e.shift()).abs() / anterior
            janela = self.cfg.JANELA_ESTABILIDADE
            tabela[f'E_media_{eixo}'] = e.transform(lambda s: s.rolling(janela, min_periods=2).mean())
            tabela[f'E_std_{eixo}'] = e.transform(lambda s: s.rolling(janela, min_periods=2).std(ddof=0))
            tabela[f'E_cv_{eixo}'] = tabela[f'E_std_{eixo}'] / tabela[f'E_media_{eixo}'].abs().replace(0, np.nan)
        return tabela.reset_index(drop=True)

    def _qualidade(self, r):
        return (r['n'] >= self.cfg.N_MIN and r['slope_mpa'] > 0
                and r['r2'] >= self.cfg.R2_MIN and r['rmse'] <= self.cfg.RMSE_MAX_MPA)

    def limites_ensaio(self):
        dados = self.aritmetica.conjunto_de_dados
        indice_maximo = int(np.argmax(dados.iloc[:, 0].to_numpy()))

        def ponto(indice):
            return dict(indice=indice, tensao_mpa=float(dados.iloc[indice, 0]),
                        deformacao=float(dados.iloc[indice, 1]))

        return dict(maximo=ponto(indice_maximo), ultimo=ponto(len(dados) - 1),
                    ruptura_confirmada=False)

    def melhores_candidatas(self, tabela, janela=1, quantidade=None):
        if quantidade is None:
            quantidade = self.cfg.NUM_CANDIDATAS

        candidatas = self.selecionar_candidatas(tabela, janela)

        if candidatas.empty:
            return candidatas

        escolhidas = []
        distancia = self.cfg.DISTANCIA_MIN_CANDIDATAS

        for _, candidata in candidatas.iterrows():

            if not escolhidas:
                escolhidas.append(candidata)
                if len(escolhidas) >= quantidade:
                    break
                continue

            diferente = all(
                abs(int(candidata['inicio']) - int(escolhida['inicio'])) >= distancia
                or
                abs(int(candidata['fim']) - int(escolhida['fim'])) >= distancia
                for escolhida in escolhidas
            )

            if diferente:
                escolhidas.append(candidata)

            if len(escolhidas) >= quantidade:
                break

        return pd.DataFrame(escolhidas).reset_index(drop=True)

    def selecionar_candidatas(self, tabela, janela=1):
        candidatas = []
        p = self.cfg.PERTURBACAO
        if p < 1:
            raise ValueError('PERTURBACAO deve ser positiva.')
        for _, linha in tabela.iterrows():
            if not self._qualidade(linha):
                continue
            variacoes, aprovados = [], 0
            for di, df in [(-p, 0), (p, 0), (0, -p), (0, p), (-p, -p), (-p, p), (p, -p), (p, p)]:
                try:
                    viz = self.aritmetica.ajuste(int(linha.inicio) + di, int(linha.fim) + df, janela)
                except ValueError:
                    continue
                if viz['n'] < self.cfg.N_MIN:
                    continue
                variacao = abs(viz['E_gpa'] / linha.E_gpa - 1)
                variacoes.append(variacao)
                aprovados += int(self._qualidade(viz) and variacao <= self.cfg.VARIACAO_E_MAX)
            if len(variacoes) < self.cfg.VIZINHOS_MIN:
                continue
            robustez = aprovados / len(variacoes)
            if max(variacoes) <= self.cfg.VARIACAO_E_MAX and robustez >= self.cfg.FRACAO_ROBUSTA_MIN:
                registro = linha.to_dict()
                registro.update(robustez=robustez, variacao_E_max=max(variacoes), vizinhos=len(variacoes))
                candidatas.append(registro)
        colunas = list(tabela.columns) + ['robustez', 'variacao_E_max', 'vizinhos']
        resultado = pd.DataFrame(candidatas, columns=colunas)
        if not resultado.empty:
            resultado = resultado.sort_values(['robustez', 'n', 'variacao_E_max', 'rmse'], ascending=[False, False, True, True])
        return resultado.reset_index(drop=True)

