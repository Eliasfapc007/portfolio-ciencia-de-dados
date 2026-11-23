# 09 — Recomendação de filmes

## Pergunta

Neste estudo, comparei duas maneiras de recomendar filmes com base nas avaliações do MovieLens. A primeira usa popularidade: recomenda os filmes que receberam mais avaliações positivas. A segunda é uma recomendação colaborativa por filme: procura filmes avaliados positivamente por grupos parecidos de pessoas. Minha pergunta foi: **em uma avaliação com dados antigos, sem testar as recomendações com pessoas em tempo real, qual método encontra mais filmes que cada pessoa avaliou positivamente no período mais recente?** A resposta vale apenas para este método de avaliação e esta versão dos dados; não mede impacto nos negócios.

## Dados, origem e licença

Usei o **MovieLens latest-small**, conjunto de dados publicado pelo GroupLens Research, da University of Minnesota. O script baixa o arquivo oficial, compactado em formato ZIP, com cerca de **1 MB**. Não é necessário fazer login nem usar um código de acesso [1] [2]. Segundo a documentação, o conjunto contém **100.836 avaliações**, **610 usuários** e **9.742 filmes no arquivo de informações dos filmes**. As avaliações vão de **29/03/1996 a 24/09/2018**. Nesta análise, encontrei avaliações para **9.724** desses filmes [2].

A fonte não informa uma licença que permita reutilizar o material sem condições, como CC BY ou MIT. A documentação determina que não se deve sugerir que a University of Minnesota ou o GroupLens apoia o projeto; que a fonte deve ser reconhecida em publicações; que o material só pode ser compartilhado sob as mesmas condições; e que **não pode ser usado para fins comerciais ou para gerar receita sem autorização prévia de um docente do projeto GroupLens** [2]. Este repositório não inclui nem compartilha o ZIP. O arquivo baixado fica em `data/`, uma pasta que o Git não acompanha. O próprio GroupLens explica que a versão latest é um conjunto de desenvolvimento, pode mudar e não é adequada para compartilhar resultados de pesquisa [1] [2]. Por isso, trato os números a seguir como um exercício educacional que pode ser repetido, não como uma medida científica estável para comparar sistemas.

## O que fiz

O script baixa o arquivo oficial e lê `ratings.csv` e `movies.csv` diretamente do ZIP. Antes da análise, confere os nomes das colunas, as notas, as datas e horas registradas (timestamps), os códigos de identificação e a existência de avaliações repetidas para o mesmo par de pessoa e filme. Para cada pessoa, organiza as avaliações por data e hora e reserva as mais recentes para teste. Os dados de treino servem para montar as recomendações; o teste é mantido separado para avaliar o resultado, sem ser usado para montar o modelo. A divisão busca deixar cerca de **80%** dos dados para treino. Avaliações da mesma pessoa com data e hora iguais ficam juntas, do mesmo lado. A separação segue a ordem do tempo, não um sorteio, e não cria dados artificiais.

Considerei positiva uma avaliação de **4,0 estrelas ou mais**. A comparação simples de popularidade conta quantas avaliações positivas cada filme recebeu nos dados de treino. Na recomendação colaborativa por filme, cada filme é representado pelo conjunto de pessoas que o avaliaram positivamente no treino. O script compara esses conjuntos pela similaridade cosseno — uma medida de quanto as listas se parecem — e soma a semelhança com os filmes positivos que a pessoa já avaliou. Nos dois métodos, retiro da lista recomendada os filmes que a pessoa já avaliou no treino. Em caso de empate, o código `movieId` define a ordem de forma consistente.

Na avaliação, considerei relevantes apenas as avaliações positivas feitas no período de teste. Para cada pessoa com pelo menos uma avaliação positiva nesse período, medi dois aspectos:

- **Recall@10**, ou parcela encontrada nas **10** recomendações: indica que parte dos filmes positivos do teste aparece na lista. Quanto maior o valor, maior a parcela encontrada.
- **NDCG@10** (ganho acumulado descontado e normalizado nas **10** recomendações), ou nota que considera a posição dos filmes: indica se os filmes relevantes aparecem mais perto do início da lista. Um valor maior representa uma ordem melhor, com os filmes relevantes em posições mais altas.

Calculei as duas medidas dando o mesmo peso a cada pessoa avaliada, em vez de dar mais peso a quem tem mais avaliações. Só entram nesse grupo as pessoas com pelo menos uma avaliação de **4 estrelas ou mais** no teste.

## Dificuldade técnica observada

**Nível: intermediário.** A documentação oficial informa que as linhas de `ratings.csv` estão organizadas pelo código `userId` e, dentro de cada pessoa, pelo código `movieId` — não pela data [2]. Assim, a ordem original das linhas não mostra quando as avaliações aconteceram. Para fazer a separação temporal, o script ordena as avaliações de cada pessoa pela data e hora e mantém juntas as que têm o mesmo horário. A execução registrada foi concluída com o download oficial; não houve bloqueio de acesso.

