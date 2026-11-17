# Validação ampliada do backend — 11/10/2026

## Conclusão

O módulo e o escoamento por offset apresentam evidências favoráveis no conjunto
avaliado. A faixa atual **não foi validada como intervalo que contém o início da
não linearidade**: nos três casos sintéticos externos, o início nominal ficou
abaixo do limite inferior calculado. Ela representa afastamento detectável da
reta, condicionado aos limiares e à persistência. Não representa probabilidade,
limite elástico certificado ou tensão segura de projeto.

Isso é uma limitação localizada e explicável, não motivo para redesenhar todo o
programa. A conclusão é parcialmente satisfatória: conservar a extração de módulo
e offset; resolver a interpretação/estimação da transição antes de apresentá-la
como localização do término físico da linearidade. Linearidade, elasticidade e
escoamento convencional são conceitos distintos; uma curva de carregamento isolada
não comprova recuperação elástica por descarregamento.

## Protocolo congelado e fontes

Nenhum parâmetro, algoritmo de produção ou arquivo da interface foi alterado nesta
etapa. Também não foram alterados os dados originais ou o documento acadêmico.
Não houve ajuste de thresholds para melhorar os resultados dos novos casos.

Fonte independente: [NPL/TENSTAND](https://www.npl.co.uk/products-services/advanced-materials/tensile-testing),
arquivos 13 (S355 real), 57, 61 e 63 (sintéticos com ruído crescente).
O [relatório de avaliação](https://www.npl.co.uk/getattachment/135ef6b3-4683-4a22-9bcc-e611a47c7bdb/SW-validation-eval.pdf?lang=en-US),
seção 7.7 e tabela 9, fornece o modelo sintético e os valores de comparação.
Trata-se de benchmark histórico, não de comprovação de conformidade com normas atuais.
Para os sintéticos, a referência nominal é E = 207,5 GPa e término da reta em
350 MPa (deformação aproximadamente 0,00169).

O adaptador converte força em kN e extensão em mm para tensão de engenharia em MPa
e deformação de engenharia, usando área e comprimento do cabeçalho. Os dados
locais Zenodo usam coordenadas verdadeiras, preservadas. Não se misturam referências
de coordenadas diferentes. A comparação não estima incerteza metrológica.

## Resultados externos

| Caso NPL | E calculado (GPa) | Offset calculado (MPa) | Avaliação |
|---|---:|---:|---|
| 13, S355 real | 227,099 | 438,755 | E dentro do intervalo 221–228,8; faixa inconclusiva |
| 57, sem ruído | 207,500 | 434,273 | Offset próximo da referência 434,3 |
| 61, ruído 0,5% | 208,740 | 441,249 | Offset dentro de 438,1–441,6 |
| 63, ruído 1% | 207,949 | 448,421 | Offset 0,221 MPa acima do intervalo 446,5–448,2 |

No S355 não há referência de offset adotada nesta comparação: ReH e ReL não são
substitutos de Rp0,2. Nos sintéticos, o erro de E em relação ao modelo nominal não
ultrapassou 0,60%. O caso 63 é próximo da referência, mas não pertence ao intervalo
publicado; não foi declarado aprovado nesse critério mais estrito.

| Caso | Faixa calculada de deformação | Contém início nominal ~0,00169? |
|---|---|---|
| 57 | 0,00175274–0,00204074 | Não |
| 61 | 0,00180874–0,00220874 | Não |
| 63 | 0,00186474–0,00232074 | Não |

O atraso já existe sem ruído. O algoritmo tolera resíduos pequenos e aguarda dois
blocos afastados; portanto, um bloco ainda tolerado pode já pertencer ao trecho
curvo. Usar seu final como limite inferior não garante conter o início da curva.
Somar candidatas não elimina esse viés comum. O status interno `estimado` descreve
o atendimento às regras do algoritmo, não a aprovação na referência externa.

## Densidade de amostragem

Foram preservados os índices 0, k, 2k… para k = 1, 2, 4 e 8, sem interpolação,
sem média prévia e sem acrescentar pontos. É um teste de sensibilidade à remoção
de pontos, não a simulação completa de outra aquisição (não há filtro antialias).
Uma única fase de amostragem foi usada; não representa todas as fases possíveis.

| Série | E completo | E com metade | E com 1/4 | E com 1/8 (GPa) |
|---|---:|---:|---:|---:|
| A500 | 186,297 | 187,087 | 184,288 | 188,608 |
| A992 web | 201,619 | 198,496 | 196,908 | 194,872 |
| NPL 57 | 207,500 | 207,500 | 207,500 | Inconclusivo |
| NPL 61 | 208,740 | 209,719 | 208,878 | Inconclusivo |
| NPL 63 | 207,949 | 209,439 | 206,689 | Inconclusivo |

Maior variação relativa ao módulo da série completa: A500 1,24%; A992 3,35%.
Esses números medem estabilidade, não exatidão contra referência independente.
As séries NPL reduzidas a 1/8 têm apenas 21 pontos na busca inicial, abaixo dos
30 exigidos. A faixa é menos robusta: A500 a 1/8 e A992 nas três reduções retornam
resultados parciais. Não reduzir o mínimo de pontos apenas para obter uma resposta.

Cinco curvas adicionais da base [Zenodo](https://zenodo.org/records/6965147),
S355J2 (IPE200, HEA160, HEM320 alma e mesa) e S235/275, têm entre 20 e 35 pontos
totais e somente 6–14 na busca inicial. Todas ficaram inconclusivas. Foram lidas
pelas colunas nomeadas `Sigma_true` e `e_true`, pois as primeiras colunas desses
arquivos não são tensão/deformação. Isso amplia a investigação, mas **não valida
desempenho nesses materiais**. Seriam necessários registros mais densos.

## Escopo simples e defensável

É possível explicar o método em quatro passos:

1. Procurar trechos iniciais suficientemente longos e aproximadamente retos.
2. Escolher um ajuste cujo módulo pouco muda ao deslocar as extremidades.
3. Calcular offset separadamente e procurar afastamento persistente da reta.
4. Comparar médias móveis com o original e informar quais propriedades mudaram.

Não são necessários rede neural, novos modelos de material ou mais dezenas de
parâmetros. Esta investigação não estabelece uma média móvel universal nem
revalida todas as janelas em novos materiais; mantém a avaliação por curva e por
finalidade já existente. Preservar E não basta para aprovar a faixa de transição.

Antes da etapa visual, a pendência central é pequena em escopo, mas necessária:
ou apresentar explicitamente a faixa como zona de afastamento detectável, ou
revisar seu limite inferior e verificar novamente o início nominal externo,
incluindo os casos com ruído e baixa densidade. Não basta ampliar arbitrariamente
a faixa para incluir o valor esperado. A segunda opção exige nova validação;
nenhuma correção numérica foi feita silenciosamente nesta investigação.

## Reprodução e entregas

```powershell
Set-Location 'D:\Documentos\PFC\Código\PFC'
python -B scripts/investigar_validacao.py --base 'D:\Documentos\PFC\Dados experimentais\Clean_Data_v1-0-0\Clean_Data'
python -B -m unittest discover -s tests -q
```

O script baixa o ZIP NPL em memória e emite JSON; requer conexão e a base local.
[VALIDACAO_AMPLIADA.json](VALIDACAO_AMPLIADA.json) registra parâmetros, hashes,
resultados de nove casos adicionais e vinte combinações de série/densidade.
As quatro densidades incluem a série completa e não são vinte ensaios independentes.
Os resultados anteriores permanecem em VALIDACAO_DADOS_REAIS.json.

Alterações desta etapa: roteiro de investigação, resultado JSON, este relatório
e link no README. Nenhuma mudança no backend de produção, frontend ou dependências.

Verificação executada: 44 testes, 43 aprovados e um ignorado por ausência de SciPy.
O JSON foi conferido contra os parâmetros de produção. Testes de software
aprovados não anulam a falha de cobertura encontrada na referência de transição.
