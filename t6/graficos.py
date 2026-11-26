"""Lê resultados/<tec>_u<N>_stats.csv e gera tabela.csv + graficos/*.png. Check: python3 graficos.py --test"""
import re, sys, glob, os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = {"rest": "REST", "graphql": "GraphQL", "soap": "SOAP", "grpc": "gRPC"}
TECS = list(BASE) + ["java_" + t for t in BASE]
NOMES = {**{t: n + " (Python)" for t, n in BASE.items()}, **{"java_" + t: n + " (Java)" for t, n in BASE.items()}}


def carregar(pasta="resultados"):
    linhas = []
    for f in glob.glob(f"{pasta}/**/*_stats.csv", recursive=True):
        m = re.search(r"(\w+?)_u(\d+)_stats\.csv$", f)
        if not m:
            continue
        df = pd.read_csv(f)
        for _, r in df.iterrows():
            linhas.append({"tec": m[1], "rep": os.path.basename(os.path.dirname(f)), "usuarios": int(m[2]), "op": "TOTAL" if r["Name"] == "Aggregated" else r["Name"],
                           "reqs": r["Request Count"], "falhas": r["Failure Count"], "media_ms": r["Average Response Time"],
                           "p95_ms": r["95%"], "rps": r["Requests/s"], "bytes": r["Average Content Size"]})
    return pd.DataFrame(linhas)


def linha(df, col, titulo, ylabel, arq, logy=False):
    g = df[df.op == "TOTAL"].groupby(["usuarios", "tec"])[col]
    d = g.mean().unstack()[TECS].rename(columns=NOMES)
    e = g.std().unstack()[TECS].rename(columns=NOMES).fillna(0)  # desvio padrão entre repetições
    ax = d.plot.bar(figsize=(9, 4.2), logy=logy, rot=0, yerr=e, error_kw={"elinewidth": 1, "capsize": 1.5})
    ax.set_xlabel("usuários simultâneos"); ax.set_ylabel(ylabel); ax.set_title(titulo); ax.grid(axis="y", alpha=.3)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8)
    plt.tight_layout(); plt.savefig(f"graficos/{arq}.png", dpi=150); plt.close()


def barras_bytes(df, usuarios, arq="bytes_por_operacao"):
    d = df[(df.op != "TOTAL") & (df.usuarios == usuarios)].pivot_table(index="op", columns="tec", values="bytes")[TECS]
    d.columns = [NOMES[c] for c in d.columns]
    ax = d.plot.bar(figsize=(9, 4.5), logy=True)
    ax.set_ylabel("bytes médios por resposta (log)"); ax.set_xlabel(""); ax.set_title("Tamanho da resposta por operação")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1))
    plt.xticks(rotation=30, ha="right"); plt.tight_layout(); plt.savefig(f"graficos/{arq}.png", dpi=150); plt.close()


def main():
    os.makedirs("graficos", exist_ok=True)
    df = carregar()
    t = df[df.op == "TOTAL"].groupby(["usuarios", "tec"]).agg(
        reps=("rep", "nunique"), reqs=("reqs", "sum"), falhas=("falhas", "sum"), rps=("rps", "mean"), rps_dp=("rps", "std"),
        media_ms=("media_ms", "mean"), media_ms_dp=("media_ms", "std"), p95_ms=("p95_ms", "mean"), p95_ms_dp=("p95_ms", "std"),
        bytes=("bytes", "mean")).reset_index()
    t.assign(falhas_pct=100 * t.falhas / t.reqs).to_csv("tabela.csv", index=False, float_format="%.1f")
    print(t.to_string(index=False))
    linha(df, "rps", "Vazão (req/s) x carga", "requisições por segundo", "vazao")
    linha(df, "media_ms", "Tempo médio de resposta x carga", "ms (log)", "tempo_medio", logy=True)
    linha(df, "p95_ms", "Percentil 95 do tempo de resposta x carga", "ms (log)", "p95", logy=True)
    barras_bytes(df, int(df.usuarios.min()))


def teste():
    import tempfile
    d = tempfile.mkdtemp()
    cols = "Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,Min Response Time,Max Response Time,Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%"
    open(f"{d}/rest_u10_stats.csv", "w").write(cols + "\n,Aggregated,100,5,1,2.5,1,9,300,50.0,0,1,1,1,1,1,7,1,1,1,1,1\n"
                                                 "GET,x,100,5,1,2.5,1,9,300,50.0,0,1,1,1,1,1,7,1,1,1,1,1\n")
    r = carregar(d)
    a = r[r.op == "TOTAL"].iloc[0]
    assert (a.tec, a.usuarios, a.reqs, a.falhas, a.p95_ms, a.rps) == ("rest", 10, 100, 5, 7, 50.0), a
    assert len(r) == 2
    print("ok")


if __name__ == "__main__":
    teste() if "--test" in sys.argv else main()
