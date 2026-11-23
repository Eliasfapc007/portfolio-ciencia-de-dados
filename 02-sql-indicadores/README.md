# 02 — Indicadores de compras com SQL

## Pergunta e objetivo

Neste estudo, analisei quantas visitas a uma loja virtual terminaram em compra e comparei essa proporção entre tipos de visitante, fins de semana e meses. Os dados de visitas foram publicados pela UCI. Cada linha representa uma visita ao site, não um produto vendido.

SQL é uma linguagem usada para pedir a um banco de dados que conte, some e organize informações. Um banco de dados guarda informações de forma organizada. O script usa Python, uma linguagem de programação, para carregar o arquivo em um banco SQLite — um programa leve que pode ser usado com os recursos incluídos na instalação padrão do Python — e fazer as consultas.

## Dados, fonte e licença

Usei o [UCI Machine Learning Repository — Online Shoppers Purchasing Intention Dataset][1], repositório que disponibiliza conjuntos de dados para aprendizado de máquina. A página oficial descreve 12.330 sessões reunidas ao longo de um período de um ano e informa que cada sessão pertence a uma pessoa diferente. Uma sessão corresponde a uma visita ao site. O arquivo traz o campo `Month` (mês), mas a página não informa as datas exatas de início e fim desse período.

O arquivo utilizado é um CSV: um arquivo de texto organizado em linhas e colunas, com os campos separados por vírgulas. Ele tem 18 colunas, 12.330 linhas de dados e 1.072.063 bytes. Segundo a UCI, 10.422 sessões não terminaram em compra e 1.908 terminaram em compra; o script confirmou as mesmas contagens nesta cópia [1].

O conjunto está sob a licença [Creative Commons Attribution 4.0 International (CC BY 4.0)][3]. Em termos simples, ela permite compartilhar e adaptar os dados, inclusive para qualquer finalidade, desde que a autoria e a fonte sejam informadas. Os arquivos publicados pelo projeto não incluem os registros de cada visita: o script baixa os dados da [distribuição oficial da UCI][2].

O Git é uma ferramenta para guardar versões de um projeto. O arquivo `.gitignore` informa ao Git quais pastas deve deixar de fora; neste caso, a pasta `data/`. A referência indicada pela UCI é Sakar, C. & Kastro, Y. (2018), *Online Shoppers Purchasing Intention Dataset*, DOI [10.24432/C5F88Q][5]. DOI é um código que identifica uma publicação ou conjunto de dados.

## O que fiz

A medida principal foi a **taxa de conversão**, isto é, a porcentagem de visitas que terminou em compra. Para calculá-la, o script divide o número de sessões com `Revenue = TRUE` pelo total de sessões do grupo. Nesse campo, `TRUE` significa que houve compra. Separei as visitas em grupos — por exemplo, visitantes novos ou visitas no fim de semana — e usei consultas SQL para contar sessões e compras e calcular a porcentagem no conjunto completo e em cada grupo.

As comparações são descritivas: mostram o que está registrado neste arquivo, mas não explicam por que aconteceu. As consultas agrupam os dados pelos campos `VisitorType` (tipo de visitante), `Weekend` (fim de semana) e `Month` (mês). Os meses aparecem abreviados em inglês no arquivo; nos resultados mensais, foram organizados na ordem do calendário, não em ordem alfabética.

Antes dos cálculos, o script verifica o cabeçalho, campos vazios, valores numéricos, categorias de mês e de tipo de visitante, respostas `TRUE/FALSE`, número de linhas e número de compras. Também confere o SHA-256 — uma espécie de impressão digital que ajuda a detectar alterações ou danos no arquivo.

O processamento usa o SQLite em memória. Isso significa que o programa carrega os registros para calcular as medidas, mas não salva um banco com as linhas de cada visita. Ele grava apenas arquivos com resultados agrupados e resumidos.

## Dificuldade técnica observada

**Nível: intermediário.** A primeira opção considerada foi outro conjunto de dados de transações da UCI, o [Online Retail][4]. A UCI informa que a planilha desse conjunto tem 22,6 MB. A tentativa de baixar o arquivo oficial não terminou por causa do tempo limite; o arquivo incompleto foi descartado e não foi analisado. Como alternativa, usei os dados de visitas deste projeto, baixados da fonte oficial e conferidos.

A escolha da pergunta também foi limitada pelos dados. Segundo a UCI, cada pessoa aparece em uma única sessão, então não há um identificador de cliente repetido que permita acompanhar visitas ao longo do tempo. Por isso, medi compras por visita. Este conjunto não permite medir retenção — quantas pessoas voltam em outras visitas — nem acompanhar grupos de clientes ao longo do tempo. Uma coorte é um grupo de pessoas acompanhado desde um mesmo ponto, como o mês da primeira compra.

## O que encontrei

