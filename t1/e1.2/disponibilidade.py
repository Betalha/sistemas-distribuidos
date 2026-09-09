import csv, random
from math import comb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def disponibilidade(n, k, p):
    if not (n > 0 and 0 < k <= n and 0.0 <= p <= 1.0):
        raise ValueError(f"parametros invalidos: n={n}, k={k}, p={p}")
    return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

def simular(n, k, p, rodadas=100_000, rng=random.Random(42)):
    ok = sum(1 for _ in range(rodadas)
             if sum(1 for _ in range(n) if rng.random() <= p) >= k)
    return ok / rodadas

def ks(n):
    return sorted({1: "k=1", max(1, -(-n // 2)): "k=n/2", n: "k=n"}.items())

def main():
    ns = [1, 3, 5, 10]
    ps = [i / 20 for i in range(21)]
    linhas = []
    for n in ns:
        for k, rot in ks(n):
            for p in ps:
                a = disponibilidade(n, k, p)
                s = simular(n, k, p, 20_000)
                linhas.append([n, k, rot, round(p, 3), round(a, 6),
                               round(s, 6), round(abs(a - s), 6)])

    with open("resultados.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "k", "caso", "p", "analitico", "simulado", "erro_abs"])
        w.writerows(linhas)
    fig, axes = plt.subplots(1, len(ns), figsize=(4 * len(ns), 3.6), sharey=True)
    for ax, n in zip(axes, ns):
        for k, rot in ks(n):
            ax.plot(ps, [disponibilidade(n, k, p) for p in ps], label=f"{rot} (k={k})")
        ax.set_title(f"n = {n}"); ax.set_xlabel("p"); ax.grid(alpha=.3); ax.legend()
    axes[0].set_ylabel("Disponibilidade")
    fig.suptitle("Disponibilidade analítica A(n,k,p)")
    fig.tight_layout(); fig.savefig("grafico_analitico.png", dpi=120)

    fig, axes = plt.subplots(1, len(ns), figsize=(4 * len(ns), 3.6), sharey=True)
    for ax, n in zip(axes, ns):
        for (k, rot), cor in zip(ks(n), ["C0", "C1", "C2"]):
            ax.plot(ps, [disponibilidade(n, k, p) for p in ps], cor, label=f"{rot} analítico")
            sim = [l[5] for l in linhas if l[0] == n and l[1] == k]
            ax.plot(ps, sim, "o", color=cor, ms=3, alpha=.6, label=f"{rot} simulado")
        ax.set_title(f"n = {n}"); ax.set_xlabel("p"); ax.grid(alpha=.3); ax.legend(fontsize=7)
    axes[0].set_ylabel("Disponibilidade")
    fig.suptitle("Analítico vs. simulado (20.000 rodadas por ponto)")
    fig.tight_layout(); fig.savefig("grafico_comparativo.png", dpi=120)

    erro = max(l[6] for l in linhas)
    print(f"{len(linhas)} linhas -> resultados.csv | erro máx. analítico-simulado: {erro:.4f}")

def demo():
    assert disponibilidade(1, 1, 0.9) == 0.9
    assert abs(disponibilidade(5, 1, 0.5) - (1 - 0.5**5)) < 1e-12   # k=1
    assert abs(disponibilidade(5, 5, 0.5) - 0.5**5) < 1e-12          # k=n
    assert disponibilidade(4, 2, 0.0) == 0.0 and disponibilidade(4, 2, 1.0) == 1.0
    assert abs(simular(5, 3, 0.7, 50_000) - disponibilidade(5, 3, 0.7)) < 0.01
    print("ok")

if __name__ == "__main__":
    demo(); main()
