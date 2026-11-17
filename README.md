# Análise de ensaios de tração

Programa em Python para o tratamento e a análise de dados de ensaios de tração,
desenvolvido no Projeto Final de Curso (PFC) *Análise e tratamento de dados
provenientes de ensaios mecânicos, com foco na caracterização do comportamento de
materiais*, do Bacharelado em Engenharia Mecânica do IFSP – Campus Itaquaquecetuba.

- **Autor:** Kaique Gabriel Alves Lima
- **Orientador:** Prof. Dr. Wendel Marcos dos Santos

## O que o programa faz

A partir de um arquivo CSV com tensão e deformação, o programa:

- calcula médias móveis da curva (janelas 3, 5 e 7, ou outra informada), sem
  substituir os dados de entrada;
- seleciona automaticamente o intervalo de regressão linear usado para estimar o
  módulo de elasticidade, avaliando quantidade e amplitude dos dados, R², RMSE,
  curvatura dos resíduos, estabilidade do módulo e uma família de intervalos
  compatíveis;
- calcula a tensão pelo método do deslocamento de 0,2% (offset), a faixa de
  afastamento da linearidade e os valores máximos registrados;
- classifica o resultado como **estimado**, **parcial** ou **inconclusivo**;
- compara as médias móveis com os dados de entrada, no mesmo intervalo e com nova
  seleção do intervalo;
- apresenta tudo em uma interface gráfica (Matplotlib) e permite exportar a
  análise em JSON.

## Instalação

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt
```

## Como usar

```bash
python main.py                                    # interface com o ensaio A500 incluído
python main.py --dados ensaio_a.csv --comparar ensaio_b.csv
python main.py --explorador                       # painel detalhado de um ensaio
python main.py --json --comparar-mm               # análise reproduzível em JSON, sem interface
python main.py --dados caminho/ensaio.csv --json
python -B -m unittest discover -s tests -q        # testes
```

O CSV deve ter cabeçalho e trazer **tensão (MPa)** e **deformação (fração)** nas
duas primeiras colunas. Arquivos com as colunas `Sigma_true` e `e_true` são
reconhecidos pelo nome. Na interface, declare se as coordenadas são
**Verdadeiras** ou de **Engenharia**; o seletor não converte valores.

A saída `--json` registra a versão do método, um código de identificação dos
dados, os parâmetros utilizados, a reta de referência, a família de candidatas, a
faixa de afastamento, o offset, os extremos e, opcionalmente, a comparação das
médias móveis.

Os parâmetros ficam em [`configuracao.py`](configuracao.py). Leia a
[matriz de parâmetros](docs/MATRIZ_PARAMETROS.md) antes de interpretar as saídas.

## Como interpretar os resultados

- Os limites utilizados são **critérios exploratórios de engenharia**, não
  valores normativos.
- `estimado` não significa certificado; `parcial` mantém as propriedades que
  puderam ser calculadas; `inconclusivo` indica que os dados ou os critérios não
  permitiram formar uma família de intervalos.
- O offset de 0,2% é aplicado nas coordenadas do arquivo e não representa uma
  incerteza de ±0,2% nem o Rp0,2 normativo quando os dados estão em coordenadas
  verdadeiras.
- A faixa de afastamento não tem probabilidade associada e não corresponde ao
  limite elástico. O último registro não é considerado ruptura confirmada.
- O R² é utilizado como valor mínimo na triagem, junto com outros indicadores; um
  R² alto, sozinho, não indica o melhor trecho.

## Dados

O arquivo [`data/A500_t16_tensile.csv`](data/A500_t16_tensile.csv) vem da base
pública:

> HARTLOPER, A. R.; OZDEN, S.; DE CASTRO E SOUSA, A.; LIGNOS, D. G. *Database of
> Uniaxial Cyclic and Tensile Coupon Tests for Structural Metallic Materials*.
> Zenodo, 2022. Versão 1.0.0. DOI:
> [10.5281/zenodo.6965147](https://doi.org/10.5281/zenodo.6965147).

Esses dados são distribuídos pelos autores sob a licença
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) e não estão cobertos
pela licença do código. Os ensaios foram realizados pelos autores da base; este
projeto apenas analisa os dados disponibilizados.

Para reproduzir a comparação com os seis ensaios da base, baixe o pacote
`Clean_Data` da versão 1.0.0 e informe a pasta:

```bash
python -B scripts/validar_metodo.py --base caminho/para/Clean_Data
```

## Documentação

- [Matriz de parâmetros](docs/MATRIZ_PARAMETROS.md)
- [Justificativa dos intervalos do A500](docs/JUSTIFICATIVA_INTERVALOS_A500.md)
- [Validação ampliada (NPL e densidade de amostragem)](docs/CONCLUSAO_BACKEND.md)
- [Relatório de alterações](docs/RELATORIO_ALTERACOES.md) e
  [relatório da interface](docs/RELATORIO_INTERFACE.md)

## Licença

O código está disponível sob a [licença MIT](LICENSE).