A análise foi executada com o CSV oficial. Os valores abaixo foram exibidos e salvos pelo `analysis.py` após essa execução. No conjunto completo, **1.908 de 12.330 sessões terminaram em compra**, uma taxa de **15,4745%**. Em termos práticos, isso corresponde a cerca de 15 compras a cada 100 visitas observadas neste arquivo; não é uma previsão para outras lojas.

Entre visitantes novos, encontrei **422 compras em 1.694 sessões (24,9115%)**. Entre visitantes recorrentes, foram **1.470 em 10.551 (13,9323%)**. A categoria `Other` teve **16 em 85 (18,8235%)**. Neste arquivo, a proporção de compras foi maior nas visitas identificadas como novas do que nas identificadas como recorrentes. Como `Other` reúne poucas visitas, seu percentual pode variar bastante. Esses dados não mostram que ser visitante novo cause mais compras.

No fim de semana, a taxa observada foi de **499/2.868 (17,3989%)**; nos dias de semana, foi de **1.409/9.462 (14,8911%)**. A diferença descreve o que aparece neste conjunto e não demonstra que mudar o dia da visita aumentaria as compras.

Entre os meses com registros, fevereiro teve a menor taxa observada: **3/184 (1,6304%)**. Novembro teve a maior: **760/2.998 (25,3502%)**. As proporções registradas diferem entre esses grupos, mas o arquivo não informa o motivo, e o número de visitas varia bastante de um mês para outro. Este CSV não tem registros em janeiro nem abril.

Os resultados completos por mês estão em [`outputs/monthly_conversion.csv`](outputs/monthly_conversion.csv). As contagens e taxas de todos os grupos estão em [`outputs/summary.json`](outputs/summary.json) e [`outputs/segment_conversion.csv`](outputs/segment_conversion.csv).

## Em palavras simples

- **Conversão**: entre as visitas de um grupo, quantas terminaram em compra. No total, 15,4745% significa cerca de 15 compras a cada 100 visitas deste arquivo.
- **Agrupar dados**: separar as visitas em conjuntos comparáveis, como fim de semana e dia de semana, para contar cada conjunto.
- **Resultado descritivo**: um retrato do que foi registrado. Ele não mostra que uma característica causou o resultado nem prova que a mesma diferença apareceria em outra loja.

## O que aprendi

Uma taxa fica mais fácil de interpretar quando apresento junto o cálculo e o total usado na comparação. Por isso, mostrei tanto as compras quanto as sessões de cada grupo, não apenas as porcentagens. Também aprendi que os dados disponíveis determinam quais perguntas posso responder: sem um identificador de pessoa ou visitas repetidas, este arquivo não permite avaliar retenção.

## Ponte para o próximo projeto

Para o próximo projeto, levo as definições estabelecidas aqui: o que conta como compra, qual total de sessões usar no cálculo da porcentagem e quais grupos comparar. O projeto **03-inferencia-experimento** poderá investigar se uma diferença observada pode ter ocorrido por acaso e como planejar um experimento para testar uma mudança. Este projeto, por si só, não faz esse teste.

## Como reproduzir

Para reproduzir a análise, execute os comandos a partir da pasta principal do repositório clonado.  é necessário ter Python 3.10 ou superior e acesso à internet na primeira execução. Não é preciso instalar pacotes externos; o `requirements.txt` registra essa informação.

```bash
cd 02-sql-indicadores
python3 analysis.py
```

O script baixa o pacote público da UCI para `data/raw/`, confere o arquivo e cria os resultados resumidos em `outputs/`. Se o arquivo já tiver sido baixado e conferido, ele é usado novamente. A pasta `data/` guarda os dados originais e não aparece nos arquivos publicados do projeto porque o `.gitignore` manda o Git ignorá-la.

## Limites e aviso educacional

Segundo a descrição da fonte, cada pessoa aparece em uma única sessão. Portanto, estes dados não permitem estimar o retorno de clientes, a retenção ou acompanhar grupos de clientes ao longo do tempo. O arquivo também não informa a data completa de cada sessão, apenas o mês, e não tem registros para janeiro ou abril. O número de visitas varia entre os grupos, especialmente na categoria `Other` (85 sessões). `Revenue` informa se houve compra, não quanto dinheiro foi recebido; por isso, os resultados não medem faturamento.

Os dados representam um site e um período descritos pela fonte, não todo o comércio eletrônico. As comparações entre grupos não separam as demais diferenças entre as visitas. Elas não demonstram causa e efeito, impacto no negócio nem o resultado que uma mudança implantada teria. Este é um material educacional: não use estas estimativas, sozinhas, para tomar decisões comerciais.

## Referências

[1]: https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset "Online Shoppers Purchasing Intention Dataset"
[2]: https://archive.ics.uci.edu/static/public/468/online+shoppers+purchasing+intention+dataset.zip "Arquivo oficial do dataset no UCI"
[3]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
[4]: https://archive.ics.uci.edu/dataset/352/online+retail "Online Retail Dataset"
[5]: https://doi.org/10.24432/C5F88Q "Citação do dataset Online Shoppers Purchasing Intention"
