# 03 — Comparação de grupos: análise estatística

**Etapa 3 de 10 · próxima etapa: `04-classificacao`**

## Pergunta

Neste estudo, comparei, para cada dose registrada de vitamina C, o comprimento médio dos odontoblastos nos grupos que receberam vitamina C por suco de laranja (`OJ`) ou por ácido ascórbico (`VC`). Calculei a diferença como a média de `OJ` menos a média de `VC` (`OJ − VC`). Essa é uma diferença observada entre os grupos; não prova que um suplemento tenha causado uma mudança.

## Dados, fonte e licença

Usei o conjunto `ToothGrowth`, descrito no pacote oficial `datasets` do R. A documentação informa que são 60 cobaias, três doses (0,5, 1 e 2 mg/dia), dois suplementos e três campos (`len`, `supp`, `dose`). O resultado medido é o comprimento dos odontoblastos [1]. O script baixa a versão guardada no repositório oficial do código-fonte do R [4]. A execução registrada confirmou 10 observações em cada uma das seis combinações de dose e suplemento.

A documentação do pacote registra os termos como “Part of R 4.7.0” [2]. O projeto R informa que o R como pacote está licenciado sob GPL-2 ou GPL-3 [3]. Este repositório não inclui nem redistribui o arquivo de dados: `analysis.py` baixa o arquivo durante a execução para `data/raw/`, uma pasta ignorada pelo `.gitignore`. Antes de redistribuir dados ou código da fonte, é preciso consultar os termos aplicáveis à versão e ao arquivo específico.

O conjunto não informa a data de cada observação. A documentação cita Crampton (1947), cujo artigo foi publicado em maio de 1947, e identifica Bliss (1952) como fonte do conjunto [1] [5]. Assim, 1947 é o ano de publicação de uma referência citada, não uma data de coleta confirmada para cada linha.

## O que fiz

Fiz três comparações de médias, uma por dose, tratando os grupos como independentes — isto é, analisei cada grupo separadamente. As comparações são bilaterais: verificam se há diferença em qualquer direção. Em todas, calculei `OJ − VC`.

Usei o teste *t* de Welch, que compara médias sem exigir que os grupos tenham a mesma variação nos resultados. Defini o nível de significância familiar como `α = 0,05`, o limite usado para avaliar em conjunto as três comparações. Como fiz três testes, ajustei os valores-p pelo método de Holm. O valor-p mede o quanto os dados observados são compatíveis com a hipótese de médias iguais; valores menores indicam menor compatibilidade com essa hipótese.

Também calculei intervalos de confiança bilaterais de Bonferroni. Um intervalo de confiança (IC) é uma faixa de valores plausíveis para a diferença, considerando a incerteza dos dados; aqui, o cálculo leva em conta as três comparações. A cobertura simultânea nominal é de 98,33% por comparação (`1 − 0,05/3`). “Nominal” significa que essa é a cobertura prevista pelo método. Uma diferença positiva indica que a média observada foi maior no grupo `OJ`.

Antes dos testes, o script baixa o arquivo oficial, lê as listas de valores publicadas e confere se há 60 observações, os grupos esperados e 10 registros em cada combinação de dose e suplemento. A documentação consultada não informa a unidade de `len`; por isso, apresento as diferenças nas unidades originais da medida, sem atribuir uma unidade física.

## O que encontrei

O relatório registra uma execução de `analysis.py` com o conjunto de dados indicado: foram encontradas 60 observações válidas, com `n = 10` por suplemento em cada dose. Aqui, `n` indica o número de observações em cada grupo. Estes são os resultados registrados pelo script:

- **0,5 mg/dia:** média `OJ = 13,230`, `VC = 7,980`; diferença `OJ − VC = 5,250`; intervalo de confiança simultâneo de 98,33% `[0,787; 9,713]`; estatística do teste `t(14,97) = 3,170` (o número entre parênteses representa os graus de liberdade); `p = 0,006359` e `p_Holm = 0,012717`. Com o limite familiar de 5%, o teste indica diferença entre as médias nesta comparação.
- **1 mg/dia:** média `OJ = 22,700`, `VC = 16,770`; diferença `= 5,930`; intervalo de confiança simultâneo `[1,980; 9,880]`; `t(15,36) = 4,033`; `p = 0,001038` e `p_Holm = 0,003115`. Com o limite familiar de 5%, o teste indica diferença entre as médias nesta comparação.
- **2 mg/dia:** média `OJ = 26,060`, `VC = 26,140`; diferença `= −0,080`; intervalo de confiança simultâneo `[−4,791; 4,631]`; `t(14,04) = −0,046`; `p = 0,963852` e `p_Holm = 0,963852`. Nesta comparação, o teste não encontrou evidência suficiente para indicar diferença entre as médias.

