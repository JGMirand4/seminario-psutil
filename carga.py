#!/usr/bin/env python3
"""Gerador de carga controlada para a demonstração 2.

Escreve a fase atual em fase.txt (o coletor.py lê esse arquivo) e gera carga de
CPU, memória ou disco. Rode em um SEGUNDO terminal, com o coletor.py já funcionando.

Sequência completa (12 min, como no roteiro):
    python carga.py sequencia
Sequência encurtada para ensaio (por exemplo, 10% do tempo):
    python carga.py sequencia --escala 0.1
Fase de CPU mais longa (melhor para o método dos lotes):
    python carga.py sequencia --cpu-segundos 600
Carga de CPU constante (sem transiente), para comparar:
    python carga.py sequencia --perfil constante
Uma fase isolada:
    python carga.py cpu --segundos 60 --nucleos 2
    python carga.py memoria --segundos 60 --max-mb 1500
    python carga.py disco --segundos 30
"""
import argparse
import math
import multiprocessing as mp
import os
import random
import tempfile
import time

import psutil

MB = 1024 ** 2
FASE_ARQ = "fase.txt"


def marcar_fase(nome):
    with open(FASE_ARQ, "w", encoding="utf-8") as f:
        f.write(nome)
    print(f"\n>>> fase: {nome}", flush=True)


def _queimar(fim):
    x = 0.0
    while time.time() < fim:
        x = x * 1.0000001 + 1.0


def perfil_carga(segundos, media=0.6, phi=0.7, sigma=0.08, tau=10, inicial=0.0, semente=None):
    """Fração de ocupação (0 a 1) de cada segundo da fase de CPU.

    Transiente: a ocupação sobe de 'inicial' até 'media' com constante de tempo 'tau' s.
    Regime: ruído AR(1) (phi) em torno da média, para observações vizinhas parecidas.
    O PERFIL é sintético, mas a CPU que o coletor lê é medida de verdade."""
    rng = random.Random(semente)
    ruido, perfil = 0.0, []
    for k in range(int(segundos) + 1):
        ruido = phi * ruido + rng.gauss(0, sigma)
        base = media + (inicial - media) * math.exp(-k / tau)
        perfil.append(min(1.0, max(0.0, base + ruido)))
    return perfil


def _queimar_perfil(inicio, fim, perfil, passo=0.1):
    """Em cada fatia de 'passo' s, fica ocupado a fração do perfil e dorme no resto."""
    x = 0.0
    while True:
        agora = time.time()
        if agora >= fim:
            break
        ocupado_ate = agora + perfil[min(int(agora - inicio), len(perfil) - 1)] * passo
        while time.time() < ocupado_ate:
            x = x * 1.0000001 + 1.0
        resto = agora + passo - time.time()
        if resto > 0:
            time.sleep(resto)


def fase_cpu(segundos, nucleos, perfil="variavel", semente=None):
    """Laço intensivo em 'nucleos' processos (um por núcleo).

    perfil 'constante': 100% de ocupação (série quase plana, sem transiente).
    perfil 'variavel':  ocupação com transiente inicial e ruído autocorrelacionado."""
    inicio = time.time()
    fim = inicio + segundos
    if perfil == "constante":
        alvo, args = _queimar, (fim,)
    else:
        alvo, args = _queimar_perfil, (inicio, fim, perfil_carga(segundos, semente=semente))
    procs = [mp.Process(target=alvo, args=args) for _ in range(nucleos)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()


def fase_memoria(segundos, max_mb, passo_mb=50):
    """Aloca memória aos poucos (passo_mb por segundo) até um limite seguro."""
    limite = min(max_mb, int(psutil.virtual_memory().available / MB * 0.5))
    print(f"    limite de alocação: {limite} MB (no máximo 50% da memória disponível)")
    fim = time.time() + segundos
    blocos, alocado = [], 0
    while time.time() < fim:
        if alocado + passo_mb <= limite:
            blocos.append(bytearray(b"\x01") * (passo_mb * MB))   # preenche: a memória é de fato usada
            alocado += passo_mb
        time.sleep(1)
    print(f"    alocado: {alocado} MB")
    del blocos


def fase_disco(segundos, pasta=None, arquivo_mb=256):
    """Escreve (com fsync) e lê um arquivo temporário em laço; apaga ao final."""
    caminho = os.path.join(pasta or tempfile.gettempdir(), "carga_psutil.bin")
    bloco = os.urandom(MB)        # gerado uma vez: não queremos carga de CPU nesta fase
    fim = time.time() + segundos
    try:
        while time.time() < fim:
            with open(caminho, "wb") as f:
                for _ in range(arquivo_mb):
                    f.write(bloco)
                f.flush()
                os.fsync(f.fileno())
                if hasattr(os, "posix_fadvise"):   # Linux: descarta o cache para a leitura ir ao disco
                    os.posix_fadvise(f.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
            with open(caminho, "rb") as f:
                while f.read(8 * MB):
                    pass
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def espera(segundos):
    time.sleep(segundos)


def sequencia(escala, nucleos, max_mb, cpu_s, perfil, semente):
    plano = [("repouso", 120, lambda s: espera(s)),
             ("cpu", cpu_s, lambda s: fase_cpu(s, nucleos, perfil, semente)),
             ("memoria", 180, lambda s: fase_memoria(s, max_mb)),
             ("disco", 120, lambda s: fase_disco(s)),
             ("fim", 120, lambda s: espera(s))]
    for nome, base, acao in plano:
        s = base * escala
        marcar_fase(nome)
        print(f"    duração: {s:.0f} s")
        acao(s)
    marcar_fase("-")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["sequencia", "cpu", "memoria", "disco"])
    ap.add_argument("--segundos", type=float, default=60)
    ap.add_argument("--nucleos", type=int, default=1, help="processos de carga de CPU (padrão 1)")
    ap.add_argument("--max-mb", type=int, default=2048, help="teto de memória alocada (padrão 2048)")
    ap.add_argument("--cpu-segundos", type=float, default=180,
                    help="duração base da fase de CPU na sequência (padrão 180; use 600 para ter 10 lotes na análise)")
    ap.add_argument("--perfil", choices=["variavel", "constante"], default="variavel",
                    help="carga de CPU: 'variavel' (transiente + ruído autocorrelacionado, padrão) ou 'constante'")
    ap.add_argument("--semente", type=int, default=None, help="semente do perfil variável (padrão: aleatória)")
    ap.add_argument("--escala", type=float, default=1.0, help="multiplica as durações da sequência")
    a = ap.parse_args()

    if a.modo == "sequencia":
        sequencia(a.escala, a.nucleos, a.max_mb, a.cpu_segundos, a.perfil, a.semente)
    else:
        marcar_fase(a.modo)
        if a.modo == "cpu":
            fase_cpu(a.segundos, a.nucleos, a.perfil, a.semente)
        elif a.modo == "memoria":
            fase_memoria(a.segundos, a.max_mb)
        else:
            fase_disco(a.segundos)
        marcar_fase("-")


if __name__ == "__main__":
    mp.freeze_support()
    main()
