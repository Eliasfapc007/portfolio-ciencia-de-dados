# 10 — Entrega e acompanhamento do modelo

## Pergunta

Neste estudo, analisei se um modelo treinado no trecho inicial do histórico consegue estimar quantas bicicletas foram alugadas por hora no trecho final. Também conferi a qualidade dos dados e se os padrões de calendário e clima mudaram entre esses períodos. A análise é feita sobre dados históricos, não em uma operação ao vivo.

## Dados, fonte e licença

Usei o arquivo `hour.csv` do conjunto **Bike Sharing**, publicado no UCI Machine Learning Repository. A página da fonte descreve contagens por hora e por dia do Capital Bikeshare entre 2011 e 2012. Ela lista 17,389 observações e informa que o conjunto não tem informações ausentes. Já o arquivo de contagens por hora lido nesta execução tem 17.379 linhas, de 2011-01-01 00:00 a 2012-12-31 23:00 [1]. Mantive as duas contagens como aparecem nas fontes: uma é a listagem da página e a outra, o arquivo efetivamente lido.

A licença informada na página é **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Ela permite compartilhar e adaptar o material, inclusive para qualquer finalidade, desde que eu dê o crédito adequado, inclua o link da licença e indique as alterações. O crédito não deve sugerir que a fonte apoia o uso [1] [2]. A fonte recomenda citar Hadi Fanaee-T (2013), *Bike Sharing*, UCI Machine Learning Repository, DOI `10.24432/C5W894` [1].

Os dados originais não estão incluídos no projeto. Na primeira execução, o `analysis.py` baixa o arquivo ZIP oficial e guarda uma cópia em `data/`. O Git, ferramenta usada para acompanhar mudanças nos arquivos do projeto, ignora essa pasta.

## O que fiz e como conferi

O programa verifica se há todas as colunas necessárias, informações ausentes e números finitos — isto é, números válidos, sem valores infinitos. Também confere IDs (códigos de identificação) repetidos, horários duplicados, valores de calendário e clima fora das faixas permitidas e se `cnt = casual + registered`. Por fim, organiza os registros por data e hora.

O modelo prevê `cnt`, a contagem total de bicicletas alugadas. `casual` (aluguel casual) e `registered` (aluguel registrado) são partes dessa contagem; por isso, não entram como informações para prever o total, pois já revelariam partes da resposta. Também deixei de fora `instant` (número do registro) e `dteday` (data). O modelo recebe informações de calendário e clima: `season` (estação), `yr` (ano), `mnth` (mês), `hr` (hora), `holiday` (feriado), `weekday` (dia da semana), `workingday` (dia útil), `weathersit` (condição do tempo), `temp` (temperatura), `atemp` (temperatura percebida), `hum` (umidade) e `windspeed` (velocidade do vento).

Para que o modelo use as informações por categoria, o fluxo as transforma em colunas com valores 0 ou 1. Também inclui recursos para preencher informações ausentes caso seja usado com outros dados, embora nesta execução os dados observados não tivessem valores ausentes.

Mantive a ordem do tempo: os primeiros 80% dos registros servem para ensinar o modelo e os 20% finais ficam reservados para o teste. O `RandomForestRegressor` (modelo de floresta aleatória para prever números) combina 120 árvores de decisão, ou conjuntos de regras que produzem previsões. Configurei `min_samples_leaf=2` (ao menos 2 exemplos em cada ponta das regras), `max_features=0.8` (considera 0,8 das informações disponíveis em cada escolha) e `random_state=42` (valor que ajuda a repetir as escolhas aleatórias).

Comparei o resultado com o `DummyRegressor`, um modelo simples que prevê a mediana do período de treino. Mediana é o valor central quando os números são ordenados. Usei três medidas: o erro absoluto médio (MAE) indica o erro médio em bicicletas por hora; a raiz do erro quadrático médio (RMSE) também mede o erro em bicicletas por hora, mas dá mais peso aos erros grandes; e o R² é uma nota de ajuste. Para R², valores mais próximos de 1 indicam previsões que acompanham melhor os dados; um valor abaixo de 0 indica resultado pior do que usar a média das contagens como previsão.

Como verificação offline — feita fora de uma operação real — comparei os padrões dos dados de teste com os do treino. Para informações numéricas, calculei o índice de estabilidade populacional (PSI), uma medida de quanto a distribuição dos valores mudou. O cálculo usa dez faixas definidas pelos quantis do treino, pontos que separam os valores em grupos; o alerta é acionado quando PSI > 0,20. Para informações por categoria, usei a variação total (TV), uma medida da diferença entre a frequência de cada categoria nos dois períodos; o alerta é acionado quando TV > 0,10. Esses limites são regras simples para este exercício, não foram ajustados para uma operação real.

O programa também executa quatro testes automatizados: eles conferem o formato e a integridade dos dados, se as informações que poderiam revelar a resposta foram excluídas, se a separação preserva a ordem do tempo e se as medidas de mudança dão zero quando comparam o período de referência com ele mesmo. Os testes usam dados reais baixados, sem criar linhas de teste. O relatório registra uma execução real com o conjunto indicado.

