# Projeto 04 — Classificação e escolha de um corte

## Pergunta

Neste estudo, investiguei se as medidas físico-químicas de um vinho tinto ajudam a identificar aqueles que receberam nota sensorial de qualidade igual ou superior a 7. Comparei duas formas de decidir: a regra padrão, que classifica como positivo um vinho cuja probabilidade calculada seja ≥ 0,50, e outro corte escolhido após conferir o desempenho do modelo em um conjunto de validação. Os dados de teste ficam separados e não são usados para ajustar o modelo nem para escolher o corte.

## Dados, fonte e licença

Usei somente o arquivo `winequality-red.csv`, obtido no pacote da ficha oficial **Wine Quality**, do UCI Machine Learning Repository [1]. A UCI descreve o conjunto como amostras de vinho verde tinto e branco do norte de Portugal, com qualidade avaliada por análise sensorial. O arquivo de vinho tinto tem 1.599 linhas, 11 medidas físico-químicas e a coluna `quality` (qualidade), conforme conferido pelo script. A ficha informa que o conjunto foi doado à UCI em `10/6/2009`, mas não indica quando cada amostra foi produzida ou coletada [1].

A licença informada pela UCI é **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Ela permite compartilhar e adaptar o conjunto, desde que seja dado o crédito apropriado [1]. O script baixa o arquivo ZIP diretamente da UCI. Os dados são guardados no cache local `data/cache/`, ignorado pelo Git, e não são incluídos neste projeto.

## O que fiz

Defini como positiva a categoria de vinhos com `quality >= 7`; as notas abaixo de 7 formam a categoria negativa. Esse corte em 7 é uma escolha deste exercício, não uma categoria oficial adicional do conjunto.

Como comparação simples (baseline), usei regressão logística, um modelo que calcula a probabilidade de cada uma das duas categorias. Antes do ajuste, o `StandardScaler` coloca as medidas em escalas comparáveis, usando suas médias e desvios. Reuni essas etapas em um `Pipeline`, isto é, uma sequência organizada de operações. O pipeline é ajustado apenas com os dados de treino, para que as médias e os desvios não sejam calculados com os dados de validação ou de teste.

Separei os dados em treino, validação e teste, mantendo proporções semelhantes das duas categorias nos três grupos: 60% para treino, 20% para validação e 20% para teste. Usei sementes fixas para controlar a separação. Na validação, conferi diferentes cortes e escolhi aquele que produziu o maior F1. O F1 resume o equilíbrio entre precisão — quantos dos casos apontados como positivos eram de fato positivos — e revocação — quantos dos positivos existentes foram encontrados. Em caso de empate, o código escolhe o corte mais alto. Consultei o teste somente depois de escolher o corte.

No teste, o script também calcula estas medidas:

- **Acurácia:** proporção de todas as previsões que acertaram.
- **Acurácia balanceada:** considera os acertos nas duas categorias, para que a categoria mais numerosa não domine a medida.
- **ROC-AUC:** área sob a curva ROC; resume quão bem o modelo ordena os casos positivos acima dos negativos ao considerar diferentes cortes.
- **Average precision** (área sob a curva precisão-revocação): resume como precisão e revocação se equilibram enquanto o corte muda.
- **Matriz de confusão:** tabela que mostra os acertos e erros em cada categoria.

ROC-AUC e average precision avaliam a ordem das probabilidades, por isso não mudam quando o corte muda. Os coeficientes apresentados são valores do modelo ajustado com medidas padronizadas. Eles indicam associações consideradas pelo modelo, não relações de causa e consequência.

## Dificuldade técnica observada

**Nível: intermediário.** A limitação observada nos dados é o desbalanceamento entre as categorias: somente 217 de 1.599 exemplos (13,57%) são positivos. No teste, a regra padrão teve 89,38% de acurácia, mas encontrou apenas 16 dos 43 positivos (revocação de 37,21%). Isso mostra que a acurácia, sozinha, não descreve bem o desempenho neste caso. Para comparar os cortes sem usar os dados de teste na escolha, o script mantém validação e teste separados.

## O que encontrei

Os resultados abaixo são os registrados ao executar `analysis.py` sobre o CSV baixado da UCI, com pandas 3.1.0 e scikit-learn 1.9.1:

