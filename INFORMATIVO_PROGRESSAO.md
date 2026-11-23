# Como avancei entre os projetos

Executei os dez scripts com dados reais, sem simulações, e não há projeto bloqueado entre os resultados recebidos. Ao longo da trilha, usei métricas — números que resumem resultados — para comparar métodos. Cada etapa me ensinou uma prática útil para a seguinte, mas os resultados observados não provam que as mesmas conclusões valem para outros dados.

## 01 → 02 — Da conferência dos dados às contagens

Comecei examinando o conjunto Adult. Conferi 48.842 registros e encontrei 52 linhas exatamente repetidas e 6.465 células sem informação, principalmente nos campos `workclass`, `occupation` e `native-country`. O rótulo `>50K` apareceu em 23,93% dos registros. Por código de escolaridade, a proporção foi de 5,71% nos códigos 1–8 e de 48,06% nos códigos 13–16 [1].

Para ler os arquivos `adult.data` e `adult.test`, precisei levar em conta que um começa com um comentário, que os rótulos do outro têm pontuação no final e que `?` indica informação ausente. Calculei as proporções por registro, sem ponderação. A diferença observada entre escolaridade e rótulo é uma associação: não prova que uma coisa causou a outra nem permite prever o resultado de uma pessoa.

Essa conferência me ensinou a verificar os campos, as ausências, as repetições e o total usado em cada cálculo. Na etapa seguinte, levei esse cuidado para contagens e proporções feitas com consultas a um banco de dados.

## 02 → 03 — Das taxas à comparação com incerteza

No conjunto de sessões de compras, contei 1.908 compras em 12.330 sessões, uma taxa de 15,4745%. A taxa foi de 24,9115% para visitantes novos e de 13,9323% para visitantes recorrentes. Em fevereiro, foram 3 compras em 184 sessões; em novembro, 760 em 2.998 sessões [2]. Neste caso, taxa de conversão é a parte das sessões que terminou em compra.

O download do conjunto Online Retail falhou por tempo esgotado, então usei o conjunto oficial sobre intenção de compra por sessão. Os dados representam sessões, não transações; não há identificadores repetidos que permitam medir quantas pessoas voltaram ou acompanhar grupos ao longo do tempo. `Revenue` indica que houve uma compra, não quanto foi gasto.

Aprendi a mostrar as taxas junto com as contagens e a não tentar responder perguntas que os dados não permitem. Na etapa seguinte, comparei diferenças entre grupos e sua incerteza, sem tratar os resultados anteriores como prova de causa.

## 03 → 04 — Da comparação de grupos à previsão de classes

No conjunto ToothGrowth, examinei 60 observações: três doses de vitamina C, dois suplementos e dez observações em cada combinação [3].

Comparei os suplementos de suco de laranja (OJ) e ácido ascórbico (VC). A diferença média OJ menos VC foi 5,250 na dose de 0,5 mg/dia e 5,930 na dose de 1 mg/dia. Os valores-p, ajustados pelo método de Holm, foram 0,012717 e 0,003115. Na dose de 2 mg/dia, a diferença foi −0,080 e o valor-p ajustado foi 0,963852. Um valor-p ajuda a avaliar o quanto os dados combinam com a hipótese de não haver diferença; o ajuste de Holm considera que fiz várias comparações.

A fonte trazia código da linguagem de programação R, não um arquivo CSV (dados organizados em colunas) pronto. Precisei manter os valores alinhados e traduzir os códigos dos suplementos para seus nomes. A documentação não descreve detalhes suficientes do protocolo para eu afirmar que os suplementos causaram as diferenças ou que o resultado vale para outros casos.

Essa análise me ensinou a definir os grupos e explicar os limites da comparação. Em seguida, passei a prever classes: separei dados para aprendizado, ajuste e teste, em vez de tentar explicar causas.

## 04 → 05 — Das classes aos erros de previsão numérica

No conjunto Wine Quality, a classe de qualidade `quality >= 7` incluía 217 de 1.599 amostras, ou 13,57% [4]. Separei os dados em 959 para treino, 320 para validação e 320 para teste. Usei a validação para escolher ajustes e mantive o teste separado para conferir o resultado final. A divisão preservou proporções parecidas entre as classes.

Escolhi 0,2919 como corte para marcar uma previsão como positiva. No teste, o F1 foi 0,5618 e a revocação foi 0,5814; com o corte padrão de 0,50, os valores foram 0,4848 e 0,3721. F1 combina a proporção de alertas positivos que estavam corretos com a proporção dos casos positivos encontrados. Revocação é a parte dos casos positivos reais que o modelo encontrou. A classe menos comum foi um desafio: com o corte padrão, o modelo encontrou só 16 dos 43 casos positivos do teste, apesar da acurácia — a parte de todas as previsões que estava correta.

