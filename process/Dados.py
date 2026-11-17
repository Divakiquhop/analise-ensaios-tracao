import pandas as pd
import numpy as np

class Dados:

    def __init__(self, nome_dos_dados = ''):
        self.local_dos_dados = pd.read_csv(nome_dos_dados)
        if self.local_dos_dados.shape[1] < 2:
            raise ValueError('O CSV deve conter tensão e deformação nas primeiras colunas.')
        self.local_dos_dados = self.local_dos_dados.iloc[:, :2].apply(pd.to_numeric, errors='raise')
        if len(self.local_dos_dados) < 3 or not np.isfinite(self.local_dos_dados.to_numpy()).all():
            raise ValueError('São necessárias pelo menos três linhas numéricas finitas.')

    def media_movel(self, janela):
        if not isinstance(janela, (int, np.integer)) or not 1 <= janela <= len(self.local_dos_dados):
            raise ValueError('Janela deve ser inteira entre 1 e o tamanho dos dados.')
        x_c , y_c = self.local_dos_dados.iloc[:, 1].rolling(janela).mean(), self.local_dos_dados.iloc[:, 0].rolling(janela).mean()
        return x_c, y_c