## Dificuldade técnica observada

Na primeira tentativa, o download com `urllib` atingiu o limite de 60 segundos. O mesmo arquivo do endereço oficial foi obtido com `curl`, usando um prazo maior. O fluxo passou a esperar até 180 segundos e a guardar uma cópia local para reutilização. Na execução final, a cópia local estava limpa, e o próprio `analysis.py` concluiu o download e o processamento.

## O que encontrei

Os resultados abaixo vieram da execução do programa sobre `hour.csv`:

- O arquivo tem **17.379 linhas**, de 2011-01-01 a 2012-12-31. Usei **13.903** linhas para ensinar o modelo e reservei **3.476** para o teste. O período de treino termina em 2012-08-07 11:00, e o de teste começa em 2012-08-07 12:00.
- As quatro conferências automatizadas passaram. Foram encontradas **0 informações ausentes** nas colunas necessárias e **0 IDs repetidos**. Em todas as linhas, `cnt = casual + registered`.
- No teste, o `RandomForestRegressor` teve **MAE 57,08**, **RMSE 85,34** e **R² 0,8502**. Em termos práticos, o erro médio foi de 57,08 bicicletas por hora; o RMSE, que dá mais peso aos erros grandes, foi de 85,34 bicicletas por hora. A nota R² foi 0,8502. Como comparação, o modelo simples que prevê a mediana teve **MAE 182,88**, **RMSE 250,43** e **R² -0,2901**. Esses valores se referem somente à divisão dos dados e ao método descritos acima.
- O monitor de mudança nos dados sinalizou **3 de 12 informações usadas pelo modelo**: `season` (TV 0,5280), `yr` (TV 0,6218) e `mnth` (TV 0,7262). Todas ultrapassaram 0,10. Nenhuma informação numérica ultrapassou PSI 0,20. O maior PSI numérico observado foi 0,1356, para `temp`.

Os alertas indicam que os padrões do trecho inicial e do trecho final são diferentes. Não provam que essa mudança causou piora no modelo nem que houve uma falha em operação. As diferenças em ano, mês e estação são compatíveis com a separação temporal usada no histórico, mas isso não demonstra uma relação de causa e efeito.

## O que aprendi

O que aprendi é que repetir uma análise depende de mais do que fixar uma semente aleatória — o valor que ajuda o programa a repetir escolhas feitas ao acaso. Também é necessário obter os mesmos dados da fonte, conferir seu formato e consistência, registrar o período usado e evitar que informações derivadas da resposta sejam usadas para prevê-la. As medidas de desempenho e de mudança nos dados respondem a perguntas diferentes; para interpretá-las, preciso explicar como foram calculadas e em que contexto se aplicam.

## Próximo projeto

Para o próximo projeto, levo um exemplo que pode ser conferido do início ao fim: fonte e termos de uso, verificações, fluxo do modelo, teste por período, comparação simples, desempenho observado e alertas de acompanhamento. Na próxima etapa, esse padrão permitirá comparar os projetos do portfólio com base em evidências, possibilidade de repetir o trabalho e limitações. Também ajudará a identificar quais projetos merecem mais atenção e como desenvolvê-los conforme os resultados, sem presumir efeitos que não foram medidos.

## Como repetir a execução

Na pasta deste projeto, com Python 3.10 ou superior e acesso à internet, execute:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis.py
```

Na primeira execução, o programa baixa o arquivo do endereço oficial do UCI para `data/bike-sharing-dataset.zip`. Depois, reutiliza uma cópia local válida. O resumo das conferências, medidas e alertas aparece em JSON, um formato de dados organizado por campos. A pasta `data/` não é guardada no Git.

## Limites e aviso educacional

Este é um teste histórico, sem operação ao vivo e com uma única separação por data. Não há recebimento contínuo de dados, coleta em produção dos resultados reais para comparar com as previsões, acompanhamento de disponibilidade ou do tempo de resposta, nem avaliações em períodos sucessivos. Portanto, este projeto não demonstra acompanhamento em produção.

As condições do tempo usadas são as registradas no mesmo momento da contagem. O exercício não demonstra que seria possível prever a procura futura sem conhecer o clima futuro. O desempenho pode mudar com outra separação, período, cidade ou padrão dos dados. PSI e TV descrevem diferenças nos dados; antes de usar seus limites para gerar alertas em uma operação, é preciso verificar se fazem sentido naquele contexto.

**Aviso educacional:** este trabalho é um exercício de preparo de dados e de modelos que aprendem com exemplos, não uma recomendação para uso em uma operação real. Não foram medidos impacto no negócio, efeitos de causa e consequência nem benefícios para um sistema real de compartilhamento.

## Referências

[1]: https://archive.ics.uci.edu/ml/datasets/bike+sharing+dataset "UCI Machine Learning Repository: Bike Sharing"
[2]: https://creativecommons.org/licenses/by/4.0/deed.en "Creative Commons Attribution 4.0 International deed"