Encontrei diferenças entre as médias observadas dos suplementos nas doses de 0,5 e 1 mg/dia, mesmo depois do ajuste de Holm. Na dose de 2 mg/dia, os dados não mostram evidência estatística de diferença. Isso não prova que os grupos sejam iguais. Os resultados comparam os grupos dentro de cada dose analisada: não demonstram que o suplemento causou a diferença nem descrevem uma resposta geral ao suplemento.

## Dificuldade técnica observada

**Nível: intermediário.** A fonte oficial fornece os dados como código R (`ToothGrowth.R`), não como uma tabela CSV pronta. Além disso, o campo `supp` usa códigos numéricos para representar uma categoria, enquanto os nomes `OJ` e `VC` são definidos separadamente. Para evitar associar valores ao grupo errado, o script interpreta cada campo e confere os nomes dos grupos e as seis contagens antes dos testes. A fonte respondeu e os dados foram executados; não houve bloqueio de acesso.

## O que aprendi

Aprendi que a comparação precisa respeitar a forma como os dados e os grupos estão organizados. Ao comparar cada dose separadamente, não misturo grupos que receberam doses diferentes. O método de Welch não exige que os grupos tenham a mesma variação, e o ajuste de Holm considera que fiz três testes. Também é importante apresentar intervalos e diferenças, além dos valores-p, e explicar o que a documentação não permite concluir — especialmente sobre datas de coleta, unidades e distribuição dos animais entre os grupos.

## Ponte para o próximo projeto

Para o próximo projeto, levo a prática de definir campos e grupos sem ambiguidade, conferir os dados antes da análise e alinhar a conclusão ao método usado. Na etapa `04-classificacao`, vou trocar a comparação de médias pela previsão de categorias e avaliar o desempenho das previsões, sem confundir previsão com explicação de causa.

## Como reproduzir

É necessário ter Python 3.10 ou posterior e conexão à internet para baixar a fonte oficial na primeira execução:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis.py
```

O script cria `data/raw/ToothGrowth.R`, arquivo ignorado pelo Git. Se a rede falhar, usa apenas uma cópia que já esteja baixada nesse caminho; se não houver cópia, encerra com erro em vez de criar dados substitutos. Não é necessário definir uma semente aleatória, porque a análise não sorteia nem separa os dados ao acaso.

## Limites e aviso educacional

O conjunto tem apenas 10 animais por combinação e é histórico. A documentação consultada não explica como os animais foram distribuídos entre os grupos, se houve sorteio, se os animais eram independentes entre si, qual foi o protocolo de medição ou se a amostra representa outros animais. Por isso, apresento diferenças entre grupos e testes para cada dose, sem afirmar que o tipo de suplemento causou as diferenças. Os testes não avaliam se o efeito do suplemento muda conforme a dose, nem uma tendência de resposta conforme a dose aumenta. Também não foi feita uma verificação formal para saber se, em cada combinação de dose e suplemento, os resultados seguem uma distribuição em forma de sino (normalidade) ou se há valores extremos, muito diferentes dos demais. As conclusões se aplicam a este conjunto, não a pessoas ou a outros contextos.

Este material é educacional e não constitui orientação veterinária, médica ou nutricional.

## Referências

[1]: https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/ToothGrowth.html "Documentação oficial de ToothGrowth no manual do R"
[2]: https://cran.r-project.org/doc/manuals/r-devel/packages/datasets/refman/datasets.html "Manual de referência oficial do pacote datasets no CRAN"
[3]: https://www.r-project.org/Licenses/ "Licenças de R e software associado"
[4]: https://svn.r-project.org/R/trunk/src/library/datasets/data/ToothGrowth.R "Arquivo-fonte oficial de ToothGrowth no repositório SVN do R"
[5]: https://doi.org/10.1093/jn/33.5.491 "Crampton 1947, artigo citado pela documentação de ToothGrowth"
