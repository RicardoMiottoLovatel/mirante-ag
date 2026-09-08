"""
Geração do relatório PDF mensal de "comportamentos diferentes" (anomalias)
nos índices bpc/CadÚnico e bpc/PBF, comparando cada município com os
demais do mesmo porte populacional.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

AZUL_GOVBR = colors.HexColor("#1351B4")
AZUL_ESCURO_GOVBR = colors.HexColor("#071D41")
AMARELO_GOVBR = colors.HexColor("#FFCD07")
CINZA_CLARO = colors.HexColor("#F8F8F8")


def _grafico_dispersao(tabela: pd.DataFrame, coluna_indice: str, titulo: str) -> Image:
    fig, eixo = plt.subplots(figsize=(16, 8))
    tabela = tabela.dropna(subset=["porte", coluna_indice])
    normais = tabela[~tabela["anomalia"]]
    anomalos = tabela[tabela["anomalia"]]

    portes = list(tabela["porte"].dropna().unique())
    posicoes = {porte: i for i, porte in enumerate(portes)}

    eixo.scatter(
        normais["porte"].map(posicoes),
        normais[coluna_indice],
        color="#5992ED",
        alpha=0.4,
        s=18,
        label="Dentro do padrão",
    )
    eixo.scatter(
        anomalos["porte"].map(posicoes),
        anomalos[coluna_indice],
        color="#C22E1B",
        s=40,
        label="Comportamento diferente",
    )
    eixo.set_xticks(list(posicoes.values()))
    eixo.set_xticklabels(list(posicoes.keys()), rotation=15)
    eixo.set_title(titulo)
    eixo.set_ylabel(coluna_indice)
    eixo.legend(loc="upper right")
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return Image(buffer, width=17 * cm, height=8.5 * cm)


def gerar_relatorio(
    tabela: pd.DataFrame,
    mes_referencia: str,
    caminho_saida: str,
) -> None:
    """Gera o PDF com o resumo e o detalhamento dos municípios com
    comportamento diferente do esperado para o seu porte."""

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloGovBr", parent=estilos["Title"], textColor=AZUL_ESCURO_GOVBR
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloGovBr", parent=estilos["Heading2"], textColor=AZUL_GOVBR
    )
    estilo_corpo = estilos["BodyText"]

    documento = SimpleDocTemplate(
        caminho_saida,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    elementos = []
    elementos.append(Paragraph("Mirante Visdata — Relatório de Comportamentos Diferentes", estilo_titulo))
    elementos.append(Paragraph(f"BPC — mês de referência analisado: {mes_referencia}", estilo_subtitulo))
    elementos.append(Spacer(1, 0.5 * cm))

    total_municipios = len(tabela)
    total_anomalos = int(tabela["anomalia"].sum())
    texto_resumo = (
        f"Foram analisados <b>{total_municipios}</b> municípios, comparando o número atual de "
        f"beneficiários do BPC com os inscritos no CadÚnico e no Bolsa Família (PBF), sempre "
        f"dentro do mesmo porte populacional (classificação do porte_pop_ibge.csv). "
        f"<b>{total_anomalos}</b> município(s) apresentaram índice a mais de "
        f"{2.5:.1f} desvios-padrão da média do seu porte em pelo menos um dos dois indicadores "
        f"— esses são os \"comportamentos diferentes\" listados abaixo."
    )
    elementos.append(Paragraph(texto_resumo, estilo_corpo))
    elementos.append(Spacer(1, 0.8 * cm))

    elementos.append(_grafico_dispersao(tabela, "indice_bpc_cadunico", "BPC / CadÚnico, por porte"))
    elementos.append(Spacer(1, 0.4 * cm))
    elementos.append(_grafico_dispersao(tabela, "indice_bpc_pbf", "BPC / PBF, por porte"))
    elementos.append(PageBreak())

    elementos.append(Paragraph("Municípios com comportamento diferente", estilo_subtitulo))
    elementos.append(Spacer(1, 0.3 * cm))

    anomalos = tabela[tabela["anomalia"]].copy()
    anomalos["desvio_maximo"] = anomalos[["z_indice_bpc_cadunico", "z_indice_bpc_pbf"]].abs().max(axis=1)
    anomalos = anomalos.sort_values("desvio_maximo", ascending=False)

    cabecalho = ["Município", "UF", "Porte", "BPC/CadÚnico", "z", "BPC/PBF", "z"]
    linhas = [cabecalho]
    for _, linha in anomalos.iterrows():
        linhas.append(
            [
                linha["municipio"],
                linha["uf"],
                linha["porte"],
                f"{linha['indice_bpc_cadunico']:.3f}",
                f"{linha['z_indice_bpc_cadunico']:.1f}",
                f"{linha['indice_bpc_pbf']:.3f}",
                f"{linha['z_indice_bpc_pbf']:.1f}",
            ]
        )

    if len(linhas) == 1:
        elementos.append(Paragraph("Nenhum município fora do padrão neste mês.", estilo_corpo))
    else:
        tabela_pdf = Table(linhas, repeatRows=1, hAlign="LEFT")
        tabela_pdf.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), AZUL_GOVBR),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elementos.append(tabela_pdf)

    documento.build(elementos)
