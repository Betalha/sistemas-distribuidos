"""Lê os CSVs do Locust e gera um gráfico por cenário e por eixo X em graficos/."""
import glob
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RESULTADOS = "locust/results/c*_i*_u*_stats.csv"
PASTA_SAIDA = "graficos"
CENARIOS = {1: "Imagem ~1MB", 2: "Texto ~400KB", 3: "Imagem ~300KB"}
METRICAS = {  # coluna -> título do gráfico
    "Average Response Time": "Tempo médio de resposta (ms)",
    "95%": "Percentil 95 (ms)",
    "Requests/s": "Requisições por segundo",
    "Falhas %": "Falhas (%)",
}
EIXOS = [  # (eixo X, uma linha por, rótulo do eixo X, rótulo da legenda)
    ("usuarios", "instancias", "Número de usuários", "instância(s)"),
    ("instancias", "usuarios", "Número de instâncias do WordPress", "usuários"),
]


def carregar_resultados():
    linhas = []
    for arquivo in glob.glob(RESULTADOS):
        c, i, u = map(int, re.search(r"c(\d+)_i(\d+)_u(\d+)_stats", arquivo).groups())
        total = pd.read_csv(arquivo).query("Name == 'Aggregated'").iloc[0]
        linhas.append({"cenario": c, "instancias": i, "usuarios": u, **total})
    df = pd.DataFrame(linhas)
    df["Falhas %"] = 100 * df["Failure Count"] / df["Request Count"].clip(lower=1)
    return df.sort_values(["cenario", "instancias", "usuarios"])


def plotar(df, cenario, eixo_x, serie, rotulo_x, rotulo_serie):
    dados = df[df.cenario == cenario]
    valores_x = sorted(dados[eixo_x].unique())
    fig, axs = plt.subplots(1, len(METRICAS), figsize=(18, 4.5))
    for ax, (coluna, titulo) in zip(axs, METRICAS.items()):
        for valor, grupo in dados.groupby(serie):
            ax.plot(grupo[eixo_x], grupo[coluna], marker="o", label=f"{valor} {rotulo_serie}")
        if eixo_x == "usuarios":
            ax.set_xscale("log")
        ax.set_xticks(valores_x, labels=valores_x)
        ax.set_title(titulo)
        ax.set_xlabel(rotulo_x)
        ax.grid(alpha=0.3)
        ax.legend()
    fig.suptitle(f"Cenário {cenario}: {CENARIOS[cenario]}")
    fig.tight_layout()
    fig.savefig(f"{PASTA_SAIDA}/cenario{cenario}_por_{eixo_x}.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    df = carregar_resultados()
    colunas = ["cenario", "instancias", "usuarios", "Request Count", *METRICAS]
    df[colunas].to_csv(f"{PASTA_SAIDA}/resumo.csv", index=False)
    for cenario in sorted(df.cenario.unique()):
        for eixo in EIXOS:
            plotar(df, cenario, *eixo)
    print(df[colunas].to_string(index=False))
