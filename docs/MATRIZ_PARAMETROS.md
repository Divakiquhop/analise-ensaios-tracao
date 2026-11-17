# Matriz de parâmetros e aceitação — método 1.0

Escopo: curvas de **tração monotônica de aços estruturais próximos do A500**,
tensão em MPa, deformação como fração (não porcentagem), pares na ordem de aquisição.
O perfil pressupõe registro desde o começo do carregamento. Não é um método
universal, nem certificação ASTM/ISO. Ciclos, compressão, ligas leves, curvas que
começam já plastificadas e aquisição insuficiente exigem outro perfil/validação.

Fonte executável: `configuracao.PARAMETROS`, copiada integralmente em cada JSON.
Todos os thresholds abaixo são **escolhas exploratórias de engenharia**, não
valores extraídos de normas. A adequação será reavaliada com mais ensaios.

`INICIOS`, `FINS`, `PASSO_REGRESSAO`, `RMSE_MAX_MPA`, `PERTURBACAO`,
`VIZINHOS_MIN` e `FRACAO_ROBUSTA_MIN` permanecem na API legada de exploração
`gerar_regressoes/selecionar_candidatas`. Não controlam o novo fluxo automático
`executar`. `NUM_CANDIDATAS` e `DISTANCIA_MIN_CANDIDATAS` controlam apenas a
seleção das duas retas exibidas no painel, não a família científica completa.

| Parâmetro | Valor inicial | Unidade / critério |
|---|---:|---|
| n_min | 30 | Pontos válidos por regressão |
| deformacoes_distintas_min | 6 | Valores distintos; mínimo de informação, não resolução instrumental |
| amplitude_deformacao_min | 0,0006 | Fração, amplitude mínima do trecho |
| amplitude_tensao_min_mpa | 80 | MPa, evita trechos pequenos de aparente linearidade |
| deformacao_busca_max | 0,0012 | Fração acima da mediana das primeiras cinco deformações; teto conservador de busca de E, **não limite elástico** |
| deformacao_inicio_max | 0,0003 | Fração acima da mesma origem; permite excluir acomodação inicial |
| inicios_grade / fins_grade | 12 / 18 | Amostragem determinística de índices na região física; máximo 216 combinações |
| r2_min | 0,94 | Piso auxiliar de triagem, antes 0,97 |
| rmse_relativo_max | 0,09 | RMSE/amplitude de tensão; substitui limite absoluto no fluxo automático |
| curvatura_relativa_max | 0,04 | Valor absoluto de m1−2m2+m3 dividido pela amplitude; m são medianas dos resíduos nos terços do intervalo |
| variacao_e_max | 0,03 | Variação máxima de E nas perturbações e entre centro/família |
| perturbacao_fracao | 0,02 | Fração do número de pontos do intervalo, mínimo um ponto, em cada extremo |
| familia_min | 3 | Número de intervalos compatíveis; não são réplicas experimentais independentes |
| sobreposicao_min | 0,5 | Interseção dividida pelo tamanho do menor intervalo |
| bloco_deformacao | 0,0001 | Amplitude-alvo de deformação por bloco da detecção |
| bloco_n_min / bloco_n_max | 5 / 50 | Limites de tamanho do bloco; os dados podem ultrapassar a amplitude-alvo por amostragem esparsa |
| persistencia_blocos | 2 | Blocos consecutivos com desvio no mesmo sentido |
| residuo_fator_ruido | 2 | Multiplicador do RMSE do trecho de referência; **não significa 95% de confiança** |
| residuo_min_mpa | 2 | Piso de afastamento em MPa |
| residuo_fracao_amplitude | 0,01 | Piso relativo à amplitude de tensão da referência |
| fracao_sinal_min | 0,8 | Fração de resíduos do bloco com sinal igual ao da mediana |
| faixa_largura_max | 0,0008 | Largura máxima da envoltória em deformação; exceder retorna inconclusivo |
| offset_deformacao | 0,002 | Deslocamento fixo da reta; **não é incerteza ±0,2%** |
| mm_variacao_e_max | 0,05 | Compatibilidade de E no suporte comum com o original |
| mm_variacao_escoamento_max | 0,02 | Compatibilidade de tensão no offset após repetir seleção |
| mm_variacao_maximo_max | 0,01 | Compatibilidade de tensão máxima registrada |
| mm_variacao_deformacao_max | 0,01 | Alteração da maior deformação ou deformação no máximo de tensão, dividida pela amplitude total de deformação original |
| mm_deslocamento_transicao_max | 0,0002 | Máximo deslocamento de um extremo da faixa; sem comparação se inconclusiva |

## Seleção e rastreabilidade

