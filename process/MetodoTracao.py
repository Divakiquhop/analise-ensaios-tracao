"""Método exploratório reproduzível. Não atribui probabilidade à transição."""
import hashlib
import numpy as np


class MetodoTracao:
    def __init__(self, dados, parametros):
        self.dados = dados
        self.p = dict(parametros)
        self.validar_parametros()
        self.y, self.x = dados.local_dos_dados.iloc[:, :2].to_numpy(dtype=float).T

    def validar_parametros(self):
        inteiros = ('n_min', 'deformacoes_distintas_min', 'inicios_grade', 'fins_grade',
                    'familia_min', 'bloco_n_min', 'bloco_n_max', 'persistencia_blocos')
        fracoes = ('r2_min', 'rmse_relativo_max', 'curvatura_relativa_max', 'variacao_e_max',
                   'perturbacao_fracao', 'sobreposicao_min', 'fracao_sinal_min',
                   'residuo_fracao_amplitude', 'mm_variacao_e_max',
                   'mm_variacao_escoamento_max', 'mm_variacao_maximo_max',
                   'mm_variacao_deformacao_max')
        for chave, valor in self.p.items():
            if not isinstance(valor, (int, float)) or not np.isfinite(valor) or valor <= 0:
                raise ValueError(f'Parâmetro {chave} deve ser positivo e finito.')
            if chave in inteiros and (isinstance(valor, bool) or not isinstance(valor, int)):
                raise ValueError(f'Parâmetro {chave} deve ser inteiro.')
            if chave in fracoes and valor > 1:
                raise ValueError(f'Parâmetro {chave} deve estar em (0, 1].')
        if (self.p['bloco_n_max'] < self.p['bloco_n_min'] or
                self.p['deformacao_inicio_max'] >= self.p['deformacao_busca_max']):
            raise ValueError('Limites de blocos ou de busca incompatíveis.')

    def serie(self, janela):
        # Preserva a média retrospectiva existente e os índices de aquisição.
        x, y = self.dados.media_movel(janela)
        return x.to_numpy(), y.to_numpy()

    @staticmethod
    def ajuste(x, y, inicio, fim):
        x, y = x[inicio:fim], y[inicio:fim]
        if len(x) < 3 or not np.isfinite(x).all() or np.ptp(x) <= 0:
            return None
        xc, yc = x - x.mean(), y - y.mean()
        a = float(xc @ yc / (xc @ xc))
        b = float(y.mean() - a * x.mean())
        r = y - a * x - b
        sst = float(yc @ yc)
        if sst <= 0 or a <= 0:
            return None
        amplitude = float(np.ptp(y))
        blocos = np.array_split(r, 3)
        curvatura = abs(float(np.median(blocos[0]) - 2 * np.median(blocos[1])
                              + np.median(blocos[2]))) / amplitude
        return dict(inicio=int(inicio), fim=int(fim), n=len(x),
                    E_gpa=a / 1000, slope_mpa=a, intercept_mpa=b,
                    r2=1 - float(r @ r) / sst, rmse=float(np.sqrt(np.mean(r*r))),
                    amplitude_tensao=amplitude, amplitude_deformacao=float(np.ptp(x)),
                    deformacoes_distintas=int(len(np.unique(x))),
                    curvatura=curvatura)

    def qualidade(self, r):
        p = self.p
        return r is not None and (
            r['n'] >= p['n_min'] and
            r['deformacoes_distintas'] >= p['deformacoes_distintas_min'] and
            r['amplitude_deformacao'] >= p['amplitude_deformacao_min'] and
            r['amplitude_tensao'] >= p['amplitude_tensao_min_mpa'] and
            r['r2'] >= p['r2_min'] and
            r['rmse'] / r['amplitude_tensao'] <= p['rmse_relativo_max'] and
            r['curvatura'] <= p['curvatura_relativa_max'])

    def candidatas(self, x, y, janela):
        p = self.p
        origem = float(np.median(self.x[:min(5, len(self.x))]))
        # Somente o primeiro ramo; não ordena nem reúne trechos de ciclos distintos.
        ultrapassa = np.flatnonzero(x > origem + p['deformacao_busca_max'])
        fim_busca = int(ultrapassa[0]) if len(ultrapassa) else len(x)
        inicio = janela - 1
        if fim_busca - inicio < p['n_min']:
            return []
        possiveis = np.arange(inicio, fim_busca - p['n_min'] + 1)
        possiveis = possiveis[x[possiveis] <= origem + p['deformacao_inicio_max']]
        if not len(possiveis):
            return []
        inicios = np.unique(possiveis[np.linspace(0, len(possiveis)-1,
                                                p['inicios_grade']).astype(int)])
        fins = np.unique(np.linspace(inicio + p['n_min'], fim_busca,
                                     p['fins_grade']).astype(int))
        aceitas = []
        for i in inicios:
            for f in fins:
                if f - i < p['n_min']:
                    continue
                r = self.ajuste(x, y, i, f)
                if not self.qualidade(r):
                    continue
                passo = max(1, round((f-i) * p['perturbacao_fracao']))
                variacoes = []
                for di, df in [(-passo, 0), (passo, 0), (0, -passo), (0, passo)]:
                    if i+di < inicio or f+df > len(x):
                        continue
                    v = self.ajuste(x, y, i+di, f+df)
                    if v is not None:
                        variacoes.append(abs(v['E_gpa']/r['E_gpa']-1))
                if len(variacoes) < 3 or max(variacoes) > p['variacao_e_max']:
                    continue
                r['variacao_E_max'] = max(variacoes)
                r['score'] = (r['curvatura'] + r['rmse']/r['amplitude_tensao']
                              + r['variacao_E_max'])
                aceitas.append(r)
        return sorted(aceitas, key=lambda r: (r['score'], r['inicio'], r['fim']))

    def familia(self, candidatas):
        for centro in candidatas:
            familia = []
            for r in candidatas:
                comum = max(0, min(r['fim'], centro['fim']) - max(r['inicio'], centro['inicio']))
                proporcao = comum / min(r['n'], centro['n'])
                if (abs(r['E_gpa']/centro['E_gpa']-1) <= self.p['variacao_e_max']
                        and proporcao >= self.p['sobreposicao_min']):
                    familia.append(r)
            if len(familia) >= self.p['familia_min']:
                return [centro] + [r for r in familia if r is not centro]
        return []

    def transicao(self, r, x, y):
        p = self.p
        limite = max(p['residuo_min_mpa'], p['residuo_fator_ruido'] * r['rmse'],
                     p['residuo_fracao_amplitude'] * r['amplitude_tensao'])
        residuos = y - r['slope_mpa'] * x - r['intercept_mpa']
        i = r['fim']
        ultimo_compativel = i - 1
        consecutivos = 0
        sentido_anterior = 0
        while i + p['bloco_n_min'] <= len(x):
            f = i + p['bloco_n_min']
            while (f < len(x) and f-i < p['bloco_n_max'] and
                   np.ptp(x[i:f]) < p['bloco_deformacao']):
                f += 1
            bloco = residuos[i:f]
            mediana = float(np.median(bloco))
            sentido = int(np.sign(mediana))
            afastado = (abs(mediana) > limite and
                        np.mean(np.sign(bloco) == sentido) >= p['fracao_sinal_min'])
            if afastado:
                consecutivos = consecutivos + 1 if sentido == sentido_anterior else 1
                if consecutivos >= p['persistencia_blocos']:
                    # Envelope inclui todos os pontos entre os limites, inclusive pequenas reversões.
                    return dict(status='estimado', indices=[ultimo_compativel, f-1],
                                deformacao=[float(np.min(x[ultimo_compativel:f])),
                                            float(np.max(x[ultimo_compativel:f]))],
                                tensao_mpa=[float(np.min(y[ultimo_compativel:f])),
                                            float(np.max(y[ultimo_compativel:f]))],
                                limiar_residuo_mpa=limite, sentido=sentido)
            else:
                consecutivos = 0
                # Blocos ambíguos não estreitam a faixa.
                if abs(mediana) <= limite:
                    ultimo_compativel = f - 1
            sentido_anterior = sentido
            i = f
        return dict(status='inconclusivo', motivo='Sem afastamento persistente confirmado.')

    def escoamento(self, r, x, y):
        offset = self.p['offset_deformacao']
        d = y - (r['slope_mpa'] * (x-offset) + r['intercept_mpa'])
        for i in range(max(r['fim'], 1), len(x)):
            if x[i] > x[i-1] and d[i-1] >= 0 and d[i] <= 0 and d[i-1] != d[i]:
                t = float(d[i-1] / (d[i-1]-d[i]))
                return dict(status='estimado', tensao_mpa=float(y[i-1]+t*(y[i]-y[i-1])),
                            deformacao=float(x[i-1]+t*(x[i]-x[i-1])),
                            offset=offset, convencao='Offset nas coordenadas de entrada; não é incerteza.')
        return dict(status='inconclusivo', motivo='Interseção de offset não encontrada no registro.')

    def executar(self, janela=1, janelas=()):
        if janelas and janela != 1:
            raise ValueError('Comparação de médias requer referência original (janela=1).')
        x, y = self.serie(janela)
        candidatas = self.candidatas(x, y, janela)
        familia = self.familia(candidatas)
        validos = np.isfinite(x) & np.isfinite(y)
        maior = int(np.nanargmax(y))
        r = dict(versao_metodo='1.0', status='inconclusivo', janela=janela,
                 parametros=self.p.copy(), n_registros=len(x),
                 hash_dados=hashlib.sha256(np.column_stack((self.y, self.x)).astype('<f8').tobytes()).hexdigest(),
                 referencia=None, candidatas=familia,
                 transicao=dict(status='inconclusivo', motivo='Sem família estável.'),
                 escoamento=dict(status='inconclusivo', motivo='Sem referência linear.'),
                 extremos=dict(tensao_maxima_mpa=float(y[maior]),
                               deformacao_na_tensao_maxima=float(x[maior]),
                               deformacao_maxima=float(x[validos].max()), ruptura_confirmada=False),
                 medias_moveis=[], ampliacoes=[], transicoes_candidatas=[])
        if not familia:
            r['motivo'] = 'Nenhuma família satisfaz o perfil de aços estruturais configurado.'
            return r
        ref = familia[0]
        r['referencia'] = ref
        # Diagnóstico de ampliação, sem substituir a referência durante a detecção.
        for fim in np.unique(np.linspace(ref['fim'], len(x), 12).astype(int)):
            ampliada = self.ajuste(x, y, ref['inicio'], int(fim))
            if ampliada is not None:
                r['ampliacoes'].append(dict(fim=int(fim), E_gpa=ampliada['E_gpa'],
                    variacao_E=abs(ampliada['E_gpa']/ref['E_gpa']-1), r2=ampliada['r2']))
        resultados = [self.transicao(c, x, y) for c in familia]
        r['transicoes_candidatas'] = resultados
        confirmadas = [t for t in resultados if t['status'] == 'estimado']
        if len(confirmadas) == len(resultados):
            faixa = [min(t['deformacao'][0] for t in confirmadas),
                     max(t['deformacao'][1] for t in confirmadas)]
            if faixa[1]-faixa[0] <= self.p['faixa_largura_max'] + 1e-12:
                r['transicao'] = dict(status='estimado', deformacao=faixa,
                    tensao_mpa=[min(t['tensao_mpa'][0] for t in confirmadas),
                                max(t['tensao_mpa'][1] for t in confirmadas)],
                    n_candidatas=len(familia), interpretacao='Envoltória de sensibilidade; sem probabilidade.')
            else:
                r['transicao'] = dict(status='inconclusivo', motivo='Envoltória muito ampla.',
                                      faixa_exploratoria=faixa)
        else:
            r['transicao'] = dict(status='inconclusivo', motivo='Candidatas sem confirmação consistente.',
                                  confirmadas=len(confirmadas), total=len(resultados))
        r['escoamento'] = self.escoamento(ref, x, y)
        r['status'] = ('estimado' if r['transicao']['status'] == 'estimado'
                       and r['escoamento']['status'] == 'estimado' else 'parcial')
        if janelas:
            r['medias_moveis'] = self.comparar(r, janelas)
        return r

    def comparar(self, base, janelas):
        janelas = sorted(set((1, *janelas)))
        ref = base['referencia']
        # MM retrospectiva: todos os suportes ficam dentro do intervalo original.
        i, f = ref['inicio'] + max(janelas)-1, ref['fim']
        comum = self.ajuste(self.x, self.y, i, f)
        if comum is None or f-i < self.p['n_min']:
            return []
        def oscilacao(x, y, ajuste):
            residuos = y[i:f] - ajuste['slope_mpa'] * x[i:f] - ajuste['intercept_mpa']
            return float(np.sqrt(np.mean(np.diff(residuos)**2)))
        oscilacao_original = oscilacao(self.x, self.y, comum)
        linhas = []
        for j in janelas:
            x, y = self.serie(j)
            ajuste = self.ajuste(x, y, i, f)
            if ajuste is None:
                continue
            completo = base if j == 1 else self.executar(j)
            de = abs(ajuste['E_gpa']/comum['E_gpa']-1)
            dy = None
            if base['escoamento']['status'] == completo['escoamento']['status'] == 'estimado':
                dy = abs(completo['escoamento']['tensao_mpa']/base['escoamento']['tensao_mpa']-1)
            dt = None
            if base['transicao']['status'] == completo['transicao']['status'] == 'estimado':
                dt = max(abs(a-b) for a,b in zip(base['transicao']['deformacao'], completo['transicao']['deformacao']))
            dm = abs(completo['extremos']['tensao_maxima_mpa']/base['extremos']['tensao_maxima_mpa']-1)
            dd = max(abs(completo['extremos'][chave]-base['extremos'][chave])
                     for chave in ('deformacao_maxima', 'deformacao_na_tensao_maxima')) / float(np.ptp(self.x))
            reducao = (1-oscilacao(x, y, ajuste)/oscilacao_original
                       if oscilacao_original > 1e-10 else None)
            linhas.append(dict(janela=j, n_comum=f-i, intervalo_comum=[i,f],
                E_mesmo_intervalo_gpa=ajuste['E_gpa'], variacao_E=de,
                reducao_oscilacao=reducao, variacao_deformacao=dd,
                rmse_original=float(np.sqrt(np.mean((self.y[i:f]-ajuste['slope_mpa']*self.x[i:f]-ajuste['intercept_mpa'])**2))),
                E_selecao_gpa=None if completo['referencia'] is None else completo['referencia']['E_gpa'],
                variacao_escoamento=dy, deslocamento_transicao=dt, variacao_maximo=dm,
                compativel_E=de <= self.p['mm_variacao_e_max'],
                compativel_escoamento=None if dy is None else dy <= self.p['mm_variacao_escoamento_max'],
                compativel_transicao=None if dt is None else dt <= self.p['mm_deslocamento_transicao_max'],
                compativel_maximo=dm <= self.p['mm_variacao_maximo_max'],
                compativel_deformacao=dd <= self.p['mm_variacao_deformacao_max'],
                interpretacao='Sensibilidade em relação ao original; não comprova exatidão.'))
        return linhas
