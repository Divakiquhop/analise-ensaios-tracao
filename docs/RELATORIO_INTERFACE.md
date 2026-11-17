# Comparação visual de ensaios — 11/10/2026

A interface padrão agora apresenta dois ensaios lado a lado. Cada painel permite
abrir CSV, declarar coordenadas e selecionar uma janela de média móvel. Os
resultados destacados são E, tensão de offset 0,2%, deformação no offset e tensão
máxima da fonte analisada. O gráfico apresenta original, MM opcional, regressão e
marcador de offset. Uma opção mostra a zona de afastamento detectável.

A alternância entre curva completa e região inicial usa escalas comuns para
coordenadas compatíveis. Não há conversão implícita entre engenharia e grandezas
verdadeiras. Resultados parciais/inconclusivos são preservados. Os detalhes abrem
o explorador anterior, mantendo ajuste manual, candidatas e comparação de médias.
Os parâmetros e as fórmulas do backend não foram modificados.

## Concordância do escoamento com a referência do A500

O resumo da base [Zenodo, registro 6965147](https://zenodo.org/records/6965147)
registra 371,8 MPa para o arquivo A500_t16_tensile.csv. O programa calcula
371,8 MPa no original: diferença de 0,0 MPa na precisão apresentada. A comparação
já é reproduzida por scripts/validar_metodo.py e está registrada em
VALIDACAO_DADOS_REAIS.json. É evidência favorável para esta propriedade e este
ensaio, nas coordenadas utilizadas. Não é um valor universal para todos os graus
e produtos A500, nem uma medição independente adicional do mesmo corpo de prova.
Não valida, por extensão, a localização do início da não linearidade.

O acordo com o usuário foi incorporado como interpretação de validação; valores
externos não foram adicionados ao painel principal. A divergência relativa deve
ser comparada usando a mesma definição de escoamento e coordenadas. A tolerância
exploratória anterior de 2% permanece, sem novo ajuste para obter aprovação.

## Arquivos e verificações

- process/Comparacao.py: composição visual e carregamento independente.
- main.py: painel padrão; opções --comparar e --explorador; JSON preservado.
- process/Graficos.py: coordenadas nos rótulos e nome correto do afastamento.
- tests/test_comparacao.py: independência dos painéis, escalas, falhas de entrada.
- README.md: instruções de operação.

Imagens estáticas foram renderizadas e inspecionadas para a curva completa e a região inicial.
Os testes exercitam callbacks com backend gráfico Agg. O diálogo nativo de seleção
de arquivos e a operação manual da janela no desktop não foram verificados por
automação; não se declara validação completa de interação nativa.

Verificação final: 47 testes executados, 46 aprovados e um ignorado por ausência
de SciPy; nenhum erro. Verificação de whitespace do diff sem erros.

## Correção do retorno da ampliação

O botão do explorador foi renomeado para Intervalo / curva e agora restaura o
enquadramento completo no segundo clique. As mudanças são registradas no histórico
da barra do Matplotlib, permitindo Reset original view. Dois testes reproduziram
as falhas anteriores e passaram após a correção, inclusive após redesenhar o gráfico.

Precisão da fonte: os números 186626,77695922228 MPa (186,6268 GPa) e 371,8 MPa
foram lidos do arquivo Overall_Summary_2022-08-30_v1-0-0.csv da base Zenodo,
registro hidden_index=299, linha 301 contando o cabeçalho. Campos:
elastic_modulus__mpa_ e yield_stress__mpa_. O citekey aponta para Suzuki e Lignos
(2021), mas não foi verificado se o texto desse artigo apresenta esses números
exatos. A fonte direta dos valores é a tabela publicada com o conjunto de dados.

## Prolongamento visual — 13/10/2026

Uma função de desenho compartilhada permite prolongar as regressões pela área
visível. O segmento ajustado permanece destacado; a extensão é pontilhada.
A opção está na comparação e nos detalhes, incluindo regressões salvas e candidatas.
Nenhum ponto adicional entra no cálculo. A reta acompanha zoom/pan, sem extremos
numéricos artificiais nem alteração da escala para acomodar sua extrapolação.
O fim do segmento continua sendo o fim do suporte de estimação de E, não um limite
elástico. A extensão facilita visualizar afastamentos, sem validá-los fisicamente.
