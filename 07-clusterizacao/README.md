# 07 — Formação de grupos semelhantes

## Pergunta principal

É possível resumir padrões diferentes de gastos anuais de clientes de um distribuidor atacadista usando seis categorias de produtos? Neste estudo, analisei essa pergunta com o conjunto de dados **Wholesale customers**, do repositório UCI. O projeto transforma e coloca os valores em escalas comparáveis, testa diferentes quantidades de grupos e mede os resultados. Também descreve os grupos em termos simples.

O agrupamento serve para explorar os dados. Ele não mede o valor comercial dos grupos nem recomenda ações.

## Dados, fonte e licença

Usei os dados do [UCI Machine Learning Repository][1]. A ficha da UCI descreve gastos anuais, em unidades monetárias (abreviadas como m.u.), de clientes de um distribuidor atacadista e lista 440 observações. A página registra que os dados foram doados em 30 de março de 2014, mas não informa em que ano ou período os gastos foram observados, nem define a moeda. Segundo a ficha da UCI, o arquivo CSV (uma tabela de dados) oficial tem 14,7 KB. O projeto baixa o arquivo ZIP (um pacote compactado) diretamente do repositório oficial [2].

A licença declarada pela UCI é **Creative Commons Attribution 4.0 International (CC BY 4.0)**. Ela permite compartilhar e adaptar o material, inclusive para qualquer finalidade, desde que a fonte seja atribuída corretamente [1] [3]. Neste projeto, cito a fonte e não incluo nem guardo uma cópia dos dados originais no controle de versões. O script baixa o ZIP quando necessário e o mantém em `data/`, uma pasta excluída pelo `.gitignore` (arquivo que informa ao Git quais itens não incluir no controle de versões).

O CSV baixado tem 440 linhas e oito colunas. Para formar os grupos, usei somente as seis variáveis numéricas de despesas: `Fresh`, `Milk`, `Grocery`, `Frozen`, `Detergents_Paper` e `Delicassen`. Deixei de fora `Channel` e `Region`, porque indicam categorias, não gastos. A ficha da UCI classifica `Region` como variável-alvo (um campo separado como resultado de interesse), não como despesa. Não usei nenhuma dessas duas colunas para formar ou conferir os grupos.

## Como fiz a análise

1. O script baixa o arquivo do endereço oficial e confere se as colunas e o formato estão como esperado. Também exige as 440 linhas previstas e verifica se faltam valores ou se há despesas negativas nas seis variáveis. O CSV fica guardado temporariamente no computador, numa pasta ignorada pelo Git.
2. A análise aplica `log1p` a cada despesa. Essa transformação reduz o peso das diferenças muito grandes entre valores baixos e altos. Depois, usa `StandardScaler`, um ajuste que coloca as seis variáveis em escalas comparáveis.
3. Para agrupar os dados, o script usa K-Means, um método que separa observações em uma quantidade escolhida de grupos com valores parecidos. Faz `n_init=20` tentativas, usa a semente 42 (um valor que ajuda a repetir a mesma configuração) e testa de `k=2` a `k=8`; aqui, `k` representa a quantidade de grupos. Antes de ver os resultados, defini como regra escolher o valor com a maior *silhouette*. Essa medida compara o quanto cada observação combina com o próprio grupo em relação aos outros; um valor maior é preferido. Também calculei Calinski–Harabasz, outra medida de separação dos grupos, em que valores maiores são preferidos; Davies–Bouldin, uma medida de quão parecidos ou próximos os grupos são, em que valores menores são preferidos; e *inertia* (inércia), a soma das distâncias dentro dos grupos, que costuma cair quando aumenta a quantidade de grupos.
4. Para conferir se o resultado de `k` escolhido se mantém, o script repete o ajuste com dez sementes seguidas, começando em 42. Compara todos os 45 pares de divisões usando o Adjusted Rand Index (ARI), uma medida de quanto duas divisões concordam. Por fim, descreve cada grupo pelas medianas das despesas nas unidades monetárias originais. Mediana é o valor que fica no meio quando os valores são ordenados. Os grupos não recebem nomes de tipos fixos de clientes.

