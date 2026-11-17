# Fundamentação dos intervalos de regressão do A500

13/10/2026. Análise sobre o CSV original, sem média móvel; índices Python
[início, fim), com fim exclusivo. Não altera o documento acadêmico nem os
critérios automáticos do programa.

## Pergunta e conclusão

Qual trecho fornece uma estimativa defensável da inclinação inicial e quanto ela
muda ao incluir tensões mais elevadas? Esta pergunta distingue propriedades a
estimar e domínio de ajuste; não usa aparência gráfica como critério científico.

Recomenda-se [17,301) como referência principal exploratória de E e [11,444) como
candidato ampliado para análise de sensibilidade. Não são duas determinações
independentes nem duas estimativas igualmente validadas do limite elástico.
O prolongamento da reta permite examinar resíduos fora do suporte do ajuste,
mas não acrescenta observações à regressão nem valida a extrapolação.

## O que as fontes efetivamente sustentam

1. **Lord, Rides e Loveday (2005), NPL DEPC MPE 016**, *TENSTAND WP3 Final
   Report: Modulus Measurement Methods*. Consultados resumo executivo e seção 3,
   páginas impressas 3–4. O relatório trata a determinação da inclinação inicial
   como problema de medição próprio e mostra que alterações de módulo afetam a
   tensão de offset. Isso fundamenta avaliar E e offset separadamente; não fornece
   os nossos índices ou thresholds. É uma fonte metodológica histórica, não uma
   declaração sobre exigências normativas atuais.
   https://www.npl.co.uk/getattachment/2626b8f4-4a4f-4bd5-b5c9-d64c383e1d9e/Modulus-measurement.pdf?lang=en-US

2. **Lord e Morrell (2010)**, *Elastic modulus measurement — obtaining reliable
   data from the tensile test*, Metrologia 47, S41–S49. O resumo disponível no
   repositório NPL destaca extensometria, alinhamento, análise, validação de
   software e incerteza. Assim, concordar com um valor publicado não elimina as
   limitações experimentais. Não foi consultado o texto integral desse artigo.
   https://eprintspublications.npl.co.uk/4797/

3. **Suttner e Merklein (2017)**, *A new approach for the determination of the
   linear elastic modulus from uniaxial tensile tests of sheet metals*, Journal
   of Materials Processing Technology 241, 64–72.
   DOI: 10.1016/j.jmatprotec.2016.10.024. O resumo institucional apresenta um
   critério baseado em trabalho de deformação para determinar um limite superior
   dependente do material. Sustenta que a escolha do intervalo merece investigação;
   não autoriza transferir um limite numérico ao A500. Não implementamos esse método
   e não atribuímos ao artigo validação dos nossos índices. Texto integral não
   consultado nesta pesquisa.
   https://cris.fau.de/publications/223261874/

4. **Hartloper et al. (2022)**, base Zenodo, DOI 10.5281/zenodo.6965147.
   O arquivo Overall_Summary_2022-08-30_v1-0-0.csv, registro hidden_index=299,
   informa E=186626,77695922228 MPa e escoamento=371,8 MPa para
   Clean_Data/A500/A500_t16_tensile.csv. São propriedades calculadas publicadas
   para a mesma curva, não ensaio independente nem valores universais do A500.
   A coluna nominal fy_n__mpa_ contém 315 MPa, uma grandeza distinta do resultado
   calculado. A fonte direta dos números é essa tabela, não uma passagem verificada
   do artigo experimental associado, Suzuki e Lignos (2021).
   https://zenodo.org/records/6965147

5. **Código rlmtp, compute_modulus / yield_properties**. A implementação pública
   estima a inclinação entre frações 0,01 e 0,66 da tensão nominal informada. É um
   precedente concreto de estimação de E abaixo do escoamento, não uma norma.
   Com nominal de 315 MPa, esses valores são 3,15 e 207,9 MPa; a seleção por índices
   e o corte exclusivo produzem [7,274) neste CSV, reproduzindo E=186,6268 GPa.
   Nosso algoritmo usa outro critério: região inicial de busca, qualidade dos
   resíduos e estabilidade. Não se deve apresentá-lo como reprodução integral do
   rlmtp; inclusive a convenção de intercepto da reta de offset difere.
   https://github.com/ahartloper/rlmtp/blob/master/rlmtp/yield_properties.py

## Evidência numérica local

