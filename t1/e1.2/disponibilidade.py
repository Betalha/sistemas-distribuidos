import csv, random
from math import comb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NS = [10, 50, 100, 200]
PS = [i / 20 for i in range(21)]
RODADAS = [10, 50, 200]              
SEED = 42
ARQ_CSV = "resultados.csv"
ARQ_ANALITICO = "grafico_analitico.png"
ARQ_COMPARATIVO = "grafico_comparativo.png"
CABECALHO = ["rodadas", "n", "k", "caso", "p", "analitico", "simulado", "erro_abs"]
CORES = ["C0", "C1", "C2"]
LARGURA_POR_N, ALTURA = 4, 3.6
DPI = 120

def disponibilidade(n, k, p):
    if not (n > 0 and 0 < k <= n and 0.0 <= p <= 1.0):
        raise ValueError(f"parametros invalidos: n={n}, k={k}, p={p}")
    return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

def simular(n, k, p, rodadas=10, rng=random.Random(SEED)):
    ok = sum(1 for _ in range(rodadas)
             if sum(1 for _ in range(n) if rng.random() <= p) >= k)
    return ok / rodadas

def ks(n):
    return sorted({1: "k=1", max(1, -(-n // 2)): "k=n/2", n: "k=n"}.items())

def main():
    linhas = []
    for r in RODADAS:
        for n in NS:
            for k, rot in ks(n):
                for p in PS:
                    a = disponibilidade(n, k, p)
                    s = simular(n, k, p, r)
                    linhas.append([r, n, k, rot, round(p, 3), round(a, 6),
                                   round(s, 6), round(abs(a - s), 6)])

    with open(ARQ_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(CABECALHO)
        w.writerows(linhas)
    fig, axes = plt.subplots(1, len(NS), figsize=(LARGURA_POR_N * len(NS), ALTURA), sharey=True)
    for ax, n in zip(axes, NS):
        for k, rot in ks(n):
            ax.plot(PS, [disponibilidade(n, k, p) for p in PS], label=f"{rot} (k={k})")
        ax.set_title(f"n = {n}"); ax.set_xlabel("p"); ax.grid(alpha=.3); ax.legend()
    axes[0].set_ylabel("Disponibilidade")
    fig.suptitle("Disponibilidade analítica A(n,k,p)")
    fig.tight_layout(); fig.savefig(ARQ_ANALITICO, dpi=DPI)

    fig, grade = plt.subplots(len(RODADAS), len(NS), squeeze=False, sharey=True,
                              figsize=(LARGURA_POR_N * len(NS), ALTURA * len(RODADAS)))
    for r, axes in zip(RODADAS, grade):
        for ax, n in zip(axes, NS):
            for (k, rot), cor in zip(ks(n), CORES):
                ax.plot(PS, [disponibilidade(n, k, p) for p in PS], cor, label=f"{rot} analítico")
                sim = [l[6] for l in linhas if l[:3] == [r, n, k]]
                ax.plot(PS, sim, "o", color=cor, ms=3, alpha=.6, label=f"{rot} simulado")
            ax.set_title(f"n = {n}, {r} rodadas"); ax.set_xlabel("p"); ax.grid(alpha=.3)
            ax.legend(fontsize=7)
        axes[0].set_ylabel("Disponibilidade")
    fig.suptitle("Analítico vs. simulado por número de rodadas")
    fig.tight_layout(); fig.savefig(ARQ_COMPARATIVO, dpi=DPI)

    print(f"{len(linhas)} linhas -> {ARQ_CSV}")
    for r in RODADAS:
        erro = max(l[7] for l in linhas if l[0] == r)
        print(f"  {r:>5} rodadas: erro máx. analítico-simulado = {erro:.4f}")

def demo():
    assert disponibilidade(1, 1, 0.9) == 0.9
    assert abs(disponibilidade(5, 1, 0.5) - (1 - 0.5**5)) < 1e-12   # k=1
    assert abs(disponibilidade(5, 5, 0.5) - 0.5**5) < 1e-12          # k=n
    assert disponibilidade(4, 2, 0.0) == 0.0 and disponibilidade(4, 2, 1.0) == 1.0
    assert abs(simular(5, 3, 0.7, 50_000) - disponibilidade(5, 3, 0.7)) < 0.01
    print("ok")

if __name__ == "__main__":
    demo(); main()