## O que encontrei

Estes são os resultados registrados ao executar `analysis.py` neste ambiente com o conjunto de dados indicado:

- O ZIP baixado tinha **978.202 bytes**. Foram processadas **100.836 avaliações**, de **610 usuários**. `movies.csv` contém **9.742 filmes**, e **9.724** aparecem em `ratings.csv`.
- O treino ficou com **80.373 avaliações** e o teste, com **20.463**. Isso corresponde a **79,71%/20,29%** do total. A divisão fica perto de 80/20 para cada pessoa, mas pode variar porque avaliações com a mesma data e hora ficam juntas.
- O teste continha **9.542 avaliações relevantes**, de **590 usuários elegíveis** — isto é, pessoas com pelo menos uma avaliação de **4 estrelas ou mais** no teste.
- **Popularidade:** Recall@10 = **0,049885**, a parcela média dos filmes relevantes que apareceu entre as 10 recomendações; NDCG@10 = **0,079733**, a nota média que considera se esses filmes apareceram mais perto do início da lista.
- **Recomendação por filme, com similaridade cosseno:** Recall@10 = **0,085584** e NDCG@10 = **0,111605**, com os mesmos significados explicados acima.

Neste recorte específico, a recomendação por filme apresentou valores maiores que a comparação simples de popularidade nas medidas calculadas. Isso não prova que um método causou a diferença, que ela seja estatisticamente significativa, que as pessoas ficaram mais satisfeitas ou que houve melhoria nos negócios. Nenhum desses efeitos foi medido.

## O que aprendi

A comparação simples de popularidade serve como referência: um método mais elaborado pode ser comparado com uma alternativa simples usando os mesmos filmes, a mesma separação dos dados e as mesmas medidas. Também aprendi a explicitar escolhas que afetam a leitura do resultado: separar os dados por tempo, não recomendar filmes já avaliados pela pessoa, definir antes o que conta como avaliação positiva e explicar as medidas. A recomendação colaborativa depende de filmes que tenham avaliações positivas em comum. Quando não há pessoas em comum nas listas positivas dos filmes, falta sinal para personalizar a recomendação.

## Ponte para o próximo projeto

Para o próximo projeto, levo a possibilidade de aproveitar este processo repetível e suas medidas feitas fora de uma operação em tempo real. A etapa **10-mlops-monitoramento** pode transformá-los em uma rotina acompanhada ao longo do tempo. A continuidade é registrar o método, a versão dos dados, a quantidade de dados coberta e as medidas de referência para observar mudanças nos dados de entrada ou no desempenho. Este projeto não instala um sistema nem acompanha seu funcionamento continuamente; isso fica para a próxima etapa.

## Como repetir a execução

São necessários Python **3.10 ou superior** e conexão à internet na primeira execução. O arquivo é baixado automaticamente do endereço oficial e fica somente em `data/raw/`.

```bash
cd 09-recomendacao
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
./analysis.py
```

A execução mostra um objeto JSON — um formato de texto organizado por campos — com o tamanho do arquivo, as contagens, o intervalo de datas, a divisão dos dados e as medidas. Para baixar o ZIP novamente, use `./analysis.py --refresh`. Para alterar o tamanho da lista recomendada, use `./analysis.py --k 20`.

## Limites e aviso

O conjunto contém uma amostra de usuários sem identificação e filmes do MovieLens, com dados até **2018**. Pode não representar usuários, listas de filmes ou preferências atuais. As notas foram agrupadas em duas categorias: positivas, a partir do corte de **4 estrelas**, e as demais. A recomendação por filme é simples: não considera gêneros, diferenças gerais nas notas dadas por cada pessoa ou filme, ajuste de configurações do modelo nem tratamento especial para filmes sem histórico. Filmes sem avaliações positivas em comum recebem nota zero; empates são resolvidos pelo código de identificação. A separação por pessoa e por tempo é feita uma única vez, sem uso em tempo real, e não inclui intervalos de confiança nem teste de significância. Os valores podem mudar se a fonte “latest” mudar. Como os dados seguem as condições do GroupLens, não use o conjunto para fins comerciais sem obter a autorização exigida [2].

**Aviso educacional:** este projeto demonstra técnicas de recomendação com dados públicos para estudo e portfólio. As recomendações e medidas não devem ser entendidas como aconselhamento, garantia de resultado em um sistema em produção ou prova de impacto comercial.

## Referências

[1]: https://grouplens.org/datasets/movielens/latest/ "MovieLens Latest Datasets"
[2]: https://files.grouplens.org/datasets/movielens/ml-latest-small-README.html "MovieLens latest-small README and usage conditions"
[3]: https://doi.org/10.1145/2827872 "The MovieLens Datasets: History and Context"