Calculei as medidas de separação usando os dados depois da transformação logarítmica e do ajuste de escala. Não separei dados para aprender e dados de teste (dados que o método não usa para aprender). A avaliação foi feita nas mesmas 440 observações usadas para formar os grupos, pois o conjunto não tem rótulos que indiquem grupos de referência. Excluí `Region` de propósito e não a tratei como resposta correta para comparar os grupos.

## Dificuldade técnica observada

**Nível: intermediário.** A dificuldade observada está na estrutura e na escala dos dados: o CSV tem oito colunas, mas somente seis são despesas numéricas; a ficha da UCI informa sete características e classifica `Region` como variável-alvo. Para responder à pergunta sobre padrões de gastos, conferi a descrição das colunas na fonte e deixei `Channel` e `Region` de fora.

Além disso, nas seis variáveis, os maiores valores observados são de 13,19 a 50,00 vezes as medianas. Sem transformação e ajuste de escala, o K-Means dependeria muito das diferenças entre os valores dos gastos. Usar `log1p` e colocar as variáveis em escalas comparáveis ajuda a lidar com essa dificuldade, mas não garante que os grupos representem divisões verdadeiras.

## O que encontrei

Os números abaixo foram gerados por `analysis.py` ao baixar e processar o arquivo oficial da UCI em 23 de novembro de 2026. A maior *silhouette* entre os valores testados seleciona **k=2**, com silhouette **0,2903**. Calinski–Harabasz também atinge seu maior valor em `k=2` (**189,050**). Davies–Bouldin é um pouco menor em `k=3` (**1,3482**) do que em `k=2` (**1,3515**). Portanto, as medidas não apontam todas para a mesma quantidade de grupos; a silhouette, sozinha, não indica uma separação forte.

Na tabela, a seta para cima (↑) indica que valores maiores são preferidos; a seta para baixo (↓), que valores menores são preferidos. *Inertia* é a soma das distâncias dentro dos grupos.

| k (quantidade de grupos) | Inertia | Silhouette (↑) | Calinski–Harabasz (↑) | Davies–Bouldin (↓) |
|---:|---:|---:|---:|---:|
| 2 | 1844,064 | 0,2903 | 189,050 | 1,3515 |
| 3 | 1553,413 | 0,2583 | 152,837 | 1,3482 |
| 4 | 1386,863 | 0,1885 | 131,320 | 1,5408 |
| 5 | 1266,149 | 0,1916 | 118,000 | 1,4843 |
| 6 | 1174,536 | 0,1953 | 108,300 | 1,4135 |
| 7 | 1086,359 | 0,1958 | 103,208 | 1,3919 |
| 8 | 1024,047 | 0,1915 | 97,386 | 1,3855 |

Com dois grupos, a divisão reúne 252 observações (**57,3%**) no grupo 0 e 188 (**42,7%**) no grupo 1. A tabela mostra as medianas nas unidades monetárias originais:

| Grupo | n (% do total) | Fresh | Milk | Grocery | Frozen | Detergents_Paper | Delicassen |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 252 (57,3%) | 10.347,5 | 1.871,0 | 2.406,0 | 2.225,0 | 327,5 | 749,5 |
| 1 | 188 (42,7%) | 5.406,5 | 7.690,5 | 11.527,0 | 1.061,5 | 4.495,0 | 1.388,5 |

Como descrição dos dados, encontrei medianas maiores de `Fresh` e `Frozen` no grupo 0. No grupo 1, as medianas são maiores nas outras quatro categorias, com diferenças especialmente visíveis em `Milk`, `Grocery` e `Detergents_Paper`. Os números 0 e 1 são apenas identificadores atribuídos pelo K-Means, não nomes de tipos fixos de clientes.

