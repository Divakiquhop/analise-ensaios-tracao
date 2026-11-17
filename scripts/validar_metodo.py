"""Comparação reproduzível com curvas locais da base Zenodo, sem baixar arquivos.

python scripts/validar_metodo.py --base ".../Clean_Data"
Saída JSON em stdout. Referências: Overall_Summary_2022-08-30_v1-0-0.csv,
https://zenodo.org/records/6965147. Não altera dados nem documentos acadêmicos.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from process.Dados import Dados
from process.AnaliseMecanica import AnaliseMecanica
from process.MetodoTracao import MetodoTracao
import configuracao as cfg

REFERENCIAS = {
    'A500/A500_t16_tensile.csv': (186.62677695922228, 371.8),
    'BCR295/BCR295_t22_tensile.csv': (182.6440511241908, 436.89603137547135),
    'A992_Gr50/A992_W14X82_web/A992_t12_tensile.csv': (199.14227626306273, 376.7328897545218),
    'A992_Gr50/A992_W14X82_flange/A992_t22_tensile.csv': (206.11492010140425, 401.0051707227034),
    'BCP325/BCP325_t22_tensile.csv': (217.4905437352245, 382.58499675527565),
    'HYP400/HYP_t27_tensile.csv': (230.25312109862675, 452.13181473627577),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True, help='Diretório Clean_Data extraído')
    args = parser.parse_args()
    resultados = []
    for arquivo, (E, fy) in REFERENCIAS.items():
        caminho = args.base / arquivo
        if not caminho.is_file():
            resultados.append(dict(arquivo=arquivo, status='arquivo_ausente'))
            continue
        dados = Dados(caminho)
        r = AnaliseMecanica(dados).executar(comparar_janelas=True)
        e_calc = None if r['referencia'] is None else r['referencia']['E_gpa']
        fy_calc = r['escoamento'].get('tensao_mpa')
        de = None if e_calc is None else abs(e_calc/E-1)
        df = None if fy_calc is None else abs(fy_calc/fy-1)
        sensibilidade = []
        # Um fator de cada vez; resultados não alteram os defaults.
        for chave, valores in {'r2_min': (.92, .94, .96, .97),
                              'variacao_e_max': (.02, .03, .05),
                              'residuo_fator_ruido': (1.5, 2., 2.5)}.items():
            for valor in valores:
                s = MetodoTracao(dados, dict(cfg.PARAMETROS, **{chave: valor})).executar()
                sensibilidade.append(dict(parametro=chave, valor=valor, status=s['status'],
                    E_gpa=None if s['referencia'] is None else s['referencia']['E_gpa'],
                    transicao=s['transicao']))
        resultados.append(dict(arquivo=arquivo, status=r['status'],
            E_referencia_gpa=E, E_gpa=e_calc, diferenca_E=de,
            offset_referencia_mpa=fy, offset_mpa=fy_calc, diferenca_offset=df,
            criterio_E=None if de is None else de <= .05,
            criterio_offset=None if df is None else df <= .02,
            faixa=r['transicao'], hash_dados=r['hash_dados'],
            medias_moveis=r['medias_moveis'], sensibilidade=sensibilidade))
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(dict(versao_metodo='1.0', parametros=cfg.PARAMETROS,
        fonte='https://zenodo.org/records/6965147',
        interpretacao='Diferenças entre procedimentos; não incerteza metrológica.',
        resultados=resultados), ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