Triagem por amplitude, diversidade, R², erro relativo e curvatura. Perturbar cada
extremo em ambos os sentidos; exigir pelo menos três vizinhos calculáveis e
variação de E <=3%. Ordenar pela soma dos três indicadores adimensionais:
curvatura + RMSE/amplitude + máxima variação de E. Pesos iguais são uma escolha
heurística registrada, não uma otimização científica estabelecida.

Selecionar o primeiro centro que possua pelo menos três candidatas sobrepostas
e com E compatível. A referência é esse centro efetivamente calculado. A família
completa, seus resíduos resumidos, transições individuais e ampliações de E
ficam no JSON; duas candidatas podem ser exibidas no painel. A ampliação é
diagnóstico, não critério automático adicional de exclusão nesta versão.

No trecho posterior à referência, o limiar é o máximo entre 2 MPa, 2×RMSE e 1%
da amplitude da referência. Comparar a mediana dos resíduos por bloco com esse
limiar, exigindo 80% no mesmo sentido e dois blocos consecutivos. A faixa vai do
último bloco compatível ao fim da confirmação. Amostragem, ruído e sensibilidade
do detector afetam esses limites: **não há garantia de cobertura do limite físico**.
Exigir confirmação em toda a família e envoltória de largura <=0,0008. Caso
contrário, conservar E/offset quando disponíveis e declarar a faixa inconclusiva.

## Médias móveis e propriedades

Manter médias retrospectivas sobre os dois eixos, compatíveis com a interface
existente. Janelas 1 (controle), 3, 5 e 7. As análises não reordenam nem alteram o CSV.
Comparar regressões no mesmo conjunto de índices, começando em início+maior_janela−1:
nenhuma janela utiliza pontos anteriores ao intervalo original. Depois repetir
todo o procedimento com cada janela. Compatibilidade com o original é avaliação
de sensibilidade, não prova de preservação do valor verdadeiro. Não há recomendação
universal/automática nem soma de percentuais para obter uma nota de qualidade.

A redução de oscilação é `1 − RMS(diff(resíduos_MM))/RMS(diff(resíduos_originais))`,
no suporte comum, com cada resíduo medido contra sua própria reta. Se o denominador
for numericamente zero, retorna null. É um indicador descritivo de variação entre
pontos, não medida independente de ruído instrumental nem frequência em Hz.

O offset usa `sigma = E*(epsilon−0,002)+b`, na convenção de entrada. Neste CSV
as coordenadas são verdadeiras. Não rotular como Rp0,2 normativo sem estabelecer
a conversão/convenção adequada. O código da base rlmtp usa intercepto zero no
offset; a diferença é intencional e documentada. Máximo registrado, deformação
nesse máximo e maior deformação registrada são grandezas separadas; nenhum
último ponto é declarado ruptura. A MM pode atenuar extremos; não substitui
uma medida de resistência máxima de engenharia sem considerar as coordenadas.

## Matriz de aceitação

| Caso | Critério |
|---|---|
| Reta + ruído, múltiplas sementes | E com erro <=5%; nenhuma transição nem offset inventados |
| Curvas bilineares E=185/200/215 GPa | E com erro <=5%; faixa próxima da transição conhecida; largura <0,0006; offset com erro <=3 MPa |
| Discretização 0,0001 e acomodação inicial | E com erro <=5%; referência encontrada |
| Curva curta ou deformação constante | Resultado inconclusivo, sem exceção inesperada |
| Repetição da mesma entrada | Resultado idêntico; parâmetros, hash e versão registrados |
| MM | Suporte comum, original intacto, compatibilidade por finalidade; faltante = null |
| A500, BCR295, A992 (dois ensaios) | Comparação exploratória: diferença de E <=5%, offset <=2% frente à base; faixa pode ser inconclusiva |
| BCP325 e HYP400 | Registrar resultado, inclusive ausência de família; não relaxar thresholds só para aprovar |

Os erros de referência são diferenças entre procedimentos, não incertezas
metrológicas. Não há referência independente do fim da linearidade nos ensaios
reais usados. Logo, a precisão física dessa faixa permanece sem validação real.

## Referências e limites de transferência

- Hartloper et al., base: https://zenodo.org/records/6965147
- Implementação comparativa: https://github.com/ahartloper/rlmtp/blob/master/rlmtp/yield_properties.py
- Suttner & Merklein (2017), DOI 10.1016/j.jmatprotec.2016.10.024:
  justifica investigar o intervalo; **não implementamos seu algoritmo de trabalho de deformação**.
- Lord & Morrell (2010): https://eprintspublications.npl.co.uk/4797/
- Schmid et al. (2022), DOI 10.1021/acsmeasuresciau.1c00054:
  fundamenta cautela com filtros, não os thresholds deste programa.
- TENSTAND: https://www.npl.co.uk/products-services/advanced-materials/tensile-testing
  é uma possibilidade de validação futura, não foi executado neste ciclo.
