#!/usr/bin/env python3
import argparse
import csv
import time
from datetime import datetime

import psutil

MB = 1024 ** 2
COLUNAS = ["t_s", "hora", "fase", "cpu_pct", "mem_pct", "mem_disp_mb", "swap_pct",
           "disco_leit_mbs", "disco_escr_mbs", "rede_env_kbs", "rede_rec_kbs",
           "coletor_cpu_pct", "coletor_rss_mb"]


def ler_fase(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            return f.read().strip() or "-"
    except OSError:
        return "-"


def contadores():
    d = psutil.disk_io_counters()
    n = psutil.net_io_counters()
    return (d.read_bytes if d else 0, d.write_bytes if d else 0, n.bytes_sent, n.bytes_recv)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--intervalo", type=float, default=1.0, help="segundos entre amostras (padrão 1.0)")
    ap.add_argument("--saida", default="coleta.csv", help="arquivo CSV de saída")
    ap.add_argument("--duracao", type=float, default=None, help="duração total em segundos (padrão: até Ctrl+C)")
    ap.add_argument("--fase-arquivo", default="fase.txt", help="arquivo com o nome da fase atual")
    ap.add_argument("--silencioso", action="store_true", help="não imprime cada amostra")
    args = ap.parse_args()

    eu = psutil.Process()
    psutil.cpu_percent(None)
    eu.cpu_percent(None)
    ant = contadores()
    inicio = prev = time.perf_counter()
    i = 0

    with open(args.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUNAS)
        print(f"Coletando a cada {args.intervalo} s em {args.saida} (Ctrl+C para parar)")
        try:
            while True:
                i += 1
                time.sleep(max(0.0, inicio + i * args.intervalo - time.perf_counter()))
                agora = time.perf_counter()
                dt, prev = agora - prev, agora

                atual = contadores()
                vm = psutil.virtual_memory()
                linha = [
                    round(agora - inicio, 3),
                    datetime.now().isoformat(timespec="milliseconds"),
                    ler_fase(args.fase_arquivo),
                    psutil.cpu_percent(None),
                    vm.percent,
                    round(vm.available / MB, 1),
                    psutil.swap_memory().percent,
                    round((atual[0] - ant[0]) / MB / dt, 3),
                    round((atual[1] - ant[1]) / MB / dt, 3),
                    round((atual[2] - ant[2]) / 1024 / dt, 3),
                    round((atual[3] - ant[3]) / 1024 / dt, 3),
                    eu.cpu_percent(None),
                    round(eu.memory_info().rss / MB, 1),
                ]
                ant = atual
                w.writerow(linha)
                f.flush()
                if not args.silencioso:
                    print(f"t={linha[0]:7.1f}s  fase={linha[2]:<8} cpu={linha[3]:5.1f}%  "
                          f"mem_disp={linha[5]:8.1f} MB  disco_esc={linha[8]:7.2f} MB/s  "
                          f"coletor={linha[11]:4.1f}% cpu")
                if args.duracao is not None and agora - inicio >= args.duracao:
                    break
        except KeyboardInterrupt:
            pass
    print(f"Fim: {i} amostras em {args.saida}")


if __name__ == "__main__":
    main()
