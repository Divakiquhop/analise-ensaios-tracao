"""Validação externa com parâmetros congelados; não altera dados de entrada.

Baixa o ZIP público NPL em memória. JSON em stdout, sem salvar o download.
--base aponta para Clean_Data local. A reamostragem descarta pontos, sem interpolar.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request
import zipfile

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import configuracao as cfg
from process.Dados import Dados
from process.MetodoTracao import MetodoTracao

ZIP_URL = 'https://www.npl.co.uk/getattachment/bf46dd80-b0ca-43a5-b836-ad4dab8c0064/tensile-ascii-set.zip?lang=en-US'
REPORT_URL = 'https://www.npl.co.uk/getattachment/135ef6b3-4683-4a22-9bcc-e611a47c7bdb/SW-validation-eval.pdf?lang=en-US'
EXTRAS = [
    'S355J2_IPE200/S355J2_IPE200_FLANGE_DATA/LP1_Specimen_1_processed_data.csv',
    'S355J2_HEA160/S355J2_HEA160_FLANGE_DATA/LP1_Specimen_2_processed_data.csv',
    'S355J2_HEM320/WP3_HEM320_D_CRM20/LP1_Specimen_1_processed_data.csv',
    'S355J2_HEM320/WP3_HEM320_C_CRM20/LP1_Specimen_1_processed_data.csv',
    'S235275_Plates/S235275_Plate15/LP1_Specimen_2_processed_data.csv',
]


def adaptar(y, x):
    quadro = pd.DataFrame({'tensao': y, 'deformacao': x}, dtype=float)
    if len(quadro) < 3 or not np.isfinite(quadro.to_numpy()).all():
        raise ValueError('Dados insuficientes ou não finitos.')
    dados = Dados.__new__(Dados)
    dados.local_dos_dados = quadro.reset_index(drop=True)
    return dados


def ler_npl(conteudo):
    linhas = list(csv.reader(io.StringIO(conteudo.decode('latin1')), delimiter=';'))
    linhas = [r for r in linhas if r]
    cab = {r[0]: r[1:] for r in linhas[:25]}
    if cab['So'][1] != 'mm2' or cab['Le'][1] != 'mm' or linhas[24] != ['s', 'mm', 'mm', 'kN']:
        raise ValueError('Layout/unidades NPL inesperados.')
    valores = np.array(linhas[25:], dtype=float)
    if valores.shape != (int(cab['N'][0]), 4):
        raise ValueError('Número de registros NPL divergente do cabeçalho.')
    return adaptar(valores[:, 3]*1000/float(cab['So'][0]),
                   valores[:, 2]/float(cab['Le'][0]))


def avaliar(dados, referencia_e=None, inicio_nominal=None):
    r = MetodoTracao(dados, cfg.PARAMETROS).executar()
    e = None if r['referencia'] is None else r['referencia']['E_gpa']
    faixa = r['transicao'].get('deformacao')
    x = dados.local_dos_dados.iloc[:, 1].to_numpy()
    origem = float(np.median(x[:5]))
    limite = np.flatnonzero(x > origem + cfg.PARAMETROS['deformacao_busca_max'])
    return dict(n=len(x), n_busca=int(limite[0]) if len(limite) else len(x),
                status=r['status'], E_gpa=e,
                erro_E_relativo=None if e is None or referencia_e is None else e/referencia_e-1,
                offset=r['escoamento'], transicao=r['transicao'],
                inicio_nominal=inicio_nominal,
                contem_inicio_nominal=None if faixa is None or inicio_nominal is None else faixa[0] <= inicio_nominal <= faixa[1],
                hash_numerico=r['hash_dados'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    args = p.parse_args()
    blob = urllib.request.urlopen(ZIP_URL, timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(blob))
    npl, series = [], {}
    # Referências do relatório NPL, seção 7.7 e tabela 9; não são novos thresholds.
    intervalos_offset = {'57': [434.3, 434.3], '61': [438.1, 441.6], '63': [446.5, 448.2]}
    for numero in ('13', '57', '61', '63'):
        conteudo = z.read(numero + '.txt')
        dados = ler_npl(conteudo)
        sintetico = numero != '13'
        r = avaliar(dados, 207.5 if sintetico else None, 350/207500 if sintetico else None)
        r.update(arquivo=numero+'.txt', coordenadas='engenharia',
                 sha256_arquivo=hashlib.sha256(conteudo).hexdigest(),
                 referencia_offset_mpa=intervalos_offset.get(numero),
                 referencia_E_gpa=[221.0, 228.8] if not sintetico else [207.5, 207.5])
        npl.append(r)
        series['NPL'+numero] = dados
    extras = []
    for nome in EXTRAS:
        caminho = args.base / nome
        if not caminho.is_file():
            extras.append(dict(arquivo=nome, status='arquivo_ausente'))
            continue
        df = pd.read_csv(caminho)
        dados = adaptar(df['Sigma_true'], df['e_true'])
        extras.append(dict(arquivo=nome, coordenadas='verdadeiras',
                           sha256_arquivo=hashlib.sha256(caminho.read_bytes()).hexdigest(),
                           **avaliar(dados)))
    for nome, arquivo in [('A500', 'A500/A500_t16_tensile.csv'),
                          ('A992_web', 'A992_Gr50/A992_W14X82_web/A992_t12_tensile.csv')]:
        series[nome] = Dados(args.base / arquivo)
    densidades = []
    for nome in ('A500', 'A992_web', 'NPL57', 'NPL61', 'NPL63'):
        df = series[nome].local_dos_dados
        e_base = avaliar(series[nome])['E_gpa']
        for fator in (1, 2, 4, 8):
            # Fase zero fixa; mantém apenas índices 0, k, 2k... Não simula novo ensaio.
            amostra = df.iloc[::fator]
            r = avaliar(adaptar(amostra.iloc[:, 0], amostra.iloc[:, 1]), e_base,
                        350/207500 if nome.startswith('NPL') else None)
            densidades.append(dict(serie=nome, fator=fator, fase=0,
                                   referencia_E='resultado da série completa', **r))
    saida = dict(versao_metodo='1.0', parametros=cfg.PARAMETROS,
                 fonte_npl=ZIP_URL, relatorio_npl=REPORT_URL,
                 sha256_zip=hashlib.sha256(blob).hexdigest(),
                 fonte_extras='https://zenodo.org/records/6965147',
                 npl=npl, adicionais=extras, densidades=densidades)
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(saida, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
