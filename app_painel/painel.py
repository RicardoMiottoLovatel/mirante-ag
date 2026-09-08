"""
App 2 — Painel Mirante Visdata (Streamlit).

Lê os arquivos bpc_MMAAAA.csv arquivados pela App 1 e apresenta os dados
com filtros em cascata (Região → UF → Mesorregião → Município, mais Porte),
construídos a partir do unidade_mirante_porte_pop_renomeado.csv e do
porte_pop_ibge.csv.

Uso:
    streamlit run painel.py
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estilo import aplicar_estilo, cabecalho  # noqa: E402
from filtros import (  # noqa: E402
    aplicar_porte,
    carregar_bpc_mensal,
    carregar_faixas_porte,
    carregar_unidade,
    filtrar_unidade,
    listar_arquivos_bpc_mensal,
    opcoes_mesorregiao,
    opcoes_municipio,
    opcoes_regiao,
    opcoes_uf,
    ordem_portes,
)

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_UNIDADE = os.path.join(RAIZ_PROJETO, "unidade_mirante_porte_pop_renomeado.csv")
CAMINHO_PORTE_IBGE = os.path.join(RAIZ_PROJETO, "porte_pop_ibge.csv")
PASTA_BPC_MENSAL = os.path.join(RAIZ_PROJETO, "bpc_mensal")


def main() -> None:
    aplicar_estilo()
    cabecalho(
        "Mirante Visdata",
        "Painel de acompanhamento do BPC por município — Benefício de Prestação Continuada",
    )

    arquivos_disponiveis = listar_arquivos_bpc_mensal(PASTA_BPC_MENSAL)
    if not arquivos_disponiveis:
        st.error(
            "Nenhum arquivo bpc_MMAAAA.csv encontrado em "
            f"'{PASTA_BPC_MENSAL}'. Rode a App 1 (processar_bpc.py) primeiro."
        )
        st.stop()

    unidade = carregar_unidade(CAMINHO_UNIDADE)
    faixas_porte = carregar_faixas_porte(CAMINHO_PORTE_IBGE)
    unidade = aplicar_porte(unidade, faixas_porte)
    portes_em_ordem = ordem_portes(faixas_porte)

    with st.sidebar:
        st.markdown("### Mês de referência")
        rotulos = [rotulo for rotulo, _ in arquivos_disponiveis]
        rotulo_escolhido = st.selectbox("Arquivo bpc_MMAAAA.csv", rotulos, index=0)
        caminho_bpc = dict(arquivos_disponiveis)[rotulo_escolhido]

        st.markdown("### Filtros")
        regioes = st.multiselect("Região", opcoes_regiao(unidade))
        ufs = st.multiselect("UF", opcoes_uf(unidade, regioes))
        mesorregioes = st.multiselect("Mesorregião", opcoes_mesorregiao(unidade, regioes, ufs))
        municipios = st.multiselect("Município", opcoes_municipio(unidade, regioes, ufs, mesorregioes))
        portes = st.multiselect("Porte", [p for p in portes_em_ordem if p in unidade["porte"].unique()])

    unidade_filtrada = filtrar_unidade(unidade, regioes, ufs, mesorregioes, municipios, portes)

    municipios_selecionados = len(unidade_filtrada)
    populacao_total = int(unidade_filtrada["populacao_censo_2022"].sum())
    ufs_selecionadas = unidade_filtrada["uf"].nunique()

    col_1, col_2, col_3 = st.columns(3)
    col_1.metric("Municípios Selecionados", f"{municipios_selecionados:,}".replace(",", "."))
    col_2.metric("População Total", f"{populacao_total:,}".replace(",", "."))
    col_3.metric("Unidades Federativas selecionadas", ufs_selecionadas)

    st.divider()

    bpc = carregar_bpc_mensal(caminho_bpc)
    dados = unidade_filtrada.merge(bpc, on="codigo_ibge_6", how="inner")

    if dados.empty:
        st.warning("Nenhum município encontrado para os filtros selecionados.")
        st.stop()

    aba_tabela, aba_graficos = st.tabs(["Tabela", "Gráficos"])

    with aba_tabela:
        colunas_exibicao = [
            "municipio",
            "uf",
            "regiao",
            "mesorregiao",
            "porte",
            "populacao_censo_2022",
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
        st.dataframe(
            dados[colunas_exibicao].sort_values("maior_media_anual", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with aba_graficos:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Top 15 municípios — maior média anual de BPC (PCD)**")
            top15 = dados.nlargest(15, "maior_media_anual").set_index("municipio")["maior_media_anual"]
            st.bar_chart(top15)
        with col_b:
            st.markdown("**Municípios por porte**")
            distrib_porte = dados["porte"].value_counts().reindex(portes_em_ordem).dropna()
            st.bar_chart(distrib_porte)


if __name__ == "__main__":
    main()