Em dez tentativas independentes para `k=2`, a média, o menor e o maior ARI entre os 45 pares de divisões foram **1,0000**. Isso indica que as divisões concordaram entre essas tentativas, neste conjunto de dados e com esta configuração. Não confirma os grupos por comparação com uma classificação externa.

## O que aprendi

Aprendi que transformar valores muito diferentes antes de colocá-los em escalas comparáveis muda a forma como a semelhança entre observações é medida. Por isso, explico essas duas etapas junto com os resultados. Silhouette, Calinski–Harabasz e Davies–Bouldin observam aspectos diferentes dos grupos. Aqui, a regra definida antes da análise favorece `k=2`, mas a silhouette de 0,2903 e a pequena vantagem de Davies–Bouldin para `k=3` pedem cautela.

As medianas nos valores originais ajudam a descrever os grupos sem confundir as despesas com a escala usada no ajuste. A concordância entre sementes acrescenta uma informação sobre estabilidade, mas não substitui a comparação com uma classificação externa.

## Próximo projeto — 08-nlp-texto

Para o próximo projeto, levo a ideia de que, para comparar ou agrupar textos, também é preciso convertê-los em números. O próximo trabalho trata de texto; uma representação como TF-IDF (frequência do termo–frequência inversa nos documentos) atribui números às palavras levando em conta sua presença e relevância nos textos. A escolha das variáveis, a transformação e o ajuste de escala, a comparação de configurações e a conferência dos grupos com medidas internas são etapas úteis como referência. Ainda assim, os dados de texto têm distribuições e significados diferentes dos gastos, então não devo transferir automaticamente os parâmetros usados aqui.

## Como repetir a análise

Para repetir a análise, é necessário ter Python 3.10 ou mais recente e acesso à internet para obter o arquivo da UCI. Na pasta principal do projeto:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis.py
```

O primeiro comando cria um ambiente virtual, uma instalação separada de Python para este projeto. O comando de análise baixa o ZIP e o guarda em `data/`, pasta ignorada pelo Git. Para baixar de novo a cópia oficial em vez de usar o arquivo guardado, execute:

```bash
python analysis.py --refresh
```

A semente padrão é 42. Para usar outra, por exemplo, execute `python analysis.py --seed 7`. Os resultados deste README foram gerados com as opções padrão. O script avisa claramente e para se o formato, a quantidade de linhas ou as verificações básicas não corresponderem ao esperado. Assim, evita fazer uma análise diferente sem avisar.

## Limitações e aviso educacional

O conjunto é pequeno: tem 440 clientes. Não informa o período em que os gastos foram coletados nem qual moeda ou unidade representa `m.u.`. O resultado depende da transformação logarítmica, do ajuste de escala, da distância euclidiana (uma forma de medir a distância entre observações) e dos valores de `k` entre 2 e 8. Outras escolhas podem produzir grupos diferentes. O K-Means favorece grupos compactos segundo a forma de medir as distâncias escolhida e pode ser afetado por observações muito afastadas das demais.

As medidas internas não provam que existam grupos naturais nem que esses perfis também apareçam em outros distribuidores ou períodos. Como não há rótulos de referência, não medi a precisão por comparação com uma classificação externa. Os resultados não estimam impacto, causa e efeito, receita ou valor de negócio. Este material é educacional e não substitui uma conferência com contexto, dados adicionais e especialistas.

## Referências

[1]: https://archive.ics.uci.edu/dataset/292/wholesale+customers "UCI Machine Learning Repository: Wholesale customers"
[2]: https://archive.ics.uci.edu/static/public/292/wholesale+customers.zip "Arquivo de dados Wholesale customers no repositório oficial da UCI"
[3]: https://creativecommons.org/licenses/by/4.0/ "Creative Commons Attribution 4.0 International"
