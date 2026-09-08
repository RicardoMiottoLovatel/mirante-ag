"""
App 1 — Processamento mensal do BPC.

Lê o download mais recente do Visdata3, filtra os últimos 4 anos, gera:
  - bpc_mensal/bpc_MMAAAA.csv        (agregado por município)
  - relatorios_anomalias/relatorio_anomalias_MMAAAA.pdf  (comportamentos diferentes)

onde MM/AAAA é o mês/ano em que este script está sendo executado.

Uso:
    python processar_bpc.py [caminho_do_csv_bruto]

Se `caminho_do_csv_bruto` não for informado, usa o arquivo mais recente que
casar com "visdata3-download-*.csv" na raiz do projeto.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys

RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agregacao import gerar_agregado  # noqa: E402
from anomalias import calcular_indices  # noqa: E402
from leitura_visdata import (  # noqa: E402
    filtrar_ultimos_anos,
    ler_visdata,
    localizar_arquivo_mais_recente,
)
from relatorio_pdf import gerar_relatorio  # noqa: E402

CAMINHO_UNIDADE = os.path.join(RAIZ_PROJETO, "unidade_mirante_porte_pop_renomeado.csv")
CAMINHO_CADUNICO = os.path.join(RAIZ_PROJETO, "cadunico_bpc_pbf_2024.csv")
CAMINHO_PORTE_IBGE = os.path.join(RAIZ_PROJETO, "porte_pop_ibge.csv")
PASTA_BPC_MENSAL = os.path.join(RAIZ_PROJETO, "bpc_mensal")
PASTA_RELATORIOS = os.path.join(RAIZ_PROJETO, "relatorios_anomalias")


def main() -> None:
    parser = argparse.ArgumentParser(description="Processa o download mensal do Visdata3.")
    parser.add_argument(
        "caminho_bruto",
        nargs="?",
        default=None,
        help="Caminho do CSV bruto do Visdata3. Se omitido, usa o mais recente na raiz do projeto.",
    )
    parser.add_argument(
        "--anos-janela",
        type=int,
        default=4,
        help="Quantidade de anos (janela rolante) a considerar. Padrão: 4.",
    )
    argumentos = parser.parse_args()

    caminho_bruto = argumentos.caminho_bruto or localizar_arquivo_mais_recente(RAIZ_PROJETO)
    print(f"[processar_bpc] Lendo arquivo bruto: {caminho_bruto}")

    df = ler_visdata(caminho_bruto)
    print(f"[processar_bpc] {len(df)} linhas lidas, {df['codigo_ibge_6'].nunique()} municípios.")

    df_janela = filtrar_ultimos_anos(df, anos=argumentos.anos_janela)
    data_min = df_janela["data"].min().strftime("%m/%Y")
    data_max = df_janela["data"].max().strftime("%m/%Y")
    print(f"[processar_bpc] Janela de {argumentos.anos_janela} anos: {data_min} a {data_max}.")

    agregado = gerar_agregado(df_janela)

    os.makedirs(PASTA_BPC_MENSAL, exist_ok=True)
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)

    hoje = datetime.date.today()
    sufixo_mes_ano = f"{hoje.month:02d}{hoje.year}"

    caminho_csv_saida = os.path.join(PASTA_BPC_MENSAL, f"bpc_{sufixo_mes_ano}.csv")
    agregado.to_csv(caminho_csv_saida, index=False, encoding="utf-8")
    print(f"[processar_bpc] Agregado salvo em: {caminho_csv_saida}")

    tabela_indices = calcular_indices(
        df_janela,
        caminho_unidade=CAMINHO_UNIDADE,
        caminho_cadunico=CAMINHO_CADUNICO,
        caminho_porte_pop_ibge=CAMINHO_PORTE_IBGE,
    )
    caminho_pdf_saida = os.path.join(PASTA_RELATORIOS, f"relatorio_anomalias_{sufixo_mes_ano}.pdf")
    gerar_relatorio(tabela_indices, mes_referencia=data_max, caminho_saida=caminho_pdf_saida)
    print(f"[processar_bpc] Relatório de anomalias salvo em: {caminho_pdf_saida}")

    print("[processar_bpc] Concluído.")


if __name__ == "__main__":
    main()
