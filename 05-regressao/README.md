# 05 — Prever valores numéricos: resistência do concreto

## Pergunta

Neste estudo, analisei se oito medidas da composição e da idade de amostras de concreto ajudam a prever sua resistência à compressão, expressa em MPa (megapascal, uma unidade de pressão). Comparei dois métodos de previsão — regressão linear, que ajusta uma linha aos dados, e Random Forest, que combina várias árvores de decisão — com uma referência simples: prever sempre a resistência média observada nos dados usados para aprender. Também examinei os erros das previsões.

O objetivo é aprender sobre previsões, não medir impacto nos negócios. Uma relação entre medidas também não demonstra que uma delas cause outra coisa.

## Dados, origem, licença e período

Usei o conjunto **Concrete Compressive Strength**, disponibilizado no UCI Machine Learning Repository (UCI). A ficha o classifica como um problema de regressão, isto é, de previsão de valores numéricos. Ela informa 1.030 observações (registros), oito medidas numéricas de entrada e uma medida numérica de saída, sem informações ausentes. O valor previsto é a resistência à compressão, em MPa; a idade do concreto é informada em dias. A ficha registra a doação do conjunto à UCI em 2 de agosto de 2007, mas não informa em que período do calendário as observações foram coletadas. [1]

O arquivo oficial é `Concrete_Data.xls` e pode ser baixado diretamente, sem login. Nesta execução, ele tinha 124.928 bytes. O código baixa o arquivo quando necessário e o guarda em `data/`. O arquivo e os demais dados não são incluídos no Git, sistema usado para guardar o código do projeto. [1] [2]