Aprendi a escolher o corte usando a validação, guardar o teste para a conferência final e não confiar só na acurácia. Também organizei o preparo dos dados junto com o modelo para evitar misturas indevidas. No projeto seguinte, passei a prever valores numéricos e medir o tamanho dos erros.

## 05 → 06 — Da divisão treino/teste à ordem do tempo

O conjunto Concrete Compressive Strength tem 1.030 observações, oito dados de entrada e um valor a prever: a resistência em MPa [5]. Na divisão aleatória por grupos, usei 826 observações para treino e 204 para teste. A Random Forest (um modelo que combina árvores de decisão) teve MAE de 3,441 MPa, RMSE de 4,662 e R² de 0,906. Como comparação simples, a média teve MAE de 12,375 e RMSE de 15,241. MAE resume o tamanho médio dos erros; RMSE também mede o erro, mas dá mais peso aos erros grandes; R² resume o quanto as previsões acompanham as variações dos valores observados.

A importância por permutação — embaralhar um dado de entrada e observar a mudança no desempenho — foi maior para idade e cimento. Isso não mostra que essas variáveis causam a resistência. O arquivo antigo de planilha exigiu um leitor próprio; havia combinações de entradas repetidas, e mantive grupos iguais juntos ao dividir os dados.

Aprendi a comparar o modelo com uma regra simples, examinar as diferenças entre valores previstos e observados e considerar que dados relacionados podem afetar a importância das variáveis. Na etapa seguinte, mantive dados de teste, mas respeitei a ordem do tempo e usei apenas o passado.

## 06 → 07 — Da previsão no tempo aos grupos sem rótulos

A série mensal de CO₂ de Mauna Loa, da NOAA, ia de janeiro de 1974 a dezembro de 2025 e tinha 624 linhas. Depois de retirar 12 marcadores de ausência, a parte recente sem interrupções ia de julho de 2023 a dezembro de 2025 [6]. Em um teste mês a mês, de julho de 2024 a dezembro de 2025, a regra de usar o último mês teve MAE de 1,2489 ppm e RMSE de 1,3776 ppm. Esses erros foram menores que os da regra de usar o mesmo mês do ano anterior: 3,0433 e 3,0968 ppm. Ppm significa partes por milhão.

O cabeçalho estava na linha 158 e havia intervalos sem dados. Por isso, separei os trechos em vez de preencher as lacunas. Aprendi a respeitar a ordem do tempo e a não inventar valores ausentes. Na etapa seguinte, deixei de prever o próximo valor e procurei grupos em dados sem respostas conhecidas; as medidas de qualidade desses grupos não equivalem a um teste de previsão.

## 07 → 08 — Dos números aos textos

O conjunto Wholesale customers tem 440 linhas [7]. Conferi oito colunas e formei grupos usando seis valores numéricos de gastos; deixei de fora `Channel` e `Region`. Como os gastos se concentravam em uma faixa, mas alguns eram muito altos, apliquei uma transformação para reduzir essa diferença antes de colocar as medidas em escalas comparáveis.

Comparei divisões em dois a oito grupos. A medida silhouette — um resumo de quão unidos e separados parecem os grupos — foi maior com dois grupos: 0,2903. A medida Calinski–Harabasz, que também avalia a separação entre grupos, favoreceu dois. Davies–Bouldin compara o quanto os grupos se distinguem, e seu valor foi ligeiramente menor com três. Nas dez execuções com dois grupos, o ARI entre pares foi 1,0000; essa medida compara se execuções diferentes formaram os mesmos grupos. Mesmo assim, a separação observada foi moderada e não havia rótulos de referência para confirmar os grupos. As medidas podem discordar, e a estabilidade não substitui uma conferência externa.

Essa etapa me mostrou que a forma de representar e medir os dados muda os grupos encontrados. Na seguinte, também transformei dados em números, mas usei palavras de avaliações para classificá-las.

## 08 → 09 — Das avaliações às interações com filmes

A documentação do conjunto RePro descreve 10.000 avaliações; o arquivo CSV que usei tinha 10.003 registros e 22 colunas [8]. Retirei 2.018 rótulos mistos, 409 neutros e uma cópia exatamente repetida. Restaram 7.575 textos únicos para uma classificação em duas categorias.

Separei os dados de forma estratificada: 80% para treino e 20% para teste, mantendo proporções parecidas entre as categorias. A representação TF-IDF (números que dão peso às palavras conforme ajudam a distinguir textos) usou palavras individuais e pares de palavras. A regressão logística classificou os textos com acurácia de 95,31% e F1 macro de 0,9529. O F1 macro do comparador que sempre escolhe a categoria mais frequente foi 0,3526. F1 macro calcula o F1 de cada categoria e dá o mesmo peso a todas.

