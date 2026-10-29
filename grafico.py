#!/usr/bin/env python3
import argparse

import matplotlib

import pandas as pd

CORES = {"repouso": "#d9d5c9", "cpu": "#f4c7a1", "memoria": "#a9d1e0", "disco": "#c9e3b4", "fim": "#e6d3ee"}
PAINEIS = [("cpu_pct", "CPU (%)"), ("mem_disp_mb", "Memória disponível (MB)"),
           ("disco_escr_mbs", "Escrita em disco (MB/s)"), ("coletor_cpu_pct", "CPU do próprio coletor (%)")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--salvar", help="salva em PNG em vez de abrir a janela")
    a = ap.parse_args()
    if a.salvar:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = pd.read_csv(a.csv)
    fig, eixos = plt.subplots(len(PAINEIS), 1, figsize=(12, 8), sharex=True)
    grupo = (df["fase"] != df["fase"].shift()).cumsum()
    for ax, (col, rotulo) in zip(eixos, PAINEIS):
        for _, g in df.groupby(grupo):
            fase = g["fase"].iloc[0]
            ax.axvspan(g["t_s"].iloc[0], g["t_s"].iloc[-1], color=CORES.get(fase, "#ffffff"), alpha=0.6, lw=0)
        ax.plot(df["t_s"], df[col], lw=1.2, color="#16222c")
        ax.set_ylabel(rotulo, fontsize=9)
    for _, g in df.groupby(grupo):
        fase = g["fase"].iloc[0]
        if fase != "-":
            eixos[0].text((g["t_s"].iloc[0] + g["t_s"].iloc[-1]) / 2, eixos[0].get_ylim()[1], fase,
                          ha="center", va="bottom", fontsize=9)
    eixos[-1].set_xlabel("tempo (s)")
    fig.tight_layout()
    if a.salvar:
        fig.savefig(a.salvar, dpi=130)
        print("Salvo em", a.salvar)
    else:
        plt.show()


if __name__ == "__main__":
    main()
