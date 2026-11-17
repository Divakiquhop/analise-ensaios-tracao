"""Comparação visual de dois ensaios, utilizando o método existente."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, TextBox, CheckButtons
from process.Dados import Dados
from process.AnaliseMecanica import AnaliseMecanica
from process.Retas import desenhar_regressao


class Comparacao:
    def __init__(self, arquivo, segundo=None):
        self.dados = [None, None]
        self.resultados = [None, None]
        self.nomes = ['', '']
        self.janelas = [1, 1]
        self.tipos = ['Verdadeiras', 'Verdadeiras']
        self.detalhe = False
        self.faixa = False
        self.prolongar = False
        self.widgets = []
        self.janelas_auxiliares = []
        self.fig, self.axes = plt.subplots(1, 2, figsize=(15, 8))
        self.fig.subplots_adjust(left=.065, right=.975, top=.78, bottom=.33, wspace=.22)
        self.fig.canvas.manager.set_window_title('Comparação de ensaios de tração')
        self.fig.patch.set_facecolor('#f5f7fa')
        self.fig.text(.065, .955, 'Comparação de ensaios', fontsize=20, weight='bold', color='#203449')
        self.fig.text(.065, .917, 'Mesmas propriedades · análise independente por curva', fontsize=11, color='#526171')
        self.status = self.fig.text(.065, .008, '', fontsize=9, color='#526171')
        self.resumos = [self.fig.text(x, .245, '', va='top', fontsize=11, linespacing=1.6)
                        for x in (.065, .565)]
        for i, esquerda in enumerate((.065, .565)):
            self.botao('Abrir ensaio', [esquerda, .84, .105, .043], lambda e, i=i: self.escolher(i))
            campo = TextBox(self.fig.add_axes([esquerda+.18, .84, .055, .04]), 'Janela MM ', initial='1')
            campo.on_submit(lambda texto, i=i: self.definir_janela(i, texto))
            self.widgets.append(campo)
            radio = RadioButtons(self.fig.add_axes([esquerda+.275, .818, .125, .075]),
                                 ['Verdadeiras', 'Engenharia'])
            radio.on_clicked(lambda texto, i=i: self.definir_tipo(i, texto))
            self.widgets.append(radio)
            self.botao('Detalhes', [esquerda+.29, .11, .10, .04], lambda e, i=i: self.detalhes(i))
        self.botao('Curva / região inicial', [.065, .045, .19, .04], self.alternar)
        checks = CheckButtons(self.fig.add_axes([.30, .033, .235, .064]), ['Mostrar zona de afastamento'], [False])
        checks.on_clicked(self.alternar_faixa)
        self.widgets.append(checks)
        extensao = CheckButtons(self.fig.add_axes([.59, .033, .32, .064]),
                                ['Prolongar retas (pontilhado)'], [False])
        extensao.on_clicked(self.alternar_retas)
        self.widgets.append(extensao)
        self.carregar(0, arquivo)
        if segundo:
            self.carregar(1, segundo)

    def botao(self, texto, pos, callback):
        b = Button(self.fig.add_axes(pos), texto, color='#e5ecf3', hovercolor='#d2dfec')
        b.on_clicked(callback)
        self.widgets.append(b)

    def escolher(self, i):
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        try:
            caminho = filedialog.askopenfilename(title='Selecionar ensaio: tensão MPa e deformação em fração',
                                                filetypes=[('CSV', '*.csv')])
        finally:
            root.destroy()
        if caminho:
            self.carregar(i, caminho)

    def carregar(self, i, caminho):
        try:
            # Bases com colunas nomeadas são normalizadas somente em memória.
            quadro = pd.read_csv(caminho)
            if {'Sigma_true', 'e_true'}.issubset(quadro.columns):
                dados = Dados.__new__(Dados)
                dados.local_dos_dados = quadro[['Sigma_true', 'e_true']].apply(pd.to_numeric)
                if len(quadro) < 3 or not np.isfinite(dados.local_dos_dados.to_numpy()).all():
                    raise ValueError('Dados insuficientes ou não finitos.')
            else:
                dados = Dados(caminho)
            resultado = AnaliseMecanica(dados).executar(self.janelas[i])
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            self.status.set_text(f'Não foi possível abrir o ensaio: {exc}')
            self.fig.canvas.draw_idle()
            return
        self.dados[i], self.resultados[i] = dados, resultado
        self.nomes[i] = Path(caminho).stem
        self.atualizar()

    def definir_janela(self, i, texto):
        try:
            janela = int(texto)
            if self.dados[i] is None:
                raise ValueError('Abra um ensaio primeiro.')
            resultado = AnaliseMecanica(self.dados[i]).executar(janela)
        except ValueError as exc:
            self.status.set_text(f'Janela não aplicada: {exc}')
            self.fig.canvas.draw_idle()
            return
        self.janelas[i], self.resultados[i] = janela, resultado
        self.atualizar()

    def definir_tipo(self, i, texto):
        self.tipos[i] = texto
        self.atualizar()

    def alternar(self, evento=None):
        self.detalhe = not self.detalhe
        self.atualizar()

    def alternar_faixa(self, evento=None):
        self.faixa = not self.faixa
        self.atualizar()

    def alternar_retas(self, evento=None):
        self.prolongar = not self.prolongar
        self.atualizar()

    def atualizar(self):
        ativos = []
        for i, ax in enumerate(self.axes):
            ax.clear()
            ax.set_facecolor('white')
            ax.grid(alpha=.16)
            ax.spines[['top', 'right']].set_visible(False)
            ax.set_xlabel(f'Deformação — {self.tipos[i].lower()} [fração]')
            ax.set_ylabel('Tensão [MPa]')
            ax.set_title(self.nomes[i] or 'Selecione outro ensaio', fontsize=11, pad=12)
            r = self.resultados[i]
            if r is None:
                ax.text(.5, .5, 'Abra um CSV para comparar', transform=ax.transAxes, ha='center', color='#687787')
                continue
            ativos.append(ax)
            x, y = self.dados[i].media_movel(1)
            ax.plot(x, y, color='#97a4b1', lw=1, label='Original')
            xs, ys = self.dados[i].media_movel(self.janelas[i])
            if self.janelas[i] > 1:
                ax.plot(xs, ys, color='#247b9b', lw=1.4, label=f'MM {self.janelas[i]}')
            ref = r['referencia']
            if ref:
                xr = np.array([xs.iloc[ref['inicio']], xs.iloc[ref['fim']-1]])
                desenhar_regressao(ax, xr, ref['slope_mpa']*xr+ref['intercept_mpa'],
                                   prolongar=self.prolongar, color='#b85c38', lw=2.3, label='Regressão')
            off = r['escoamento']
            if off['status'] == 'estimado':
                ax.plot(off['deformacao'], off['tensao_mpa'], 'D', color='#247b9b', ms=5, label='Offset 0,2%')
            t = r['transicao']
            if self.faixa and t['status'] == 'estimado':
                ax.axvspan(*t['deformacao'], color='#dbba70', alpha=.25, label='Afastamento detectável')
            if self.detalhe:
                inicio = float(x.min())
                fim = off.get('deformacao', float(x.iloc[0])+.004)*1.15
                fim = max(inicio+.0012, fim)
                trecho = y[(x >= inicio) & (x <= fim)]
                ax.set_xlim(inicio, fim)
                if len(trecho):
                    margem = max(float(np.ptp(trecho))*.08, 1.)
                    ax.set_ylim(float(trecho.min())-margem, float(trecho.max())+margem)
            ax.legend(loc='best', fontsize=8, frameon=False)
            modulo = 'Inconclusivo' if ref is None else f'{ref["E_gpa"]:.2f} GPa'
            escoamento = 'Inconclusivo' if off['status'] != 'estimado' else f'{off["tensao_mpa"]:.2f} MPa'
            deformacao = '—' if off['status'] != 'estimado' else f'{off["deformacao"]:.6f}'
            fonte = 'Original' if self.janelas[i] == 1 else f'MM {self.janelas[i]}'
            self.resumos[i].set_text(f'E   {modulo}     |     Offset   {escoamento}\n'
                                    f'ε no offset   {deformacao}     |     σ máxima   {r["extremos"]["tensao_maxima_mpa"]:.2f} MPa\n'
                                    f'Fonte: {fonte} · Resultado {r["status"]}')
        comuns = len(ativos) == 2 and self.tipos[0] == self.tipos[1]
        if comuns:
            for getter, setter in [('get_xlim', 'set_xlim'), ('get_ylim', 'set_ylim')]:
                limites = [getattr(a, getter)() for a in ativos]
                for a in ativos:
                    getattr(a, setter)(min(v[0] for v in limites), max(v[1] for v in limites))
        self.status.set_text(('Escalas comuns.' if comuns else 'Escalas independentes.') +
                             ' Coordenadas declaradas pelo operador; não são convertidas. Janela 1 = original.')
        self.fig.canvas.draw_idle()

    def detalhes(self, i):
        if self.dados[i] is None:
            return
        from process.Graficos import Graficos
        painel = Graficos(self.dados[i], self.janelas[i], coordenadas=self.tipos[i].lower())
        # O explorador antigo foi originalmente rotulado para coordenadas verdadeiras.
        painel.fig.suptitle(f'{self.nomes[i]} · coordenadas {self.tipos[i].lower()}', x=.08, ha='left')
        painel.ax.set_xlabel(f'Deformação — {self.tipos[i].lower()} [fração]')
        painel.ax.set_ylabel('Tensão [MPa]')
        self.janelas_auxiliares.append(painel)
        painel.mostrar()

    def mostrar(self):
        plt.show()
