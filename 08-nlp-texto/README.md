# Projeto 08 — Análise de avaliações de produtos

**Etapa 8 de 10 · Próxima etapa: `09-recomendacao`**

## Pergunta do projeto

Neste estudo, analisei se um programa consegue classificar avaliações em português como positivas ou negativas usando as palavras do texto como pistas. Comparei esse método com uma referência simples: escolher sempre o sentimento que aparece mais vezes. Separei os dados em uma parte para o programa aprender e outra, não usada no aprendizado, para conferir o resultado. Esse teste mede o desempenho nesta divisão dos dados; não mostra impacto comercial nem prova que uma coisa causou outra.

A análise registrada usa uma amostra real de avaliações de produtos do corpus RePro. Pessoas classificaram essas avaliações para estudos de opiniões em português brasileiro. A publicação do RePro descreve 10.000 avaliações com rótulos de sentimento e tópico [1] [2].

## Dados, origem e licença

Usei o conjunto **RePro — REview of PROducts**, disponível no repositório [lucasnil/repro](https://github.com/lucasnil/repro). O arquivo é um CSV público no Hugging Face, baixado de uma revisão específica (`cb93d9cc1183d4a594317a5188d325bcaa04cda4`) [1] [3]. Não é preciso ter conta ou token para baixá-lo. O script lê somente as colunas `review_text`, `polarity` e `submission_date`; não exibe nem exporta o texto das avaliações.

A página do RePro descreve 10.000 avaliações classificadas manualmente [1] [2]. No arquivo fixado, a execução leu **10.003 registros e 22 colunas**. As datas iam de **1º de janeiro a 31 de maio de 2018**, período compatível com a descrição do conjunto original B2W-Reviews01, coletado entre janeiro e maio de 2018 [4]. A documentação consultada não explica a diferença entre os 10.000 registros descritos e os 10.003 lidos no arquivo. Por isso, mantenho os dois números sem supor o motivo.

**Termos de uso:** o repositório do RePro e o texto do cartão de dados declaram a licença **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**. Ela exige atribuição de crédito, proíbe uso comercial e determina que adaptações sejam compartilhadas sob a mesma licença [1] [2] [5]. Já o campo de licença nos dados do Hugging Face indica `CC BY 4.0`, em desacordo com o texto explicativo do próprio cartão e com o repositório [1] [2]. Por cautela, trato o conjunto e seus derivados como sujeitos aos termos mais restritivos da **CC BY-NC-SA 4.0**, e não destinados a uso comercial, até que os responsáveis esclareçam a diferença. Isto não é uma avaliação jurídica; confira os termos antes de reutilizar ou redistribuir o material.

O CSV original é baixado para `data/RePro.csv`, em uma pasta ignorada pelo Git. Não coloque esse arquivo em um repositório público. Ele contém os textos e outros dados sobre avaliações e perfis que não são necessários para esta análise.

## O que fiz

1. Baixei a versão fixada do CSV e conferi os nomes das colunas e a estrutura das linhas.
2. Examinei a coluna `polarity`, que guarda listas de rótulos. Para classificar apenas entre duas opções, mantive registros com exatamente um rótulo: `NEGATIVO` ou `POSITIVO`. Excluí avaliações neutras e avaliações com mais de um sentimento.
3. Removi textos exatamente repetidos antes de separar os dados. Se o mesmo texto aparecesse com rótulos diferentes, o script excluiria todas as cópias: assim, não escolheria um rótulo ao acaso nem deixaria o mesmo texto nas duas partes, o que poderia inflar o resultado.
4. Separei os dados uma vez: **80% para o programa aprender e 20% para conferir o desempenho**. Mantive proporções parecidas de avaliações positivas e negativas nas duas partes. O parâmetro `random_state=42` torna essa divisão reproduzível.
5. Comparei a escolha do sentimento mais frequente com o **TF-IDF**, uma forma de transformar palavras em números considerando sua frequência e raridade nos textos. O método considera palavras individuais e pares de palavras (unigramas e bigramas) e usa **regressão logística**, que calcula qual das duas classes parece mais provável. O ajuste é feito somente com os dados de treino — os usados para aprender — e dá mais peso à classe menos comum por meio de `class_weight="balanced"`.
6. Conferi as previsões nos dados de teste, separados do aprendizado. Usei acurácia, F1 macro, precisão, recall, F1 por classe e matriz de confusão. A **acurácia** é a proporção de previsões corretas. **Precisão** indica, entre os casos marcados com um sentimento, quantos tinham esse sentimento; **recall** indica quantos dos casos que realmente tinham aquele sentimento foram encontrados. O **F1** combina precisão e recall em uma medida, e o **F1 macro** calcula a média das duas classes dando o mesmo peso a cada uma. Nestas medidas, valores mais próximos de 1 indicam resultados melhores. A matriz de confusão conta acertos e erros: as linhas mostram o sentimento real e as colunas, o previsto. A ordem de ambas é `NEGATIVO` e depois `POSITIVO`.

## Dificuldade técnica observada

**Nível: intermediário.** A principal dificuldade esteve no formato dos rótulos: a coluna de polaridade não traz um rótulo simples, mas listas que podem conter mais de um sentimento. Foi necessário conferir esse formato e manter apenas os casos com um único rótulo positivo ou negativo. Dos 10.003 registros lidos, 2.018 tinham mais de um sentimento e 409 eram neutros; esses casos ficaram fora da classificação binária. O arquivo também tinha três registros a mais que o tamanho anunciado, sem explicação encontrada na documentação. Depois do filtro, uma avaliação repetida exatamente foi removida antes da separação dos dados.

## O que encontrei

Os números abaixo são da execução registrada de `python3 analysis.py --refresh`, com Python 3.12.3 e scikit-learn 1.9.1 (biblioteca usada para treinar e avaliar o programa):

- O primeiro filtro manteve **7.576** avaliações: 4.127 positivas e 3.449 negativas. Após remover um texto repetido exatamente, restaram **7.575** textos: 4.126 positivos e 3.449 negativos.
- A separação preservou proporções parecidas entre os sentimentos e resultou em **6.060** exemplos para aprender e **1.515** para conferir.
- A comparação que sempre escolhe a classe mais frequente acertou **54,46%** dos casos e teve **0,3526 de F1 macro**. Como marcou todos os casos como positivos, não encontrou nenhum dos 690 exemplos negativos do teste.
- O método TF-IDF com regressão logística acertou **95,31%** dos casos e teve **0,9529 de F1 macro** neste teste. O F1 macro vai de 0 a 1; esse valor, próximo de 1, resume o resultado das duas classes com o mesmo peso.
- A matriz de confusão, com sentimento real nas linhas e previsto nas colunas — na ordem `NEGATIVO`, `POSITIVO` — foi `[[673, 17], [54, 771]]`. Foram **71 erros em 1.515 previsões (4,69%)**: 17 avaliações negativas foram marcadas como positivas e 54 positivas, como negativas. O recall foi 97,54% para avaliações negativas e 93,45% para positivas. Em termos práticos, essas são as proporções dos exemplos de cada sentimento no teste que o programa encontrou.

Esses números descrevem somente esta divisão dos dados e este procedimento de teste. A diferença em relação à comparação simples não indica como o programa funcionaria em outros períodos, plataformas ou usos reais.

## O que aprendi

O que aprendi com este experimento é como representar palavras por números e comparar um classificador com uma referência simples, de forma reproduzível e mensurável. Separar o aprendizado do teste ajuda a evitar que os dados usados para conferir influenciem o ajuste. Também vi que a seleção das avaliações faz parte do método: excluir textos neutros ou com mais de um sentimento permite classificar apenas entre positivo e negativo, mas restringe quais textos os resultados representam.

Uma medida alta não significa que o programa entende a linguagem. O TF-IDF representa a frequência de palavras e de pares próximos, mas não interpreta de forma confiável a negação e seu alcance, a ironia, o sarcasmo, o contexto longo ou opiniões diferentes dentro de um mesmo texto. Diferenças na escrita, gírias e o tipo de avaliação também podem alterar os padrões aprendidos.

## Ponte para a próxima etapa

Para a próxima etapa, levo o preparo dos dados, o cuidado com a reprodução da análise, a separação entre aprendizado e teste e a medição de erros. Em `09-recomendacao`, o foco muda: em vez de classificar uma avaliação, vou relacionar pessoas usuárias, itens e preferências. Preparar textos e usar sentimento como informação auxiliar pode ser útil, mas essas habilidades não foram medidas neste classificador. A etapa seguinte também exigirá compreender as interações entre pessoas e itens e avaliar recomendações.

## Como reproduzir a análise

São necessários Python 3.10 ou superior e acesso à internet para o primeiro download. Na pasta deste projeto, execute:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis.py
```

Na primeira execução, o programa baixa o CSV para `data/`. Nas seguintes, usa a cópia local, ignorada pelo Git. Para baixar novamente a mesma revisão fixada, execute:

```bash
python analysis.py --refresh
```

O script mostra somente contagens agrupadas, medidas, versões das ferramentas e a identificação digital do arquivo (hash SHA-256). Não mostra as avaliações nem salva um modelo treinado. A revisão e o SHA-256 observados aparecem no resultado da execução. Os parâmetros da separação e do método estão definidos em `analysis.py`.

## Limites

- O resultado vem de uma única separação aleatória que mantém proporções parecidas entre as classes. Não fiz validação cruzada (repetição do teste com várias separações), nem teste com dados de outro período ou de outra fonte.
- Os dados são avaliações brasileiras de produtos, com datas de 2018. Não representam necessariamente outros tipos de texto, períodos ou grupos de pessoas.
- Excluí rótulos neutros e com mais de um sentimento; por isso, as medidas não mostram como o programa classificaria essas avaliações.
- O corpus tem rótulos de sentimento, mas uma avaliação pode expressar sentimentos diferentes sobre o produto, a entrega e o atendimento. O programa usa somente o texto e não separa esses aspectos.
- A análise de palavras e pares de palavras não corrige erros de escrita, gírias ou variações das palavras por meio de análise linguística. Também não resolve ironia, sarcasmo ou negação dentro do contexto.
- A diferença entre as licenças informadas no cartão do Hugging Face e no repositório exige cautela. Este projeto não redistribui o CSV original.
- Esta é uma demonstração educacional, não um sistema testado para tomar decisões automáticas sobre clientes, avaliações ou moderação.

## Referências

[1]: https://github.com/lucasnil/repro "Repositório RePro, descrição do conjunto de dados e termos declarados"
[2]: https://huggingface.co/datasets/lucasnil/repro/raw/main/README.md "Cartão de dados do RePro no Hugging Face"
[3]: https://huggingface.co/datasets/lucasnil/repro/resolve/cb93d9cc1183d4a594317a5188d325bcaa04cda4/RePro.csv "Arquivo CSV RePro na revisão fixada"
[4]: https://github.com/americanas-tech/b2w-reviews01 "Conjunto original B2W-Reviews01 e seus termos"
[5]: https://creativecommons.org/licenses/by-nc-sa/4.0/ "Creative Commons Attribution-NonCommercial-ShareAlike 4.0"
[6]: https://aclanthology.org/2024.propor-1.44/ "Publicação do RePro na ACL Anthology, PROPOR 2024"
