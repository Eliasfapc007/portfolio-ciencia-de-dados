# 06 — Séries temporais: previsão com dados ao longo do tempo

## Pergunta

Neste estudo, comparei duas regras simples para prever um mês à frente: repetir o último valor observado ou usar o valor do mesmo mês do ano anterior. Para isso, analisei as médias mensais de dióxido de carbono (CO₂) no ar medidas no Observatório de Mauna Loa. A comparação não busca explicar as causas das mudanças nem representar a concentração global.

## Dados, fonte e licença

Usei o conjunto **Carbon Dioxide monthly averages from Mauna Loa, Hawaii, United States**, mantido pelo Laboratório Global de Monitoramento da NOAA (NOAA Global Monitoring Laboratory, ou GML). A ficha oficial descreve medições *in situ* (feitas no próprio local), uma vez por mês. Ela informa que os dados cobrem janeiro de 1974 a dezembro de 2025 e oferece um arquivo de texto de cerca de 88 kB [1]. O script baixa o arquivo público indicado na ficha [2].

A página do conjunto informa a licença **CC0 1.0 Universal**. Isso significa que, nos Estados Unidos, a NOAA declara que o conjunto não tem proteção autoral e que, no mundo todo, dedica ou renuncia aos direitos autorais e direitos relacionados. A política de uso justo pede que a NOAA/GML receba crédito por meio de citação adequada [1]. O relatório e o código registram essa atribuição. Os dados originais não foram incluídos nos arquivos do projeto nem no histórico de alterações do código.

O cabeçalho do arquivo baixado traz a citação e a versão do conjunto. A fonte avisa que os valores podem ser corrigidos após verificações de qualidade e calibração — ajustes para manter as medições corretas. Portanto, os dados podem ser revisados [1] [3].

## O que fiz

O script lê o arquivo de texto usando ferramentas que já vêm com Python. Ele ignora as informações explicativas que aparecem antes do cabeçalho da tabela, lê o ano, o mês e a concentração em ppm (partes por milhão, uma unidade que expressa a quantidade de CO₂) e trata o marcador `-999.99` como informação ausente, não como medição. Não estima valores para preencher as lacunas. Também confere a ordem das datas e a existência de meses repetidos.

Como o arquivo tem meses ausentes, o script separa as observações em trechos de meses consecutivos e usa o trecho mais recente para comparar as previsões. Assim, nenhuma regra atravessa meses desconhecidos. Esse trecho contínuo tem 30 meses: os 12 primeiros servem de histórico, e os 18 meses finais formam o teste, usado para conferir o desempenho das previsões.

No teste, o script faz uma avaliação *walk-forward* (avaliação mês a mês, avançando no tempo) com previsão de um passo. Em cada mês, a primeira regra repete o último valor já observado; a regra sazonal usa o valor observado 12 meses antes, no mesmo mês do ano anterior. Nenhuma das duas usa o valor que está tentando prever ou informações do futuro. Depois de cada previsão, o valor real daquele mês fica disponível para prever o mês seguinte, como numa atualização mensal. Portanto, esse procedimento não mede uma previsão fixa de 18 meses feita no início do teste.

Para resumir os erros, o script calcula o MAE (erro absoluto médio: a média da distância entre cada previsão e o valor real) e o RMSE (raiz do erro quadrático médio: uma medida do tamanho dos erros que dá mais peso aos erros maiores). As duas métricas são expressas em ppm; números menores significam erros menores nesse trecho avaliado. As regras são comparadas com instruções fixas, sem ajustar opções para tentar alterar seu funcionamento.

## Dificuldade técnica observada

**Nível: intermediário.** O cabeçalho da tabela de texto aparece na linha 158, depois das informações explicativas. Na execução registrada, foram encontrados 12 marcadores de ausência `-999.99`: janeiro–abril de 1974, dezembro de 1975 e dezembro de 2022 a junho de 2023. O histórico da execução relata que uma primeira tentativa foi interrompida pela conferência de lacunas na sequência mensal. O tratamento usado para a comparação passa a considerar apenas o trecho consecutivo mais recente, sem estimar valores ausentes. Com isso, o histórico consecutivo disponível fica limitado a 30 meses e a comparação sazonal, a 18 meses de teste, após reservar os 12 meses necessários para a primeira comparação com o mesmo mês do ano anterior.

## O que encontrei

Os resultados abaixo foram observados na execução de `analysis.py` em 23/11/2026, após o download do arquivo NOAA de 87.824 bytes, com a versão `2026-08-11` indicada no próprio arquivo:

