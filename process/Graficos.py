import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RangeSlider, TextBox
import configuracao as cfg
from process.AnaliseMecanica import AnaliseMecanica
from process.Retas import desenhar_regressao



class Graficos:
    def __init__(self, dados, janela=1, coordenadas="verdadeiras"):
        self.coordenadas = coordenadas
        #configs
        self.dados = dados
        self.analise = AnaliseMecanica(dados)
        dados.media_movel(janela)
        self.janela = janela
        self.metodo = None
        self.salvas = []
        self.resultados = {}
        self.candidatas = None
        self.candidatas_selecionadas = []
        self.atual = None
        self.mm_personalizada = None
        self.limites_ensaio = self.analise.limites_ensaio()
        self.fig, self.ax = plt.subplots(figsize=(14, 8))
        self.fig.canvas.manager.set_window_title('Explorador de ensaio de tração')
        self.fig.subplots_adjust(left=.08, right=.72, bottom=.32, top=.93)
        self.fig.suptitle(f'Curva tensão × deformação — {self.coordenadas}', x=.08, y=.975, ha='left', fontsize=12)
        self.info = self.fig.text(.76, .55, '', va='top', fontsize=10)
        self.status = self.fig.text(.08, .025, 'Intervalos [início, fim): fim exclusivo. Limites exploratórios em configuracao.py.', fontsize=9)
        total = len(dados.local_dos_dados)
        self.medias_referencia = [j for j in cfg.JANELAS_MM if 1 < j <= total]
        self.fig.text(.76, .92, 'Médias móveis — mostrar / ocultar', fontsize=10)
        self.seletores_mm = CheckButtons(self.fig.add_axes([.76, .71, .22, .19]),
            [f'MM{j} — {j} pontos' for j in self.medias_referencia] + ['Personalizada'],
            [True] * len(self.medias_referencia) + [False])
        self.seletores_mm.on_clicked(self.atualizar)
        self.caixa_mm = TextBox(self.fig.add_axes([.83, .655, .14, .035]), 'Janela: ', initial='')
        self.caixa_mm.on_submit(self.definir_personalizada)
        self.fig.text(.76, .60, 'Seletores: apenas visualização.\nFonte do ajuste: controle abaixo do gráfico.', fontsize=9)
        self.caixa_fonte = TextBox(self.fig.add_axes([.25, .08, .08, .035]), 'Janela do ajuste: ', initial=str(janela))
        self.caixa_fonte.on_submit(self.definir_fonte)
        inicio, fim = cfg.INTERVALO_INICIAL
        fim = min(total, max(3, fim))
        inicio = min(inicio, fim - 3)
        self.intervalo = RangeSlider(self.fig.add_axes([.16, .235, .52, .035]), 'Início / fim', 0, total,
                                    valinit=(inicio, fim), valstep=1, valfmt='%0.0f')
        self.intervalo.on_changed(self.atualizar)
        self.checks = CheckButtons(self.fig.add_axes([.76, .04, .22, .13]),
                                  ['Original', 'Regressões', 'Região'],
                                  [True, True, True])
        self.checks.on_clicked(self.atualizar)
        self.extensao = CheckButtons(self.fig.add_axes([.55, .945, .18, .035]),
                                    ['Prolongar retas'], [False])
        self.extensao.on_clicked(self.atualizar)
        maximo, ultimo = self.limites_ensaio['maximo'], self.limites_ensaio['ultimo']
        resumo = (f'Tensão máxima registrada (original)\n'
                  f'σ = {maximo["tensao_mpa"]:.5g} MPa\n'
                  f'ε = {maximo["deformacao"]:.5g} | ponto {maximo["indice"]}\n\n'
                  f'Último registro: {ultimo["indice"]} — ruptura não confirmada\n'
                  f'σ = {ultimo["tensao_mpa"]:.5g} MPa | ε = {ultimo["deformacao"]:.5g}')
        self.info_ensaio = self.fig.text(.76, .41, resumo, va='top', fontsize=9)

        self.fig.text(
            .76, .275,
            'Regressões candidatas — mostrar / ocultar',
            fontsize=10
        )

        self.seletores_candidatas = CheckButtons(
            self.fig.add_axes([.76, .18, .22, .085]),
            [
                'C1 — aguardando análise',
                'C2 — aguardando análise'
            ],
            [False, False]
        )

        self.seletores_candidatas.on_clicked(self.atualizar)

        self.botoes = []
        for texto, posicao, callback in [
            ('Intervalo / curva', [.39, .945, .15, .035], self.ampliar),
            ('Adicionar regressão', [.08, .15, .19, .05], self.adicionar),
            ('Limpar regressões', [.29, .15, .19, .05], self.limpar),
            ('Analisar regressões', [.50, .15, .20, .05], self.analisar),
            ('Comparar médias', [.40, .075, .20, .045], self.comparar_medias)
        ]:
            botao = Button(self.fig.add_axes(posicao), texto)
            botao.on_clicked(callback)
            self.botoes.append(botao)
        self.atualizar()
        self.analisar()
        self.vista_completa = (self.ax.get_xlim(), self.ax.get_ylim())
        if self.fig.canvas.toolbar is not None:
            self.fig.canvas.toolbar.push_current()

    def mensagem(self, texto):
        self.status.set_text(texto)
        self.fig.canvas.draw_idle()

    def definir_fonte(self, texto):
        try:
            janela = int(texto)
            self.dados.media_movel(janela)
        except ValueError as exc:
            self.mensagem(f'Fonte inválida: {exc}')
            return
        self.janela = janela
        self.analisar()

    def comparar_medias(self, evento=None):
        r = self.analise.executar(comparar_janelas=True)
        linhas = r['medias_moveis']
        if not linhas:
            self.mensagem('Comparação indisponível: sem referência estável ou suporte comum suficiente.')
            return
        fig, ax = plt.subplots(figsize=(13, 4))
        ax.axis('off')
        def estado(v):
            return '—' if v is None else ('Sim' if v else 'Não')
        valores = [[v['janela'], f'{v["E_mesmo_intervalo_gpa"]:.2f}',
                    '—' if v['E_selecao_gpa'] is None else f'{v["E_selecao_gpa"]:.2f}',
                    f'{100*v["variacao_E"]:.2f}%', estado(v['compativel_E']),
                    estado(v['compativel_escoamento']), estado(v['compativel_transicao']),
                    estado(v['compativel_maximo']), estado(v['compativel_deformacao']),
                    '—' if v['reducao_oscilacao'] is None else f'{100*v["reducao_oscilacao"]:.1f}%'] for v in linhas]
        tabela = ax.table(cellText=valores, colLabels=['Janela', 'E comum\nGPa', 'E seleção\nGPa',
            'ΔE comum', 'E compatível', 'Offset comp.', 'Faixa comp.', 'Máximo comp.',
            'Deform. comp.', 'Red. oscilação'], loc='center')
        tabela.auto_set_font_size(False)
        tabela.set_fontsize(9)
        tabela.scale(1, 2)
        ax.set_title('Sensibilidade das médias móveis em relação aos dados originais')
        fig.text(.05, .06, 'Compatibilidade nos thresholds exploratórios; não comprova exatidão.\n'
                 '— = evidência insuficiente. Janelas retrospectivas; extremos podem ser atenuados.', fontsize=9)
        if fig.canvas.manager is not None and 'agg' != plt.get_backend().lower():
            fig.show()

    def definir_personalizada(self, texto):
        try:
            janela = int(texto)
            if janela < 2:
                raise ValueError('A média móvel deve ter pelo menos 2 pontos.')
            self.dados.media_movel(janela)
        except ValueError as exc:
            self.mensagem(f'Janela inválida: {exc}')
            return
        self.mm_personalizada = janela
        self.seletores_mm.labels[-1].set_text(f'Personalizada — {janela} pontos')
        if not self.seletores_mm.get_status()[-1]:
            self.seletores_mm.set_active(len(self.medias_referencia))
        self.atualizar()
        self.mensagem(f'MM{janela} adicionada. Os seletores controlam apenas a visibilidade das médias.')

    def medias_visiveis(self):
        estados = self.seletores_mm.get_status()
        janelas = [j for j, visivel in zip(self.medias_referencia, estados) if visivel]
        if estados[-1] and self.mm_personalizada is not None:
            janelas.append(self.mm_personalizada)
        return sorted(set(janelas))

    @property
    def fonte(self):
        return 'Original' if self.janela == 1 else f'MM{self.janela}'

    def atualizar(self, evento=None):
        limites = (
            (self.ax.get_xlim(), self.ax.get_ylim())
            if self.ax.has_data()
            else None
        )

        self.ax.clear()

        original, retas, regiao = self.checks.get_status()

        x, y = self.dados.media_movel(1)

        if original:
            self.ax.plot(
                x,
                y,
                linestyle='None',
                marker='.',
                markersize=3,
                color='.45',
                label='Original'
            )

        for janela in self.medias_visiveis():
            xm, ym = self.dados.media_movel(janela)

            cor = (
                plt.get_cmap('tab10')(
                    self.medias_referencia.index(janela) % 10
                )
                if janela in self.medias_referencia
                else 'tab:purple'
            )

            self.ax.plot(
                xm,
                ym,
                color=cor,
                lw=1.2,
                label=f'MM{janela} — janela de {janela} pontos'
            )

        inicio, fim = map(int, self.intervalo.val)
        self.atual = None

        try:
            r = self.analise.aritmetica.ajuste(
                inicio,
                fim,
                self.janela
            )

            self.atual = r

            if retas:
                desenhar_regressao(self.ax,
                    r['x_linha'],
                    r['y_linha'],
                    prolongar=self.extensao.get_status()[0],
                    color='tab:red',
                    lw=2,
                    label=(
                        f'Atual {self.fonte} '
                        f'[{inicio}, {fim})'
                    )
                )

            if regiao:
                self.ax.axvspan(
                    r['x'].min(),
                    r['x'].max(),
                    color='tab:orange',
                    alpha=.15,
                    label='Intervalo selecionado'
                )

                self.ax.axvline(
                    r['x'][0],
                    color='tab:orange',
                    ls=':',
                    label='Início / último ponto'
                )

                self.ax.axvline(
                    r['x'][-1],
                    color='tab:orange',
                    ls=':'
                )

            self.info.set_text(
                f'Fonte: {self.fonte}\n'
                f'Início: {inicio}   Fim: {fim}\n'
                f'N válido: {r["n"]}\n'
                f'E = {r["E_gpa"]:.5g} GPa\n'
                f'R² = {r["r2"]:.7f}\n'
                f'b = {r["intercept_mpa"]:.5g} MPa\n'
                f'RMSE = {r["rmse"]:.5g} MPa'
            )

        except ValueError as exc:
            self.info.set_text(
                f'{self.fonte}\n{exc}'
            )

        if retas:
            for i, (fonte, regressao_salva) in enumerate(
                    self.salvas,
                    start=1
            ):
                desenhar_regressao(self.ax,
                    regressao_salva['x_linha'],
                    regressao_salva['y_linha'],
                    prolongar=self.extensao.get_status()[0], linestyle='-',
                    label=(
                        f'R{i} {fonte} '
                        f'[{regressao_salva["inicio"]}, '
                        f'{regressao_salva["fim"]}) '
                        f'E={regressao_salva["E_gpa"]:.3g} GPa'
                    )
                )

        estados_candidatas = (
            self.seletores_candidatas.get_status()
        )

        for i, candidata in enumerate(
                self.candidatas_selecionadas
        ):

            if i >= len(estados_candidatas):
                break

            if estados_candidatas[i]:
                desenhar_regressao(self.ax,
                    candidata['x_linha'],
                    candidata['y_linha'],
                    prolongar=self.extensao.get_status()[0], linestyle='-',
                    linewidth=2.2,
                    label=(
                        f'C{i + 1} '
                        f'[{candidata["inicio"]}, '
                        f'{candidata["fim"]}) '
                        f'E={candidata["E_gpa"]:.2f} GPa'
                    )
                )

        if original:
            maximo = self.limites_ensaio['maximo']
            ultimo = self.limites_ensaio['ultimo']

            self.ax.plot(
                maximo['deformacao'],
                maximo['tensao_mpa'],
                linestyle='None',
                marker='o',
                markersize=10,
                markerfacecolor='none',
                color='tab:blue',
                label='Tensão máxima registrada',
                zorder=5
            )

            self.ax.plot(
                ultimo['deformacao'],
                ultimo['tensao_mpa'],
                linestyle='None',
                marker='x',
                markersize=7,
                color='purple',
                label='Último ponto (ruptura não confirmada)',
                zorder=6
            )

        if self.metodo is not None and regiao:
            t = self.metodo['transicao']
            if t['status'] == 'estimado':
                self.ax.axvspan(*t['deformacao'], color='tab:green', alpha=.2,
                                label=f'Afastamento detectável {self.fonte} — sem probabilidade')
            e = self.metodo['escoamento']
            if e['status'] == 'estimado':
                self.ax.plot(e['deformacao'], e['tensao_mpa'], 'D', color='tab:green',
                             label=f'Offset 0,2% {self.fonte} (coordenadas de entrada)')
        self.ax.set(
            xlabel=f'Deformação — {self.coordenadas} ε [−]',
            ylabel='Tensão σ [MPa]'
        )

        self.ax.grid(alpha=.2)

        if self.ax.get_legend_handles_labels()[0]:
            self.ax.legend(
                fontsize=8,
                loc='best'
            )

        if limites:
            self.ax.set_xlim(limites[0])
            self.ax.set_ylim(limites[1])

        self.fig.canvas.draw_idle()

    def adicionar(self, evento=None):
        if self.atual is not None:
            self.salvas.append((self.fonte, self.atual.copy()))
            self.atualizar()

    def ampliar(self, evento=None):
        if self.atual is not None:
            toolbar = self.fig.canvas.toolbar
            if toolbar is not None:
                toolbar.push_current()
            completa = (np.allclose(self.ax.get_xlim(), self.vista_completa[0]) and
                        np.allclose(self.ax.get_ylim(), self.vista_completa[1]))
            if completa:
                r = self.atual
                for valores, definir in [(r['x'], self.ax.set_xlim), (r['y'], self.ax.set_ylim)]:
                    margem = max(float(np.ptp(valores)) * .1, 1e-8)
                    definir(float(min(valores)) - margem, float(max(valores)) + margem)
            else:
                self.ax.set_xlim(self.vista_completa[0])
                self.ax.set_ylim(self.vista_completa[1])
            if toolbar is not None:
                toolbar.push_current()
            self.fig.canvas.draw_idle()

    def limpar(self, evento=None):
        self.salvas.clear()
        self.atualizar()

    def analisar(self, evento=None):
        self.mensagem('Calculando regressões...')
        self.fig.canvas.flush_events()
        a = self.analise
        self.metodo = a.executar(self.janela)
        self.resultados = {'variaveis': pd.DataFrame(self.metodo['candidatas']), 'metodo': self.metodo}

        self.selecionar()

    def selecionar(self, evento=None):

        if not self.resultados:
            self.analisar()

        tabela = self.resultados['variaveis']
        # Referência sempre é a primeira candidata realmente avaliada.
        escolhidas = []
        for _, c in tabela.iterrows():
            if not escolhidas or all(abs(c.inicio-v.inicio) >= cfg.DISTANCIA_MIN_CANDIDATAS
                                     or abs(c.fim-v.fim) >= cfg.DISTANCIA_MIN_CANDIDATAS for v in escolhidas):
                escolhidas.append(c)
            if len(escolhidas) >= cfg.NUM_CANDIDATAS:
                break
        self.candidatas = pd.DataFrame(escolhidas)

        if self.candidatas.empty:
            for i, label in enumerate(self.seletores_candidatas.labels, start=1):
                label.set_text(f'C{i} — não encontrada')
            self.candidatas_selecionadas = []
            self.atualizar()

            self.mensagem(
                'Análise automática inconclusiva. Ajuste manual permanece exploratório; '
                'revise dados e perfil de parâmetros.'
            )

            return

        self.candidatas_selecionadas = []

        for _, c in self.candidatas.iterrows():
            regressao = self.analise.aritmetica.ajuste(
                int(c.inicio),
                int(c.fim),
                self.janela
            )

            regressao['variacao_E_max'] = c.variacao_E_max

            self.candidatas_selecionadas.append(regressao)

        c1 = self.candidatas_selecionadas[0]
        self.intervalo.set_val((c1['inicio'], c1['fim']))

        texto = ' | '.join(
            f'C{i}: [{r["inicio"]}, {r["fim"]}) '
            f'E={r["E_gpa"]:.2f} GPa '
            f'R²={r["r2"]:.5f}'
            for i, r in enumerate(
                self.candidatas_selecionadas,
                start=1
            )
        )

        for i, label in enumerate(self.seletores_candidatas.labels):

            if i < len(self.candidatas_selecionadas):
                r = self.candidatas_selecionadas[i]

                label.set_text(
                    f'C{i + 1}: [{r["inicio"]}, {r["fim"]})  '
                    f'E={r["E_gpa"]:.2f} GPa'
                )

            else:
                label.set_text(f'C{i + 1} — não encontrada')

        t = self.metodo['transicao']
        texto += (f' | Faixa σ: {t["tensao_mpa"][0]:.1f}–{t["tensao_mpa"][1]:.1f} MPa'
                  if t['status'] == 'estimado' else ' | Faixa: inconclusiva')
        self.mensagem(texto)

    def mostrar(self):
        plt.show()