A diferença entre os 10.000 descritos e os 10.003 do arquivo, a filtragem dos rótulos e as declarações divergentes sobre a licença exigiram cautela. Aprendi o vocabulário apenas com os dados de treino para evitar que o teste influenciasse o modelo. A contagem de palavras não entende plenamente negação, ironia ou contexto longo.

Aprendi a definir o que quero prever e a separar treino e teste. Na etapa seguinte, troquei os textos por avaliações de filmes e interações entre usuários e itens. Qualquer uso de texto como sinal auxiliar exigiria dados e avaliação próprios.

## 09 → 10 — Da recomendação offline ao acompanhamento dos dados

O MovieLens latest-small contém 100.836 avaliações de 610 usuários, de 29/03/1996 a 24/09/2018 [9]. No teste temporal, usei 9.542 interações positivas de 590 usuários elegíveis. A recomendação de filmes parecidos pelo padrão de notas teve Recall@10 de 0,085584 e NDCG@10 de 0,111605, acima da lista por popularidade, que teve 0,049885 e 0,079733.

Recall@10 resume quantos itens relevantes aparecem entre os dez primeiros; NDCG@10 também considera a posição e dá mais valor a itens relevantes que aparecem mais acima. Os resultados são médias em que cada usuário conta igualmente. O arquivo da fonte não vinha em ordem de tempo: ordenei as avaliações de cada usuário e mantive avaliações com horários iguais no mesmo lado da divisão. Esse teste usa dados históricos; não demonstra satisfação nem impacto comercial. A fonte restringe o uso comercial sem autorização.

Aprendi a definir o que conta como positivo, retirar da lista os filmes já vistos e comparar as recomendações com uma regra simples. Na última etapa, ampliei os cuidados com dados e testes para observar mudanças nas informações. Isso não significa que o modelo esteja funcionando continuamente.

## 10 — Consolidação: modelo e acompanhamento offline

O arquivo horário de aluguel de bicicletas tem 17.379 registros de 2011 a 2012 [10]. Na divisão por tempo, usei 13.903 linhas para treino e 3.476 para teste. A Random Forest teve MAE de 57,08, RMSE de 85,34 e R² de 0,8502. A comparação simples pela mediana teve MAE de 182,88, RMSE de 250,43 e R² de −0,2901.

Quatro testes automatizados passaram. As colunas obrigatórias não tinham informações ausentes e não havia IDs repetidos. O acompanhamento sinalizou 3 de 12 variáveis categóricas (campos com grupos ou rótulos); nenhuma variável numérica passou de PSI 0,20. PSI é uma medida que compara a distribuição dos dados entre dois grupos. Um aviso de mudança nos dados não prova que o modelo piorou por causa dessa mudança.

Um tempo esgotado no primeiro download me levou a ampliar o prazo e usar uma cópia local. A relação `cnt = casual + registered` revelaria partes da resposta; por isso, retirei esses componentes para evitar que o modelo recebesse a própria resposta. Previsão e mudança na distribuição respondem a perguntas diferentes. Fiz apenas uma avaliação histórica, sem entrada contínua de dados nem respostas reais de uso. Portanto, demonstrei acompanhamento offline, não operação em produção.

## Referências dos datasets

1. UCI Machine Learning Repository, **Adult**: https://archive.ics.uci.edu/dataset/2/adult
2. UCI Machine Learning Repository, **Online Shoppers Purchasing Intention Dataset**: https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset
3. R Documentation, **ToothGrowth**: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/ToothGrowth.html
4. UCI Machine Learning Repository, **Wine Quality**: https://archive.ics.uci.edu/dataset/186/wine+quality
5. UCI Machine Learning Repository, **Concrete Compressive Strength**: https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength
6. NOAA Global Monitoring Laboratory, **Carbon Dioxide monthly averages — Mauna Loa**: https://gml.noaa.gov/data/dataset.php?item=mlo-co2-observatory-monthly
7. UCI Machine Learning Repository, **Wholesale customers**: https://archive.ics.uci.edu/dataset/292/wholesale+customers
8. Hugging Face Datasets, **RePro — REview of PROducts**: https://huggingface.co/datasets/lucasnil/repro
9. GroupLens Research, **MovieLens latest-small**: https://grouplens.org/datasets/movielens/latest/
10. UCI Machine Learning Repository, **Bike Sharing Dataset**: https://archive.ics.uci.edu/ml/datasets/bike+sharing+dataset
