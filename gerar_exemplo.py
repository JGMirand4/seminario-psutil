#!/usr/bin/env python3
import numpy as np
import pandas as pd

FASES = [("repouso", 120, 4.0), ("cpu", 180, None), ("memoria", 180, 12.0), ("disco", 120, 15.0), ("fim", 120, 4.0)]


def gerar(nivel_cpu, semente):
    rng = np.random.default_rng(semente)
    linhas, t, ruido, mem = [], 0, 0.0, 8000.0
    for fase, dur, nivel in FASES:
        alvo = nivel_cpu if fase == "cpu" else nivel
        base = linhas[-1]["cpu_pct"] if linhas else 3.0
        for k in range(dur):
            ruido = 0.7 * ruido + rng.normal(0, 2.5)
            cpu = alvo + (base - alvo) * np.exp(-k / 8) + ruido
            mem = mem - 25 if fase == "memoria" else mem + (8000 - mem) * 0.1
            linhas.append({"t_s": t, "hora": "", "fase": fase, "cpu_pct": round(float(np.clip(cpu, 0, 100)), 2),
                           "mem_pct": round(100 - mem / 160, 1), "mem_disp_mb": round(mem, 1), "swap_pct": 0.0,
                           "disco_leit_mbs": 0.0, "disco_escr_mbs": round(float(rng.gamma(4, 20)) if fase == "disco" else 0.1, 2),
                           "rede_env_kbs": 1.0, "rede_rec_kbs": 2.0, "coletor_cpu_pct": 0.5, "coletor_rss_mb": 30.0})
            t += 1
    return pd.DataFrame(linhas)


if __name__ == "__main__":
    gerar(78, 1).to_csv("exemplo_A.csv", index=False)
    gerar(72, 2).to_csv("exemplo_B.csv", index=False)
    print("Criados exemplo_A.csv e exemplo_B.csv (dados simulados).")