A licença informada pela UCI é **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Em termos simples, ela permite compartilhar e adaptar o material, inclusive para uso comercial, desde que a fonte seja indicada e a licença seja vinculada. A atribuição usada neste projeto é I-Cheng Yeh (1998), *Concrete Compressive Strength*, UCI Machine Learning Repository, DOI [10.24432/C5PK67](https://doi.org/10.24432/C5PK67). [1] [3]

## O que fiz

O script verifica se o arquivo está no formato XLS esperado, se contém as nove colunas e a quantidade esperada de linhas, se não há informações ausentes e se todos os valores são finitos (sem valores infinitos). Os três modelos usam as mesmas oito medidas. Não foram preenchidas informações ausentes, alterada a escala das medidas, escolhidas variáveis ou testadas configurações para tentar melhorar os modelos.

Separei os dados com `GroupShuffleSplit`, usando `test_size=0.20` e `random_state=42`. Os dados de treino são usados para o modelo aprender; os de teste ficam separados para conferir seu desempenho. Defini os grupos por cada combinação exata das oito medidas de entrada, para que a mesma receita e idade não aparecessem tanto no treino quanto no teste. O teste ficou com 204 observações e 200 grupos; o treino, com 826 observações e 796 grupos. Como a separação é feita por grupos, a parcela de observações no teste não é necessariamente exatamente 20%. O valor `42` ajuda a repetir a mesma divisão e os mesmos sorteios aleatórios.

Comparei três alternativas: a referência simples, que prevê a média do valor a prever calculada apenas com os dados de treino; a regressão linear; e uma Random Forest com 500 árvores, `min_samples_leaf=2` (no mínimo duas observações em cada resultado final de uma árvore) e semente aleatória 42.

Conferi o desempenho uma única vez nos dados de teste, usando três medidas:

- **MAE**, ou erro absoluto médio: indica, em média, a distância entre as previsões e os valores reais, em MPa. Um MAE de 3 MPa, por exemplo, significa uma diferença média de 3 MPa.
- **RMSE**, ou raiz do erro quadrático médio: também resume a distância entre previsão e valor real, mas dá mais peso aos erros grandes.
- **R²**: indica quanto as previsões acompanham as diferenças entre os valores reais. Um valor mais alto indica melhor desempenho nessa medida; um valor negativo indica desempenho abaixo da referência baseada na média dos valores reais do teste.

Também examinei os resíduos da Random Forest — a diferença entre o valor real e o previsto. Para estimar a importância por permutação, embaralhei cada medida nos dados de teste e observei quanto o MAE aumentava, repetindo o procedimento 20 vezes. Isso descreve o comportamento das previsões, mas não mede causa e efeito.

## Dificuldade técnica observada

**Nível: intermediário.** O arquivo da fonte usa XLS, um formato antigo de planilha. Na primeira tentativa de leitura, o ambiente não tinha `xlrd`, uma ferramenta para ler esse formato. Depois de instalá-la, o pandas (biblioteca do Python para trabalhar com tabelas) mostrou um aviso de descontinuação, ou seja, de que o uso do mecanismo `xlrd` está sendo retirado aos poucos. Testei `python-calamine`, que conseguiu ler o arquivo oficial com as colunas esperadas. Por isso, o projeto indica explicitamente esse mecanismo para que a leitura possa ser reproduzida.

Encontrei ainda 34 combinações de entrada repetidas além da primeira ocorrência e 25 linhas completas repetidas. Uma separação aleatória por linha poderia colocar a mesma combinação de medidas nos dois grupos e fazer a avaliação parecer melhor para receitas que o modelo já encontrou no treino. Para evitar essa sobreposição, separei os dados de teste por receita e idade. A execução confirmou que não houve grupos em comum entre treino e teste.

## O que encontrei

Os resultados abaixo vieram de uma execução de `python3 analysis.py` com o arquivo baixado da UCI e a divisão descrita acima:

- **Referência simples pela média:** MAE = **12,375 MPa**, RMSE = **15,241 MPa**, R² = **−0,005**.
- **Regressão linear:** MAE = **8,472 MPa**, RMSE = **10,646 MPa**, R² = **0,510**.
- **Random Forest:** MAE = **3,441 MPa**, RMSE = **4,662 MPa**, R² = **0,906**.

Neste teste, o erro absoluto médio da Random Forest foi 8,934 MPa menor que o da referência simples e 5,031 MPa menor que o da regressão linear. O R² da referência simples ficou um pouco abaixo de zero nesta divisão por grupos. Isso significa que, neste teste, prever sempre a média calculada no treino foi um pouco pior do que usar como referência a média dos próprios valores reais do teste.

Na Random Forest, a média dos resíduos foi **−0,164 MPa**, a mediana (o valor central quando os erros são ordenados) foi **−0,290 MPa** e o desvio-padrão (medida de quanto os erros se espalham em torno da média) foi **4,670 MPa**. Os quantis de 5% e 95% — valores que delimitam as partes mais baixas e mais altas dos erros — foram **−7,789 MPa** e **6,724 MPa**. **44,6%** dos resíduos foram positivos; nesses casos, o modelo previu uma resistência abaixo da real. A correlação de Pearson entre o valor previsto e o resíduo foi **0,213**. Esse resultado indica uma associação positiva entre os dois valores: os erros variaram conforme o nível previsto. Sozinho, porém, não é um teste formal para verificar se a variação dos erros muda com o nível previsto (heterocedasticidade).

Na análise de importância por permutação da Random Forest, estes foram os maiores aumentos médios no MAE quando cada medida foi embaralhada nos dados de teste:

- idade do concreto: **8,683 ± 0,485 MPa**;
- cimento: **6,514 ± 0,538 MPa**;
- escória de alto-forno: **2,780 ± 0,285 MPa**;
- água: **2,081 ± 0,295 MPa**;
- superplastificante: **1,336 ± 0,173 MPa**.

Em cada item, o valor depois do sinal ± indica quanto o aumento do MAE variou entre as repetições. Os resultados dependem deste modelo e deste teste. Como algumas medidas podem estar relacionadas entre si, essa ordem não prova causa nem representa a contribuição independente de cada medida.

## O que aprendi

Aprendi que o desempenho nos dados usados para ensinar o modelo não substitui a conferência em dados separados. A referência simples ajuda a colocar os resultados em perspectiva e mostra que o ganho depende de como os dados são separados. Aqui, o teste usou combinações de medidas ausentes do treino, em vez de uma seleção aleatória de linhas que poderia repetir receitas nos dois grupos.

Os erros complementam MAE, RMSE e R². Uma média de erros perto de zero não elimina erros individuais de vários MPa. A relação observada entre o valor previsto e o erro é um motivo para fazer outras verificações antes de considerar o modelo bem ajustado. A importância por permutação ajuda a descrever as previsões, mas não demonstra que mudar uma medida causará uma mudança na resistência.

## Ponte para o próximo projeto

Para o próximo projeto, levo essa prática de definir uma referência simples, separar dados para conferir o resultado e examinar os erros. No **06-series-temporais**, a previsão será aplicada a dados organizados no tempo. Em séries temporais, uma divisão aleatória pode deixar informações do futuro chegarem ao treino. O próximo passo é separar os dados pela ordem do tempo e comparar as previsões com métodos simples que também respeitem essa ordem. Também serão conferidos padrões de autocorrelação (quando os valores ou erros se parecem com valores anteriores) e os erros ao longo do tempo.

## Como reproduzir

É necessário ter Python 3.10 ou superior e acesso à internet na primeira execução. Na pasta do projeto, rode:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python analysis.py
```

O primeiro comando cria um ambiente virtual, um espaço separado para instalar as ferramentas Python do projeto. No Windows, use o caminho indicado no comentário do segundo comando para ativá-lo. Se não houver uma cópia local, o script baixa o XLS oficial para `data/` e usa esse arquivo nas próximas execuções. A pasta está no `.gitignore`, que informa ao Git quais arquivos não deve incluir. Com o mesmo arquivo e versões compatíveis das bibliotecas, `random_state=42` reproduz a divisão e os sorteios dos estimadores (modelos que usam sorteios). Pequenas diferenças nos números podem ocorrer entre versões das dependências, isto é, das bibliotecas necessárias ao projeto.

## Limites

Os resultados vêm de uma única divisão de teste de um conjunto de dados pequeno e histórico, com observações separadas pelas combinações das medidas de entrada. Portanto, não são uma estimativa de desempenho válida para todos os casos. Não houve validação cruzada (repetição da conferência com diferentes divisões dos dados), cálculo de uma faixa de incerteza ou teste com outra fonte de dados. A comparação também não incluiu ajuste das configurações dos modelos.

Resumi os erros com números, sem gráfico Q-Q (que compara os erros com um padrão de referência), análise por grupos de observações ou teste formal para verificar se a variação dos erros se mantém constante. A importância por permutação usa o mesmo conjunto de teste das outras medidas de desempenho e pode variar bastante quando as medidas de entrada são relacionadas entre si. O conjunto também não informa o período do calendário em que as observações foram coletadas. Esta análise é educativa e não deve ser usada como orientação para engenharia estrutural, projeto de mistura ou controle de qualidade.

## Referências

[1]: https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength "Concrete Compressive Strength, UCI Machine Learning Repository"
[2]: https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Data.xls "Arquivo Concrete_Data.xls, UCI Machine Learning Repository"
[3]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