| Indicador | [17,301) | [11,444) |
|---|---:|---:|
| Pontos | 284 | 433 |
| Deformações distintas | 13 | 21 |
| E (GPa) | 186,2974 | 180,3492 |
| Diferença relativa ao E da base | −0,1765% | −3,3637% |
| R² | 0,96194 | 0,98060 |
| RMSE (MPa) | 12,2972 | 12,7156 |
| Indicador de curvatura normalizado | 0,001781 | 0,038453 |
| Maior tensão observada dentro do ajuste (MPa) | 225,3 | 319,2 |
| Escoamento por offset calculado (MPa) | 371,8 | 371,8 |

O indicador de curvatura é a segunda diferença das medianas dos resíduos nos três
terços, normalizada pela amplitude de tensão. Não é uma curvatura geométrica nem
um teste estatístico de significância. Ambos passam pela triagem básica atual;
o ampliado se aproxima do threshold exploratório de 0,04. A busca automática
atual é limitada à região inicial e não chega a avaliar [11,444) como candidato.
Logo, seria incorreto dizer que houve uma competição automática entre ambos.

Mantendo o início em 11 e variando o fim, E passa por 186,06 GPa (301),
184,97 (375), 184,73 (400), 182,26 (425) e 180,35 (444). É uma evidência
descritiva de sensibilidade à ampliação, não um detector validado do início plástico.
R² cresce apesar da mudança de inclinação: minimizar esse problema só por R²
selecionaria uma propriedade diferente sem resolver a adequação física.

O offset igual em ambos decorre da interseção com o mesmo segmento horizontal do
registro, entre deformações 0,0038 e 0,0040, a 371,8 MPa. As deformações calculadas
são aproximadamente 0,003951 e 0,003995. Assim, o escoamento confirma concordância
de processamento nesse caso, mas não discrimina essas duas escolhas de módulo.

## Argumentos e limites para cada candidato

**17–301:** estima a inclinação inicial em um domínio restrito, com pequena
curvatura residual e concordância com o valor publicado. O uso de um domínio
inicial tem respaldo nas fontes acima. Entretanto, o teto de busca de deformação
0,0012 e os pesos da seleção são heurísticas do projeto. A proximidade à referência
é uma verificação posterior, não deve virar um objetivo de ajuste de parâmetros.
Os 284 pontos incluem apenas 13 deformações distintas: número de linhas não é
equivalente a informação independente. Não alegar exatidão metrológica comprovada.

**11–444:** cobre maior amplitude de tensão e mais níveis distintos de deformação;
é uma alternativa útil para verificar se a estimativa permanece estável ao ampliar
o suporte. Sua divergência de E ainda está dentro da tolerância exploratória de 5%
usada no projeto, mas isso não demonstra equivalência física. A maior curvatura
residual e a queda progressiva de E desaconselham promovê-lo automaticamente a
referência principal. O fundamento é análise de sensibilidade do intervalo, não
aparência visual nem a existência de literatura que prescreva o ponto 444.

**225,3 e 319,2 MPa não são propriedades novas do material.** São máximos observados
dentro de dois subconjuntos. A maior tensão registrada na curva inteira permanece
520 MPa, em coordenadas verdadeiras. Nenhum desses três números determina, por si,
limite de proporcionalidade, limite elástico ou resistência máxima de engenharia.
Uma proximidade de 319,2 com o nominal de 315 MPa tampouco demonstra elasticidade.

## Redação proposta para a defesa metodológica

Adotou-se uma regressão de referência no trecho inicial [17,301) para estimar o
módulo, considerando qualidade dos resíduos e estabilidade do ajuste. Comparou-se
o resultado com o valor publicado para o mesmo ensaio e com um intervalo ampliado
[11,444), empregado como análise de sensibilidade. A ampliação elevou a cobertura
de tensões, mas reduziu o módulo e aumentou o indicador de curvatura residual.
Por isso, manteve-se o primeiro intervalo como referência exploratória, sem
interpretar sua extremidade como limite elástico. O segundo foi conservado como
alternativa investigativa, sem atribuir à sua tensão final significado físico
ainda não validado. A extensão gráfica das retas serve à inspeção do afastamento,
não à comprovação da elasticidade fora dos intervalos ajustados.

## Escopo da alteração visual

Somente os segmentos de candidatas e regressões salvas passaram de tracejados a
contínuos. O prolongamento pontilhado, os parâmetros e a seleção automática foram
preservados. [11,444) não foi fixado como candidato automático: isso seria uma
mudança metodológica adicional e específica deste arquivo. Pode ser avaliado e
salvo pelo controle manual existente. Na imagem enviada, R2 é [5,444), não
[11,444); os números da tabela acima não devem ser atribuídos àquela R2.
