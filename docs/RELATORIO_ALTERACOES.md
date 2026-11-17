# Relatório de alterações — 11/10/2026

## Escopo e preservação

Implementado o método aprovado na conversa, no programa. Nenhum documento
acadêmico Word/ODT/PDF foi editado. Nenhuma dependência foi instalada. O CSV A500
permanece com SHA-256 `aa235036521d41735508232a251d1159289bcd793bbca450c54360988763a19a`.

A pasta não era um repositório Git. Foi inicializada e recebeu o commit baseline
`8320bec`, com o código, testes, dependências e CSV preexistentes. A alteração
metodológica fica em commit separado. Autor configurado somente neste repositório,
conforme informado pelo usuário. Não houve push. `Colab comands.txt` e o PDF do
gráfico preexistente permaneceram fora dos commits e não foram modificados.

## O que mudou

- `configuracao.py`: perfil central `PARAMETROS`, thresholds com unidades
  documentadas; R² mínimo auxiliar 0,94 (antes 0,97); MM padrão 3/5/7.
- `process/MetodoTracao.py`: busca na região inicial em deformação, triagem por
  informação/amplitude, estabilidade de E, família sobreposta, referência realmente
  avaliada, resíduos por blocos e faixa de transição por persistência. Retorna
  resultados estimados, parciais ou inconclusivos. Registra ampliação progressiva,
  transições por candidata, hash numérico e parâmetros. Offset com intercepto
  consistente e nas coordenadas de entrada. Extremos de tensão/deformação separados.
- Comparação MM: suporte comum dentro do intervalo original e repetição da seleção;
  sensibilidade de E, offset, faixa, tensão máxima e deformações. Indicador de
  redução de oscilações dos resíduos. Não há recomendação automática universal.
- `process/AnaliseMecanica.py`: integra o novo método sem remover a API exploratória;
  corrige a seleção de quantidade=1 para não retornar uma segunda candidata.
- `process/Graficos.py`: usa a nova análise; referência deixa de ser a média dos
  índices C1/C2. Exibe faixa automática e ponto de offset. Campo para escolher a
  janela efetivamente usada no ajuste, independente da visibilidade das MM.
  Botão abre tabela comparativa. Último ponto deixa de ser rotulado como ruptura.
- `main.py`: modo `--json`, janela e comparação de MM sem abrir interface.
- `tests`: novos casos sintéticos, A500, determinismo, parâmetros inválidos, fonte
  da interface, tabela MM e regressão da escolha do centro da família.
- `scripts/validar_metodo.py`: comparação reproduzível com seis curvas locais da
  base e análise de sensibilidade de R², estabilidade e limiar de resíduos.
- README, matriz de parâmetros, plano/registro e snapshot JSON de validação.

## Critérios e limites científicos

Consulte `MATRIZ_PARAMETROS.md` para a matriz completa. Os valores são critérios
exploratórios de engenharia. Não constituem recomendações normativas nem um
algoritmo publicado reproduzido integralmente. A regressão e o escoamento usam
coordenadas verdadeiras no arquivo A500. Offset 0,002 não é incerteza ±0,2%.
O resultado não deve ser chamado automaticamente de Rp0,2 normativo.

A faixa é uma envoltória de sensibilidade entre candidatas aceitas. Não tem
probabilidade/confiança atribuída, não é uma tensão admissível de projeto e não
prova o limite reversível do material. Os ensaios reais não fornecem uma referência
independente desse término; portanto a exatidão da faixa em dados reais continua
em aberto. A largura máxima 0,0008 é um limite de utilidade exploratória.

## Verificações executadas

Ambiente: Python 3.13.3, NumPy 2.2.6, Pandas 2.2.3, Matplotlib 3.10.3.

- Baseline: 25 testes executados, sem falhas, 1 ignorado (SciPy ausente).
- Suíte final: **44 testes executados, 43 aprovados, 1 ignorado**, sem falhas.
- Testes novos foram observados falhando antes das respectivas implementações.
- Curvas sintéticas: E=185/200/215 GPa, transições distintas, ruído, múltiplas
  sementes, discretização, acomodação, menor densidade de pontos, pico isolado,
  reta sem transição, dados curtos e deformação constante.
