"""Desenho de regressões; prolongamento não participa do cálculo do ajuste."""


def desenhar_regressao(ax, x, y, prolongar=False, **estilo):
    segmento, = ax.plot(x, y, **estilo)
    if prolongar:
        # AxLine é recortada pela área visível e acompanha zoom/pan sem extremos artificiais.
        limites = ax.get_xlim(), ax.get_ylim()
        reta = ax.axline((x[0], y[0]), (x[-1], y[-1]),
                        color=segmento.get_color(), linestyle=':', linewidth=1.4,
                        alpha=.75, zorder=segmento.get_zorder()-.1, label='_nolegend_')
        ax.set_xlim(limites[0])
        ax.set_ylim(limites[1])
        return segmento, reta
    return segmento, None
