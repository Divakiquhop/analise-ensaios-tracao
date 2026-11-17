from pathlib import Path

ARQUIVO_DADOS = Path(__file__).resolve().parent / 'data' / 'A500_t16_tensile.csv'

JANELAS_MM = (3, 5, 7)

N_MIN = 30

# Grade legada: mantida para exploração explícita e compatibilidade da API.
# O painel automático usa PARAMETROS (região física), não INICIOS/FINS.
PASSO_REGRESSAO = 10

INICIOS = range(0, 151, PASSO_REGRESSAO)

FINS = range(100, 501, PASSO_REGRESSAO)

INTERVALO_INICIAL = (10, 400)

R2_MIN = 0.94

VARIACAO_E_MAX = 0.03

RMSE_MAX_MPA = 15.0

JANELA_ESTABILIDADE = 5

PERTURBACAO = 5

VIZINHOS_MIN = 4

FRACAO_ROBUSTA_MIN = 0.75

NUM_CANDIDATAS = 2

DISTANCIA_MIN_CANDIDATAS = 20

# Perfil exploratório para tração de aços estruturais.
# Frações de deformação, tensão em MPa. Não são limites normativos.
PARAMETROS = {
    'n_min': N_MIN,
    'deformacoes_distintas_min': 6,
    'amplitude_deformacao_min': 0.0006,
    'amplitude_tensao_min_mpa': 80.0,
    'deformacao_busca_max': 0.0012,
    'deformacao_inicio_max': 0.0003,
    'inicios_grade': 12,
    'fins_grade': 18,
    'r2_min': R2_MIN,
    'rmse_relativo_max': 0.09,
    'curvatura_relativa_max': 0.04,
    'variacao_e_max': VARIACAO_E_MAX,
    'perturbacao_fracao': 0.02,
    'familia_min': 3,
    'sobreposicao_min': 0.5,
    'bloco_deformacao': 0.0001,
    'bloco_n_min': 5,
    'bloco_n_max': 50,
    'persistencia_blocos': 2,
    'residuo_fator_ruido': 2.0,
    'residuo_min_mpa': 2.0,
    'residuo_fracao_amplitude': 0.01,
    'fracao_sinal_min': 0.8,
    'faixa_largura_max': 0.0008,
    'offset_deformacao': 0.002,
    'mm_variacao_e_max': 0.05,
    'mm_variacao_escoamento_max': 0.02,
    'mm_variacao_maximo_max': 0.01,
    'mm_variacao_deformacao_max': 0.01,
    'mm_deslocamento_transicao_max': 0.0002,
}