- O arquivo contém 624 linhas mensais, de janeiro de 1974 a dezembro de 2025. Excluídos os 12 marcadores de ausência, restam 612 medições válidas, de maio de 1974 a dezembro de 2025.
- O trecho contínuo mais recente reúne 30 meses, de julho de 2023 a dezembro de 2025. O histórico consecutivo termina em junho de 2024 (12 meses); o teste cobre julho de 2024 a dezembro de 2025 (18 meses).
- **Regra baseada no último mês:** MAE **1,2489 ppm**; RMSE **1,3776 ppm**.
- **Regra sazonal, baseada no mesmo mês do ano anterior:** MAE **3,0433 ppm**; RMSE **3,0968 ppm**.
- Neste teste, a regra baseada no último mês teve MAE menor do que a regra sazonal.

Esses números descrevem somente o trecho de teste e a versão do arquivo avaliados. Não demonstram impacto em atividades ou negócios nem mostram que uma coisa causou a outra.

## O que aprendi

Aprendi que embaralhar os dados numa divisão aleatória apaga a ordem dos meses e pode deixar informações futuras influenciarem a avaliação. Separar os dados pela ordem das datas e calcular cada previsão com informações anteriores evita esse vazamento. A comparação sazonal também mostra como confrontar uma regra simples com outra que considera a repetição anual, sem apresentar nenhuma delas como modelo avançado.

## Ponte para o próximo projeto

No próximo projeto, **07-clusterizacao**, a tarefa muda: em vez de prever valores futuros, vou agrupar observações parecidas. Levo daqui o cuidado de respeitar a estrutura dos dados e conferir as escolhas feitas. Neste estudo, a estrutura importante foi a ordem do tempo e a separação que impede o uso de informações futuras. Na clusterização, será preciso escolher quais informações usar para formar os grupos, como lidar com medidas em escalas diferentes e como avaliar os grupos sem tratá-los como respostas certas já conhecidas.

## Como reproduzir

Para reproduzir a análise, execute os comandos a partir da pasta principal do repositório clonado.  é necessário ter Python 3.9+ (uma versão da linguagem de programação Python) e acesso à internet na primeira execução. O projeto usa somente ferramentas que já vêm com Python.

```bash
cd 06-series-temporais
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./analysis.py
```

O script baixa o arquivo oficial para `data/raw/`, uma pasta ignorada pelo Git (ferramenta que registra alterações nos arquivos do projeto). Para executar sem internet usando a cópia já baixada, use `./analysis.py --offline`. O teste atual usa o máximo de 18 meses permitido pelo trecho contínuo mais recente e mantém os 12 meses anteriores como histórico para a comparação sazonal. Também é possível reduzir o período de teste com `./analysis.py --holdout-months 12`. Se for solicitada uma janela maior do que a sequência contínua permite, o script apresenta uma explicação de erro em vez de preencher as lacunas.

## Limites

Os dados vêm de uma única estação em grande altitude, em Mauna Loa, não de uma série mundial. A NOAA informa que eles representam as condições de fundo medidas no observatório e podem diferir da concentração média global na superfície [3]. O conjunto mensal foi processado e passou por controles da fonte; não são dados originais medidos hora a hora.

As lacunas de dezembro de 1975 e de dezembro de 2022 a junho de 2023 limitam o trecho contínuo mais recente. A análise reserva somente 12 meses de histórico consecutivo e testa 18 meses. Como a avaliação mês a mês usa os valores reais dos meses anteriores à medida que o teste avança, ela não mede uma previsão de longo prazo feita toda de uma vez, a partir de uma única data. Os erros dependem da versão dos dados e podem mudar quando a fonte fizer revisões. MAE e RMSE, sem comparar muitos períodos nem mostrar a incerteza, não provam que o desempenho será bom no futuro, com dados que ficaram fora do teste.

**Aviso educacional:** este exercício serve para aprender sobre avaliação que respeita a ordem do tempo e regras simples de comparação. Não use os resultados sozinhos para tomar decisões científicas, políticas ou operacionais.

## Referências

[1]: https://gml.noaa.gov/data/dataset.php?item=mlo-co2-observatory-monthly "NOAA GML dataset: Carbon Dioxide monthly averages from Mauna Loa"
[2]: https://gml.noaa.gov/aftp/data/trace_gases/co2/in-situ/surface/txt/co2_mlo_surface-insitu_1_ccgg_MonthlyData.txt "Arquivo mensal público NOAA GML"
[3]: https://gml.noaa.gov/ccgg/trends/ "NOAA GML: Trends in Atmospheric Carbon Dioxide"
