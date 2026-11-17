import numpy as np


class Aritmetica:
    def __init__(self, conjunto_de_dados):
        self.dados = conjunto_de_dados
        self.conjunto_de_dados = conjunto_de_dados.local_dos_dados

    def ajuste(self, inicio=0, fim=None, janela=1):


        fim = len(self.conjunto_de_dados) if fim is None else fim
        if not all(isinstance(v, (int, np.integer)) for v in (inicio, fim)):
            raise ValueError('Início e fim devem ser inteiros.')
        if not 0 <= inicio < fim <= len(self.conjunto_de_dados):
            raise ValueError('Intervalo fora dos dados ou vazio.')
        xs, ys = self.dados.media_movel(janela)
        x, y = xs.iloc[inicio:fim].to_numpy(), ys.iloc[inicio:fim].to_numpy()
        validos = np.isfinite(x) & np.isfinite(y)
        x, y = x[validos], y[validos]
        if len(x) < 2 or len(np.unique(x)) < 2:
            raise ValueError('Poucos pontos válidos ou deformação constante.')
        x_c, y_c = x - np.mean(x), y - np.mean(y)

        a = np.sum(x_c * y_c) / np.sum(x_c ** 2)
        b = np.mean(y) - a * np.mean(x)
        previsto = a * x + b


        residuos = y - previsto
        sse = float(np.sum(residuos ** 2))
        sst = float(np.sum(y_c ** 2))
        r2 = 1 - sse / sst if sst > 0 else float('nan')
        xl = np.linspace(x.min(), x.max(), 200)
        return dict(inicio=int(inicio), fim=int(fim), n=len(x),
                    slope_mpa=float(a),
                    E_gpa=float(a / 1000),
                    intercept_mpa=float(b),
                    r2=float(r2), rmse=float(np.sqrt(sse / len(x))), sse=sse,
                    x=x, y=y, x_linha=xl,
                    y_linha=a * xl + b)

    '''def regressao(self, inicio=0, fim=0):
        r = self.ajuste(inicio, fim)
        return r['x_linha'], r['y_linha'], r['r2'], r['slope_mpa'], r['intercept_mpa']'''
