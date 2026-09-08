"""
Leitura robusta dos CSVs brutos exportados do portal Visdata3.

O mesmo relatório, baixado em datas diferentes, já apareceu em codificações
diferentes (utf-8 numa exportação, cp1252/latin-1 noutra) e os campos
numéricos vêm no formato brasileiro (ex.: "191.521,69" ou, para valores sem
casas decimais, simplesmente "58176"). Este módulo concentra esse tratamento
para não repetir em cada script.
"""

from __future__ import annotations

import glob
import os

import pandas as pd

COLUNAS_ESPERADAS = [
    "Código",
    "Unidade Territorial",
    "UF",
    "Referência",
    "Pessoas com Deficiência (PCD) beneficiárias do BPC",
    "Idosos beneficiários do BPC",
    "Valor Repassado a PCDs pelo BPC",
    "Valor Repassado a Idosos pelo BPC",
    "Total de Beneficiários do BPC",
    "Valor Total repassado ao BPC",
]

# Nomes curtos usados internamente pelo resto da aplicação.
RENOMEIA_COLUNAS = {
    "Código": "codigo_ibge_6",
    "Unidade Territorial": "municipio",
    "UF": "uf",
    "Referência": "referencia",
    "Pessoas com Deficiência (PCD) beneficiárias do BPC": "pcd",
    "Idosos beneficiários do BPC": "idosos",
    "Valor Repassado a PCDs pelo BPC": "valor_pcd",
    "Valor Repassado a Idosos pelo BPC": "valor_idosos",
    "Total de Beneficiários do BPC": "total",
    "Valor Total repassado ao BPC": "valor_total",
}

ENCODINGS_TENTATIVAS = ("utf-8", "cp1252", "latin-1")


def _numero_br_para_float(serie: pd.Series) -> pd.Series:
    """Converte texto em formato numérico brasileiro (ponto de milhar,
    vírgula decimal) para float. Tolera valores que já vieram sem separador
    de milhar e sem vírgula (inteiros "puros")."""
    texto = serie.astype(str).str.strip()
    texto = texto.str.replace(".", "", regex=False)
    texto = texto.str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce")


def localizar_arquivo_mais_recente(pasta: str = ".", padrao: str = "visdata3-download-*.csv") -> str:
    """Encontra, na pasta informada, o arquivo bruto do Visdata3 mais
    recente (maior data de modificação). Levanta erro se não achar nenhum."""
    candidatos = glob.glob(os.path.join(pasta, padrao))
    if not candidatos:
        raise FileNotFoundError(
            f"Nenhum arquivo casando com '{padrao}' encontrado em '{pasta}'."
        )
    return max(candidatos, key=os.path.getmtime)


def ler_visdata(caminho: str) -> pd.DataFrame:
    """Lê um CSV bruto do Visdata3 (uma linha por município por mês) e
    devolve um DataFrame já limpo, com colunas curtas e tipos corretos.

    Colunas do resultado:
        codigo_ibge_6, municipio, uf, referencia (str "MM/AAAA"),
        pcd, idosos, valor_pcd, valor_idosos, total, valor_total,
        mes (int), ano (int), data (Timestamp, dia 1 do mês)
    """
    ultimo_erro: Exception | None = None
    df = None
    for encoding in ENCODINGS_TENTATIVAS:
        try:
            df = pd.read_csv(caminho, encoding=encoding)
            break
        except UnicodeDecodeError as erro:
            ultimo_erro = erro
            continue
    if df is None:
        raise ValueError(
            f"Não foi possível ler '{caminho}' com nenhuma das codificações "
            f"tentadas {ENCODINGS_TENTATIVAS}."
        ) from ultimo_erro

    df.columns = [c.strip() for c in df.columns]
    faltando = set(COLUNAS_ESPERADAS) - set(df.columns)
    if faltando:
        raise ValueError(
            f"Arquivo '{caminho}' não tem as colunas esperadas do Visdata3: {faltando}"
        )

    df = df.rename(columns=RENOMEIA_COLUNAS)

    for col in ("pcd", "idosos", "total"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("valor_pcd", "valor_idosos", "valor_total"):
        df[col] = _numero_br_para_float(df[col])

    df["codigo_ibge_6"] = pd.to_numeric(df["codigo_ibge_6"], errors="coerce").astype("Int64")

    partes_data = df["referencia"].astype(str).str.split("/", expand=True)
    df["mes"] = pd.to_numeric(partes_data[0], errors="coerce").astype("Int64")
    df["ano"] = pd.to_numeric(partes_data[1], errors="coerce").astype("Int64")
    df["data"] = pd.to_datetime(
        dict(year=df["ano"], month=df["mes"], day=1), errors="coerce"
    )

    antes = len(df)
    df = df.dropna(subset=["codigo_ibge_6", "data", "pcd"]).copy()
    descartadas = antes - len(df)
    if descartadas:
        print(f"[leitura_visdata] {descartadas} linha(s) descartada(s) por dados inválidos/incompletos.")

    df["codigo_ibge_6"] = df["codigo_ibge_6"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df["ano"] = df["ano"].astype(int)

    return df.reset_index(drop=True)


def filtrar_ultimos_anos(df: pd.DataFrame, anos: int = 4) -> pd.DataFrame:
    """Mantém somente as linhas dentro da janela rolante dos últimos `anos`
    anos (48 meses, por padrão), contados a partir do mês mais recente
    presente no próprio arquivo — não da data do sistema."""
    data_maxima = df["data"].max()
    data_minima = data_maxima - pd.DateOffset(years=anos) + pd.DateOffset(months=1)
    filtrado = df[(df["data"] >= data_minima) & (df["data"] <= data_maxima)].copy()
    return filtrado.reset_index(drop=True)
