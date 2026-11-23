# 01 — Conferência da qualidade dos dados e análise inicial

**Etapa 1 de 10 · próxima etapa: `02-sql-indicadores`**

## Pergunta

Neste estudo, analisei uma pergunta descritiva sobre o conjunto Adult: **nos registros históricos, como varia a parcela de registros com o rótulo de renda anual acima de 50 mil dólares (`>50K`) entre grupos do código numérico de escolaridade `education-num`? E que problemas aparecem em informações não preenchidas ou em linhas repetidas?**

A análise ajuda a praticar contagens e comparações de dados reais. O resultado não mede a renda atual nem explica por que as diferenças aparecem.

## Dados, fonte e licença

Usei o conjunto de dados *Adult*, publicado no UCI Machine Learning Repository, um repositório de dados para aprendizado de máquina. A ficha informa **48.842 registros** (linhas), **14 atributos** (campos de informação) e uma extração da base censitária dos Estados Unidos de **1994**. Os dados vêm em dois arquivos: `adult.data` e `adult.test`. Na execução registrada neste projeto, o arquivo ZIP baixado pelo script tinha **620.237 bytes**. A ficha da UCI informa que alguns campos — entre eles `workclass`, `occupation` e `native-country` — têm valores ausentes, ou seja, informações que faltam [1].

A licença indicada pela UCI é **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Ela permite compartilhar e adaptar o material, inclusive para uso comercial, desde que se dê o crédito adequado, inclua o link da licença e indique as alterações. Também não se deve dar a entender que a UCI aprova este projeto [1] [3]. A ficha recomenda dar crédito a Becker e Kohavi (1996) [1].

Os arquivos de dados originais não estão incluídos neste projeto. Ao executar o programa, o ZIP oficial é baixado para `data/adult.zip`. O `.gitignore` impede que essa pasta seja incluída no Git, o sistema usado para acompanhar mudanças nos arquivos do projeto. O ZIP contém os arquivos originais listados pela UCI [2].

## O que fiz

1. Li `adult.data` e `adult.test`, conferi o total esperado de linhas em cada arquivo e juntei os registros. Nesse caso, ler significa separar as informações de cada linha nos campos correspondentes. Fiz essa leitura diretamente dentro do ZIP, sem criar cópias dos arquivos CSV na pasta. CSV é um formato usado para guardar tabelas.
2. Tratei o sinal `?` usado pela fonte como informação ausente. Não removi linhas nem inventei valores para preencher os espaços.
3. Conferi quantas linhas e colunas havia, quais eram os dois rótulos de renda e se alguns campos numéricos estavam dentro de faixas plausíveis. Essas verificações avaliam a organização e os valores básicos dos arquivos; não treinam nem testam um modelo de previsão.
4. Contei as linhas exatamente repetidas nos **15 campos originais** e as mantive para não alterar os dados de origem.
5. Para responder à pergunta, separei os códigos de `education-num` em três faixas: **1–8**, **9–12** e **13–16**. Em cada faixa, dividi o número de registros com o rótulo `>50K` pelo total de registros daquele grupo. Assim, obtive uma porcentagem simples por linha. Não usei pesos, testes estatísticos nem intervalos de confiança.

## Dificuldade técnica observada

**Nível: intermediário.** Os dois arquivos originais têm pequenas diferenças de formato: `adult.test` começa com uma linha de comentário e acrescenta um ponto final aos rótulos de renda. A fonte também usa `?` para algumas informações ausentes. Para lidar com esses formatos, o código ignora a linha de comentário, ajusta os rótulos, trata `?` como informação ausente e confere o número de linhas dos dois arquivos antes de calcular os resultados.

## O que encontrei

Os resultados abaixo vêm da execução registrada de `analysis.py --force-download` com o conjunto Adult descrito neste relatório:

