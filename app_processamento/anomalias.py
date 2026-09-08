"""
Cálculo dos índices relativos de BPC (por CadÚnico e por PBF) e detecção de
"comportamentos diferentes" (municípios fora do padrão do seu porte).
"""

from __future__ import annotations

import re

import pandas as pd

LIMIAR_DESVIOS_PADRAO = 2.5


def carregar_faixas_porte(caminho_porte_pop_ibge: str) -> pd.DataFrame:
    """Lê o porte_pop_ibge.csv e devolve uma tabela com limites numéricos
    (minimo, maximo) por faixa, prontos para classificar uma população."""
    df = pd.read_csv(caminho_porte_pop_ibge, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]

    def _extrai_numeros(texto: str) -> list[int]:
        return [int(n.replace(".", "")) for n in re.findall(r"[\d.]+\d", texto)]

    minimos, maximos = [], []
    for faixa in df["Faixa Populacional"]:
        numeros = _extrai_numeros(faixa)
        baixa = faixa.lower()
        if "até" in baixa:
            minimos.append(0)
            maximos.append(numeros[0])
        elif "acima" in baixa:
            minimos.append(numeros[0] + 1)
            maximos.append(None)
        else:
            minimos.append(numeros[0])
            maximos.append(numeros[1])

    df["minimo"] = minimos
    df["maximo"] = maximos
    return df[["Porte da Cidade", "minimo", "maximo"]].rename(
        columns={"Porte da Cidade": "porte"}
    )


def classificar_porte(populacao: float, faixas: pd.DataFrame) -> str | None:
    if pd.isna(populacao):
        return None
    for _, faixa in faixas.iterrows():
        minimo = faixa["minimo"]
        maximo = faixa["maximo"]
        # `maximo` pode virar NaN (não None) quando a coluna é convertida
        # para float64 por misturar números com None — por isso usamos
        # pd.isna aqui em vez de "is None".
        if populacao >= minimo and (pd.isna(maximo) or populacao <= maximo):
            return faixa["porte"]
    return None


def _ultimo_valor_por_municipio(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    """Para cada município, pega a linha do mês mais recente disponível na
    janela já filtrada e devolve o Total de Beneficiários (PCD+Idosos)."""
    idx_ultimo_mes = df_filtrado.groupby("codigo_ibge_6")["data"].idxmax()
    ultimo = df_filtrado.loc[idx_ultimo_mes, ["codigo_ibge_6", "data", "total"]]
    return ultimo.rename(columns={"data": "data_referencia", "total": "bpc_atual"})


def calcular_indices(
    df_filtrado: pd.DataFrame,
    caminho_unidade: str,
    caminho_cadunico: str,
    caminho_porte_pop_ibge: str,
) -> pd.DataFrame:
    """Monta a tabela por município com os índices bpc/cadunico e bpc/pbf,
    o porte (faixa populacional do porte_pop_ibge.csv) e os z-scores dentro
    do respectivo porte."""

    ultimo = _ultimo_valor_por_municipio(df_filtrado)

    unidade = pd.read_csv(caminho_unidade, encoding="utf-8")
    unidade = unidade[
        [
            "codigo_ibge_6",
            "codigo_ibge_7",
            "municipio",
            "uf",
            "regiao",
            "mesorregiao",
            "populacao_censo_2022",
        ]
    ].copy()
    unidade["populacao_censo_2022"] = (
        unidade["populacao_censo_2022"].astype(str).str.replace(".", "", regex=False).astype(int)
    )

    cadunico = pd.read_csv(caminho_cadunico, encoding="utf-8")
    cadunico = cadunico.rename(columns={"codigo_municipio": "codigo_ibge_7"})[
        ["codigo_ibge_7", "cadunico", "bpc", "pbf"]
    ]

    tabela = ultimo.merge(unidade, on="codigo_ibge_6", how="left")
    tabela = tabela.merge(cadunico, on="codigo_ibge_7", how="left")

    faixas = carregar_faixas_porte(caminho_porte_pop_ibge)
    tabela["porte"] = tabela["populacao_censo_2022"].apply(
        lambda pop: classificar_porte(pop, faixas)
    )

    tabela["indice_bpc_cadunico"] = tabela["bpc_atual"] / tabela["cadunico"]
    tabela["indice_bpc_pbf"] = tabela["bpc_atual"] / tabela["pbf"]

    for coluna_indice in ("indice_bpc_cadunico", "indice_bpc_pbf"):
        media_porte = tabela.groupby("porte")[coluna_indice].transform("mean")
        desvio_porte = tabela.groupby("porte")[coluna_indice].transform("std")
        tabela[f"z_{coluna_indice}"] = (tabela[coluna_indice] - media_porte) / desvio_porte

    tabela["anomalia"] = (
        tabela["z_indice_bpc_cadunico"].abs().gt(LIMIAR_DESVIOS_PADRAO)
        | tabela["z_indice_bpc_pbf"].abs().gt(LIMIAR_DESVIOS_PADRAO)
    ).fillna(False)

    return tabela
