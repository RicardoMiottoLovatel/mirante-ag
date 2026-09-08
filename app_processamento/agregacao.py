"""
Agregação mensal → bpc_MMAAAA.csv

Reproduz exatamente a fórmula usada para gerar o bpc_052026.csv a partir do
bpc_2226.csv (validada em 5.571/5.571 municípios, 100% de acerto em todas as
colunas). O cálculo usa a coluna de PCD (Pessoas com Deficiência
beneficiárias do BPC) por município, dentro da janela de anos já filtrada
por `leitura_visdata.filtrar_ultimos_anos`.
"""

from __future__ import annotations

import pandas as pd

COLUNAS_SAIDA = [
    "Código IBGE",
    "Nome do Municipio",
    "uf",
    "maior_media_anual",
    "ano_maior_media",
    "maior_media_semestral",
    "semestre_maior_media",
    "maior_diferenca_entre_meses",
    "ano_maior_diferença_ano",
    "media_pessoas_geral",
    "max_valor",
    "min_valor",
]


def gerar_agregado(df: pd.DataFrame) -> pd.DataFrame:
    """Recebe o DataFrame já lido/filtrado (ver leitura_visdata.py) e
    devolve o agregado por município no mesmo formato do bpc_MMAAAA.csv."""

    df = df.copy()
    df["semestre"] = df["mes"].apply(lambda m: "S1" if m <= 6 else "S2")
    df["ano_semestre"] = df["ano"].astype(str) + "_" + df["semestre"]

    linhas = []
    for codigo, grupo in df.groupby("codigo_ibge_6", sort=False):
        serie_pcd = grupo["pcd"]

        media_por_ano = grupo.groupby("ano")["pcd"].mean()
        media_por_semestre = grupo.groupby("ano_semestre")["pcd"].mean()
        amplitude_por_ano = grupo.groupby("ano")["pcd"].agg(lambda s: s.max() - s.min())

        linhas.append(
            {
                "Código IBGE": codigo,
                "Nome do Municipio": grupo["municipio"].iloc[0],
                "uf": grupo["uf"].iloc[0],
                "maior_media_anual": round(media_por_ano.max(), 2),
                "ano_maior_media": int(media_por_ano.idxmax()),
                "maior_media_semestral": round(media_por_semestre.max(), 2),
                "semestre_maior_media": media_por_semestre.idxmax(),
                "maior_diferenca_entre_meses": int(amplitude_por_ano.max()),
                "ano_maior_diferença_ano": int(amplitude_por_ano.idxmax()),
                "media_pessoas_geral": round(serie_pcd.mean(), 2),
                "max_valor": int(serie_pcd.max()),
                "min_valor": int(serie_pcd.min()),
            }
        )

    agregado = pd.DataFrame(linhas, columns=COLUNAS_SAIDA)
    agregado = agregado.sort_values("maior_media_anual", ascending=False).reset_index(drop=True)
    return agregado
