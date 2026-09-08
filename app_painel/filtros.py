"""
Carregamento dos dados de referência e lógica dos filtros em cascata do
painel Mirante Visdata (Região → UF → Mesorregião → Município, mais Porte).

Este módulo é autossuficiente (não depende de app_processamento) para que a
App 2 possa ser publicada/rodada sozinha.
"""

from __future__ import annotations

import glob
import os
import re

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Referência de município (unidade_mirante_porte_pop_renomeado.csv)
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def carregar_unidade(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho, encoding="utf-8")
    df["populacao_censo_2022"] = (
        df["populacao_censo_2022"].astype(str).str.replace(".", "", regex=False).astype(int)
    )
    return df


# ---------------------------------------------------------------------------
# Porte por faixa populacional (porte_pop_ibge.csv) — recorte independente
# do porte_pop_categoria/porte_pop_codigo já presente no arquivo de unidade.
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def carregar_faixas_porte(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho, encoding="utf-8")
    df.columns = [c.strip() for c in df.columns]

    def _extrai_numeros(texto: str) -> list[int]:
        return [int(n.replace(".", "")) for n in re.findall(r"[\d.]+\d", texto)]

    minimos: list[int] = []
    maximos: list[float | None] = []
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
    return df[["Porte da Cidade", "minimo", "maximo"]].rename(columns={"Porte da Cidade": "porte"})


def classificar_porte(populacao: float, faixas: pd.DataFrame) -> str | None:
    if pd.isna(populacao):
        return None
    for _, faixa in faixas.iterrows():
        if populacao >= faixa["minimo"] and (pd.isna(faixa["maximo"]) or populacao <= faixa["maximo"]):
            return faixa["porte"]
    return None


def aplicar_porte(unidade: pd.DataFrame, faixas: pd.DataFrame) -> pd.DataFrame:
    unidade = unidade.copy()
    unidade["porte"] = unidade["populacao_censo_2022"].apply(lambda pop: classificar_porte(pop, faixas))
    return unidade


def ordem_portes(faixas: pd.DataFrame) -> list[str]:
    """Ordem "do menor pro maior" porte, na ordem em que aparecem no
    porte_pop_ibge.csv (já é essa a ordem no arquivo)."""
    return list(faixas["porte"])


# ---------------------------------------------------------------------------
# Arquivos bpc_MMAAAA.csv arquivados
# ---------------------------------------------------------------------------


def listar_arquivos_bpc_mensal(pasta: str) -> list[tuple[str, str]]:
    """Devolve [(rótulo "MM/AAAA", caminho)], do mais recente pro mais antigo."""
    caminhos = glob.glob(os.path.join(pasta, "bpc_*.csv"))
    itens = []
    for caminho in caminhos:
        nome = os.path.splitext(os.path.basename(caminho))[0]
        digitos = re.sub(r"\D", "", nome)
        if len(digitos) != 6:
            continue
        mes, ano = digitos[:2], digitos[2:]
        itens.append((f"{mes}/{ano}", caminho, ano + mes))
    itens.sort(key=lambda item: item[2], reverse=True)
    return [(rotulo, caminho) for rotulo, caminho, _ in itens]


@st.cache_data(show_spinner=False)
def carregar_bpc_mensal(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho, encoding="utf-8")
    df = df.rename(columns={"Código IBGE": "codigo_ibge_6"})
    # "Nome do Municipio" e "uf" já vêm do unidade_mirante_porte_pop_renomeado.csv
    # (colunas "municipio" e "uf") — descartar aqui evita colisão de nomes no merge.
    df = df.drop(columns=["Nome do Municipio", "uf"], errors="ignore")
    return df


# ---------------------------------------------------------------------------
# Opções em cascata para os seletores da barra lateral
# ---------------------------------------------------------------------------


def opcoes_regiao(unidade: pd.DataFrame) -> list[str]:
    return sorted(unidade["regiao"].dropna().unique())


def opcoes_uf(unidade: pd.DataFrame, regioes: list[str]) -> list[str]:
    dados = unidade if not regioes else unidade[unidade["regiao"].isin(regioes)]
    return sorted(dados["uf"].dropna().unique())


def opcoes_mesorregiao(unidade: pd.DataFrame, regioes: list[str], ufs: list[str]) -> list[str]:
    dados = unidade
    if regioes:
        dados = dados[dados["regiao"].isin(regioes)]
    if ufs:
        dados = dados[dados["uf"].isin(ufs)]
    return sorted(dados["mesorregiao"].dropna().unique())


def opcoes_municipio(
    unidade: pd.DataFrame, regioes: list[str], ufs: list[str], mesorregioes: list[str]
) -> list[str]:
    dados = unidade
    if regioes:
        dados = dados[dados["regiao"].isin(regioes)]
    if ufs:
        dados = dados[dados["uf"].isin(ufs)]
    if mesorregioes:
        dados = dados[dados["mesorregiao"].isin(mesorregioes)]
    return sorted(dados["municipio"].dropna().unique())


def filtrar_unidade(
    unidade: pd.DataFrame,
    regioes: list[str],
    ufs: list[str],
    mesorregioes: list[str],
    municipios: list[str],
    portes: list[str],
) -> pd.DataFrame:
    dados = unidade
    if regioes:
        dados = dados[dados["regiao"].isin(regioes)]
    if ufs:
        dados = dados[dados["uf"].isin(ufs)]
    if mesorregioes:
        dados = dados[dados["mesorregiao"].isin(mesorregioes)]
    if municipios:
        dados = dados[dados["municipio"].isin(municipios)]
    if portes:
        dados = dados[dados["porte"].isin(portes)]
    return dados