- O arquivo contém 1.599 linhas, 11 medidas e nenhum valor ausente (nenhuma informação faltando). Há 217 casos positivos (13,57%). As separações ficaram com 959 linhas de treino, 320 de validação e 320 de teste; esses grupos têm, respectivamente, 130, 44 e 43 positivos.
- O corte que alcançou o maior F1 na validação foi **0,2919**, com F1 de validação **0,5743**.
- No teste, com o corte padrão **0,50**, a acurácia foi **0,8938** (proporção total de previsões certas); a precisão, **0,6957** (proporção dos apontados como positivos que eram positivos); a revocação, **0,3721** (proporção dos positivos encontrados); e o F1, **0,4848** (resumo do equilíbrio entre precisão e revocação). A acurácia balanceada foi **0,6734** (acertos considerando as duas categorias), a ROC-AUC foi **0,8786** (capacidade de ordenar positivos acima de negativos) e a average precision foi **0,5652** (resumo de precisão e revocação conforme o corte muda). A matriz de confusão foi TN=270, FP=7, FN=27, TP=16. Nessa tabela, TN são negativos identificados corretamente; FP, negativos apontados por engano como positivos; FN, positivos não encontrados; e TP, positivos identificados corretamente.
- No mesmo teste, usando o corte escolhido na validação (**0,2919**), a acurácia foi **0,8781**, a precisão **0,5435**, a revocação **0,5814**, o F1 **0,5618**, a acurácia balanceada **0,7528**, a ROC-AUC **0,8786** e a average precision **0,5652**. A matriz foi TN=256, FP=21, FN=18, TP=25.
- Nesta única separação dos dados, o corte escolhido na validação aumentou o F1 no teste em aproximadamente 0,077 e a revocação em aproximadamente 0,209, mas reduziu a precisão e a acurácia. Na prática, nesse teste foram encontrados mais positivos, ao custo de apontar mais casos negativos como positivos. Esse resultado vale para o grupo separado para teste e não garante o mesmo desempenho em novas amostras.
- Entre os coeficientes padronizados de maior valor absoluto no modelo ajustado estavam `alcohol` (+0,9466), `total sulfur dioxide` (-0,8135), `sulphates` (+0,6827), `chlorides` (-0,5153) e `volatile acidity` (-0,4324). São associações aprendidas nesta comparação simples, não recomendações nem provas de causa e consequência.

## O que aprendi

O que aprendi com a comparação é que 0,50 não é uma regra universal: o corte deve ser avaliado de acordo com a medida importante para a tarefa. A validação permite escolher o corte sem consultar o teste; manter o teste separado ajuda a estimar o desempenho após essa escolha. Também vi por que, quando as categorias aparecem em quantidades diferentes, é útil observar medidas voltadas à categoria positiva e a matriz de confusão, além da acurácia.

## Ponte para o próximo projeto

Para o próximo projeto, levo a separação entre treino, validação e teste, o pré-processamento dentro de um pipeline e a avaliação com dados que não foram usados no ajuste. A etapa seguinte, **05-regressao**, passa de prever uma categoria para prever um valor numérico. A diferença principal será escolher e interpretar medidas de erro para valores contínuos, em vez de usar um corte e medidas de classificação.

## Como reproduzir

É necessário Python 3.10 ou superior e acesso à internet na primeira execução. A partir desta pasta:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python analysis.py
```

Se o arquivo ainda não estiver no cache, o script baixa o ZIP público da UCI. As sementes fixas controlam as separações. A execução imprime as dependências, as versões observadas, o corte, as medidas e os coeficientes. Para baixar uma cópia nova, remova `data/cache/` antes de executar novamente.

## Limites e aviso educacional

A avaliação usa uma única separação aleatória dos dados; não usa validação cruzada nem um teste externo. As estimativas podem mudar com outras amostras ou separações. Como a busca pelo corte escolhe o que maximiza o F1 na validação, essa escolha pode se ajustar às particularidades daquela parte dos dados. A categoria positiva depende do corte escolhido (`quality >= 7`), e as notas vêm de uma avaliação sensorial, não de uma medida física objetiva de qualidade. A ficha da UCI observa que informações como marca, preço e tipo de uva não estão disponíveis [1]; por isso, as previsões se limitam às medidas fornecidas. A comparação simples, baseada em relações lineares, pode não captar relações não lineares ou interações entre medidas. Os resultados são estritamente educacionais: não medem impacto comercial, não demonstram causa e consequência e não devem ser usados para avaliar ou certificar vinhos reais.

## Referências

[1]: https://archive.ics.uci.edu/dataset/186/wine+quality "Wine Quality, UCI Machine Learning Repository"