- Referência de E dentro de 5% nas curvas sintéticas previstas; offset dentro
  de 3 MPa da solução bilinear analítica nos cenários testados.
- Saída JSON testada como subprocesso e reanálise determinística verificada.
- Interface exercitada com backend Agg: fonte, seletores, regressão principal
  e tabela. Imagens estáticas inspecionadas; sessão interativa nativa não testada.
- Revisão independente parcial encontrou erro na ordenação do centro da família.
  Reproduzido com 194,2/200/205,8 GPa e corrigido com teste de regressão. A revisão
  independente não foi concluída por indisponibilidade do agente; houve revisão
  adicional local do diff e da integração.

Comando: `python -B -m unittest discover -s tests -q`.

## Comparação real com parâmetros idênticos

Valores de referência: `Overall_Summary_2022-08-30_v1-0-0.csv` da base
https://zenodo.org/records/6965147. Comparação entre procedimentos, não incerteza
metrológica. O código da base usa outra convenção de intercepto no offset.

| Ensaio | E base (GPa) | E método (GPa) | Diferença E | Offset (MPa) | Situação da faixa |
|---|---:|---:|---:|---:|---|
| A500 t16 | 186,627 | 186,297 | 0,176% | 371,800 | Estimada |
| BCR295 t22 | 182,644 | 183,517 | 0,478% | 436,874 | Inconclusiva: envoltória ampla |
| A992 t12 web | 199,142 | 201,619 | 1,244% | 377,081 | Estimada, no limite de largura configurado |
| A992 t22 flange | 206,115 | 207,074 | 0,465% | 400,509 | Inconclusiva: envoltória ampla |
| BCP325 t22 | 217,491 | — | — | — | Sem família estável |
| HYP400 t27 | 230,253 | — | — | — | Sem família estável |

As diferenças de offset nos quatro resultados disponíveis são inferiores a 0,13%.
BCP325 tem 27 registros antes do teto da busca, abaixo de N mínimo=30. HYP400
tem 30, sem diversidade suficiente de intervalos aceitos para formar uma família.
São limitações do perfil/amostragem; não evidência de comportamento inadequado
desses materiais. Não reduzimos os requisitos apenas para aprovar esses ensaios.

No A500: referência [17,301), R²=0,961940, E=186,297 GPa. Faixa operacional
epsilon=0,0017–0,0020; envelope de tensão dos pontos correspondentes=316,4–327,5 MPa.
Offset=371,8 MPa em epsilon≈0,00395072. Não confundir essa faixa com o offset.

## Sensibilidade observada

- A500 manteve E ao variar R² mínimo entre 0,92/0,94/0,96; 0,97 não encontrou família.
- Nos quatro ensaios com referência, a estimativa E foi estável às variações
  testadas de tolerância da família (2/3/5%). Isso não valida todos os thresholds.
- Mudar o multiplicador do RMSE (1,5/2/2,5) altera a confirmação da faixa em
  BCR295 e A992 flange. A transição é menos robusta que E neste conjunto.
- Com suporte comum no A500, MM3/5/7 alteraram E em +3,10/+3,65/+3,85%.
  A redução do indicador de oscilação foi 67,4/79,5/85,5%; não é uma medição
  da redução de ruído instrumental.
- MM3 ficou compatível em todos os critérios exploratórios implementados no
  A500. MM5 e MM7 falharam na compatibilidade da faixa e das deformações.
  Não extrapolar essa conclusão para outro ensaio ou chamar MM3 de ótima universal.

O snapshot completo e os parâmetros estão em `VALIDACAO_DADOS_REAIS.json`.
Para reproduzir, executar o comando do README com a pasta Clean_Data local.

## Próximas limitações a investigar

Validar referência independente da transição, ampliar diversidade de ensaios e
densidades de amostragem, estudar convenções de coordenadas/offset e incerteza
instrumental. O método é uma evolução verificável do PFC, não uma certificação
de desempenho para todos os materiais próximos ao A500.
