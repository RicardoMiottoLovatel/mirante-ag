# Mirante Visdata

Duas aplicações Python para acompanhar o BPC (Benefício de Prestação Continuada) por município, a partir dos dados públicos do portal Visdata3 (Rede SUAS).

## Estrutura

```
mirante-ag/
  app_processamento/          # App 1 — processa o download mensal do Visdata3
    processar_bpc.py           # ponto de entrada
    leitura_visdata.py         # leitura robusta do CSV bruto (encoding + números BR)
    agregacao.py               # fórmula validada que gera as estatísticas por município
    anomalias.py                # índices relativos (bpc/CadÚnico, bpc/PBF) + detecção de outliers
    relatorio_pdf.py            # geração do relatório PDF de "comportamentos diferentes"
  app_painel/                  # App 2 — painel Streamlit "Mirante Visdata"
    painel.py                   # ponto de entrada (streamlit run painel.py)
    filtros.py                  # filtros em cascata (Região→UF→Mesorregião→Município, Porte)
    estilo.py                   # paleta gov.br + layout wide
  bpc_mensal/                  # saída da App 1: bpc_MMAAAA.csv arquivados (1 por mês)
  relatorios_anomalias/        # saída da App 1: relatorio_anomalias_MMAAAA.pdf arquivados
  unidade_mirante_porte_pop_renomeado.csv   # referência fixa de município/UF/região/mesorregião/população
  porte_pop_ibge.csv                        # faixas de porte por população (4 categorias)
  cadunico_bpc_pbf_2024.csv                 # inscritos no CadÚnico e no PBF por município (foto 2024)
```

## Instalação

```
pip install -r requirements.txt
```

## App 1 — processamento mensal

Todo mês, baixe o CSV atualizado do Visdata3 (formato: `Código, Unidade Territorial, UF,
Referência, Pessoas com Deficiência (PCD) beneficiárias do BPC, Idosos beneficiários do
BPC, Valor Repassado a PCDs pelo BPC, Valor Repassado a Idosos pelo BPC, Total de
Beneficiários do BPC, Valor Total repassado ao BPC`) para a raiz do projeto e rode:

```
python app_processamento/processar_bpc.py
```

Sem argumentos, o script usa automaticamente o arquivo `visdata3-download-*.csv` mais
recente da pasta. Isso gera:

- `bpc_mensal/bpc_MMAAAA.csv` — agregado por município, considerando os últimos 4 anos de
  dados (`MM/AAAA` = mês/ano em que o script rodou).
- `relatorios_anomalias/relatorio_anomalias_MMAAAA.pdf` — municípios cujo número atual de
  beneficiários do BPC, em relação aos inscritos no CadÚnico e no Bolsa Família, foge do
  padrão dos municípios do mesmo porte.

## App 2 — painel Streamlit

```
streamlit run app_painel/painel.py
```

Abre o painel "Mirante Visdata": seletor de mês/ano (lendo os arquivos arquivados em
`bpc_mensal/`), filtros em cascata na barra lateral e indicadores de Municípios
Selecionados / População Total / UFs selecionadas no cabeçalho.
