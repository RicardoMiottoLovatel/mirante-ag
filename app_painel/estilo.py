"""Paleta e CSS baseados na identidade visual do gov.br, injetados no painel."""

import streamlit as st

AZUL_GOVBR = "#1351B4"
AZUL_ESCURO_GOVBR = "#071D41"
AZUL_CLARO_GOVBR = "#5992ED"
AMARELO_GOVBR = "#FFCD07"
VERDE_GOVBR = "#168821"
CINZA_CLARO = "#F8F8F8"
CINZA_TEXTO = "#333333"

CSS = f"""
<style>
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }}
    #MainMenu, footer {{visibility: hidden;}}

    .cabecalho-mirante {{
        background: linear-gradient(90deg, {AZUL_ESCURO_GOVBR} 0%, {AZUL_GOVBR} 100%);
        padding: 1.2rem 1.6rem;
        border-radius: 8px;
        margin-bottom: 1.2rem;
        border-left: 8px solid {AMARELO_GOVBR};
    }}
    .cabecalho-mirante h1 {{
        color: white;
        margin: 0;
        font-size: 1.8rem;
    }}
    .cabecalho-mirante p {{
        color: {CINZA_CLARO};
        margin: 0.2rem 0 0 0;
        font-size: 0.95rem;
    }}

    div[data-testid="stMetric"] {{
        background-color: white;
        border: 1px solid #E0E0E0;
        border-top: 4px solid {AZUL_GOVBR};
        border-radius: 8px;
        padding: 0.8rem 1rem;
    }}

    section[data-testid="stSidebar"] {{
        border-right: 3px solid {AZUL_GOVBR};
    }}

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {{
        color: {AZUL_ESCURO_GOVBR} !important;
    }}
</style>
"""


def aplicar_estilo() -> None:
    st.set_page_config(
        page_title="Mirante Visdata",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(titulo: str, subtitulo: str) -> None:
    st.markdown(
        f"""
        <div class="cabecalho-mirante">
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