- Li **48.842 linhas**: **32.561** de `adult.data` e **16.281** de `adult.test`, com **14 atributos e 1 rótulo**. O rótulo é a categoria informada para cada registro; aqui, indica a faixa de renda. As conferências da organização dos arquivos, dos rótulos e das faixas numéricas foram aprovadas.
- Encontrei **52 linhas exatamente repetidas** nos **15 campos originais**. Mantive essas linhas; não as apaguei.
- Depois de tratar `?` como informação ausente, contei **6.465 campos sem informação**. `workclass` tinha **2.799 (5,73%)** das linhas, `occupation` tinha **2.809 (5,75%)** e `native-country` tinha **857 (1,75%)**.
- No conjunto inteiro, **11.687 registros (23,93%)** tinham o rótulo `>50K`; **37.155 (76,07%)** tinham o rótulo `<=50K`.
- A idade ia de **17 a 90 anos**. A mediana — o valor que fica no meio quando as idades são ordenadas — era **37,0** anos. A média — a soma das idades dividida pela quantidade de registros — era **38,6**.
- A parcela de registros com o rótulo `>50K` foi **5,71%** no grupo `education-num` **1–8** (**366 de 6.408**), **18,14%** no grupo **9–12** (**5.501 de 30.324**) e **48,06%** no grupo **13–16** (**5.820 de 12.110**). Por exemplo, **48,06%** quer dizer que essa era a parcela dos registros daquele grupo que tinha o rótulo `>50K`.

Neste recorte histórico, a parcela de registros com o rótulo `>50K` é maior nos grupos com códigos mais altos de `education-num`. Isso descreve os registros deste conjunto: não prova que a escolaridade causou a diferença, não prevê a situação de uma pessoa e não mostra o que ocorreria com dados atuais.

## O que aprendi

O que aprendi com esta análise é que vale conferir os arquivos e identificar informações ausentes antes de resumir os dados. Uma pequena diferença de formato entre arquivos pode causar erros de leitura; por isso, o programa confere os totais esperados e os rótulos depois de ler os arquivos.

Também deixei explícito como calculei cada porcentagem: usei somente as linhas da faixa correspondente, então o total da divisão é o número de registros daquele próprio grupo.

## Próximo projeto

Para o próximo projeto, levo os indicadores e os totais usados nesta análise. Na etapa `02-sql-indicadores`, as mesmas contagens por faixa, divisões para obter porcentagens e conferências de linhas ausentes ou repetidas podem ser feitas em SQL. Comparar os resultados permitirá verificar se o cálculo em SQL reproduz a análise feita em Python.

## Como reproduzir

É necessário ter Python **3.10** ou mais recente e acesso à internet para baixar os dados na primeira execução. O pacote `pandas` é instalado pelo arquivo `requirements.txt`.

```bash
cd 01-eda-qualidade
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis.py
```

Na primeira execução, o programa baixa o ZIP oficial. Isso pode levar alguns minutos, dependendo da conexão. Nas execuções seguintes, usa a cópia guardada no computador. Para baixar o arquivo de novo, rode `python analysis.py --force-download`. Para guardar essa cópia em outra pasta, use `python analysis.py --data-dir /caminho/para/cache`.

## Limites e aviso educacional

A base descreve uma realidade histórica dos Estados Unidos, baseada na base censitária de **1994**, conforme a UCI. Ela não representa automaticamente a população ou o mercado de trabalho atuais. O rótulo `>50K` vem da fonte e não foi ajustado pela inflação. As porcentagens são contagens simples por registro: o programa não usa o campo `fnlwgt` como peso para estimar totais da população. As **52 linhas repetidas** foram mantidas e podem influenciar as porcentagens se forem cópias que não deveriam estar ali. As informações ausentes foram contadas, mas não preenchidas; não são necessárias para separar os registros nas faixas usadas nesta pergunta.

A base contém informações demográficas sensíveis. Esta análise não verifica se os resultados são justos, não calcula efeitos de causa e não deve ser usada para decidir sobre contratação, crédito ou tratamento de pessoas. É um exercício educacional com dados históricos.

## Referências

[1]: https://archive.ics.uci.edu/dataset/2/adult "UCI Machine Learning Repository: Adult"
[2]: https://archive.ics.uci.edu/static/public/2/adult.zip "Arquivos originais do UCI Adult em ZIP"
[3]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
