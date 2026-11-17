import argparse
import configuracao
from process.Dados import Dados


def main():
    parser = argparse.ArgumentParser(description='Explorador interativo de ensaios de tração')
    parser.add_argument('--dados', default=str(configuracao.ARQUIVO_DADOS), help='CSV: tensão MPa, deformação')
    parser.add_argument('--json', action='store_true', help='Análise reproduzível em JSON, sem interface')
    parser.add_argument('--janela', type=int, default=1, help='Janela de análise (1 = original)')
    parser.add_argument('--comparar-mm', action='store_true', help='Comparar janelas configuradas ao original')
    parser.add_argument('--comparar', help='Segundo CSV para comparação visual')
    parser.add_argument('--explorador', action='store_true', help='Abrir painel detalhado de um ensaio')
    args = parser.parse_args()
    if args.json:
        dados = Dados(args.dados)
        import json
        import sys
        from process.AnaliseMecanica import AnaliseMecanica
        if args.comparar_mm and args.janela != 1:
            parser.error('--comparar-mm requer --janela 1 para referência original.')
        try:
            resultado = AnaliseMecanica(dados).executar(args.janela, args.comparar_mm)
        except ValueError as exc:
            parser.error(str(exc))
        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False))
        return resultado
    if args.explorador:
        dados = Dados(args.dados)
        from process.Graficos import Graficos
        painel = Graficos(dados, janela=args.janela)
    else:
        from process.Comparacao import Comparacao
        painel = Comparacao(args.dados, args.comparar)
        if args.janela != 1:
            painel.definir_janela(0, str(args.janela))
    painel.mostrar()
    return painel


if __name__ == '__main__':
    main()
