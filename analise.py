# %%
import math
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ARQ_A = os.environ.get("ARQ_A", "coleta_A.csv")
ARQ_B = os.environ.get("ARQ_B")
METRICA = "cpu_pct"
FASE = "cpu"
JANELA = 20
ALFA = 0.05
PRECISAO_REL = 0.09
MOSTRAR = os.environ.get("MOSTRAR", "1") != "0"
os.makedirs("figuras", exist_ok=True)


def carregar(arq, metrica=METRICA, fase=FASE):
    df = pd.read_csv(arq)
    if fase:
        df = df[df["fase"] == fase]
    return df[metrica].to_numpy(dtype=float)


def media_movel(x, janela):
    return pd.Series(x).rolling(janela, min_periods=1).mean().to_numpy()


def truncagem(x):
    for l in range(len(x) - 1):
        resto = x[l:]
        if x[l] != resto.min() and x[l] != resto.max():
            return l
    return 0


def transiente_regressao(x, janela, alfa=ALFA):
    t = np.arange(janela)
    for ini in range(len(x) - janela + 1):
        if stats.linregress(t, x[ini:ini + janela]).pvalue > alfa:
            return ini
    return None


def acf(x, maxlag):
    x = x - x.mean()
    den = (x * x).sum()
    return np.array([(x[:len(x) - k] * x[k:]).sum() / den for k in range(maxlag + 1)])


def lag_nao_significativo(x, maxlag=None):
    maxlag = maxlag or min(len(x) // 3, 200)
    r = acf(x, maxlag)
    limite = 1.96 / math.sqrt(len(x))
    for k in range(1, maxlag + 1):
        if abs(r[k]) < limite:
            return k, r, limite
    return maxlag, r, limite


def lotes(x, lag):
    tam = max(1, 10 * lag)
    if len(x) // tam < 10:
        print(f"AVISO: com lote de {tam} só há {len(x) // tam} lotes (o livro pede 10). "
              f"Colete por mais tempo; para a demonstração, uso 10 lotes menores.")
        tam = max(1, len(x) // 10)
    n = len(x) // tam
    return x[:n * tam].reshape(n, tam).mean(axis=1), tam


def intervalo(medias, alfa=ALFA):
    n = len(medias)
    m, s = medias.mean(), medias.std(ddof=1)
    t = stats.t.ppf(1 - alfa / 2, n - 1)
    meia = t * s / math.sqrt(n)
    return m, s, t, meia, meia / m


def salvar_e_mostrar(nome):
    plt.tight_layout()
    plt.savefig(f"figuras/{nome}.png", dpi=130)
    if MOSTRAR:
        plt.show()


serie = carregar(ARQ_A)
print(f"{ARQ_A}: {len(serie)} observações de '{METRICA}' na fase '{FASE}'")

# %%
plt.figure(figsize=(10, 4))
plt.plot(serie, lw=0.8, alpha=0.6, label="observações")
plt.plot(media_movel(serie, JANELA), lw=2, color="#e07a2f", label=f"média móvel ({JANELA})")
plt.xlabel("observação (1 por segundo)")
plt.ylabel(METRICA)
plt.legend()
salvar_e_mostrar("1_serie")

# %%
l_trunc = truncagem(serie)
l_reg = transiente_regressao(serie, janela=min(JANELA, len(serie) // 2))
print("Truncagem (Jain, cap. 25):      descartar", l_trunc, "observações")
print("Regressão linear (cap. 10):     descartar", l_reg, "observações")
TRANSIENTE = l_reg if l_reg is not None else l_trunc
estavel = serie[TRANSIENTE:]
print(f"Usando {TRANSIENTE}; restam {len(estavel)} observações em regime estacionário")
plt.figure(figsize=(10, 4))
plt.plot(serie, lw=0.8, alpha=0.6)
plt.axvline(TRANSIENTE, color="#c0392b", ls="--", label=f"fim do transiente = {TRANSIENTE}")
plt.legend()
salvar_e_mostrar("2_transiente")

# %%
lag, r, limite = lag_nao_significativo(estavel)
print(f"Primeiro lag sem correlação significativa: {lag}")
plt.figure(figsize=(10, 4))
plt.bar(range(len(r)), r, width=0.8, color="#2f7f9d")
plt.axhline(limite, color="#c0392b", ls="--")
plt.axhline(-limite, color="#c0392b", ls="--")
plt.xlabel("lag (observações)")
plt.ylabel("autocorrelação")
salvar_e_mostrar("3_correlograma")

# %%
medias, tam = lotes(estavel, lag)
print(f"Lote de {tam} observações -> {len(medias)} lotes")
print("Médias dos lotes:", np.round(medias, 2))
if len(medias) > 2:
    r1 = acf(medias, 1)[1]
    print(f"Autocorrelação lag 1 entre lotes: {r1:.2f} (deve ficar perto de zero)")

# %%
m, s, t, meia, rel = intervalo(medias)
print(f"Média das médias dos lotes: {m:.2f}   s = {s:.2f}   t = {t:.3f} (n = {len(medias)})")
print(f"IC de {100 * (1 - ALFA):.0f}%: {m:.2f} ± {meia:.2f}  ->  [{m - meia:.2f}, {m + meia:.2f}]")
print(f"Precisão relativa = {rel:.3f}  (alvo: <= {PRECISAO_REL})")
if rel <= PRECISAO_REL:
    print("Atende a precisão: basta esta quantidade de lotes.")
else:
    n_nec = math.ceil((t * s / (PRECISAO_REL * m)) ** 2)
    print(f"Não atende: seriam necessários cerca de {n_nec} lotes (arredonde para cima e confira de novo).")

# %%
if ARQ_B is None:
    print("Defina ARQ_B no bloco 0 (por exemplo, 'coleta_B.csv') para comparar dois cenários.")
else:
    def prepara(arq):
        x = carregar(arq)
        ini = transiente_regressao(x, janela=min(JANELA, len(x) // 2))
        if ini is None:
            ini = truncagem(x)
        x = x[ini:]
        lag_, _, _ = lag_nao_significativo(x)
        return lotes(x, lag_)[0]

    a, b = prepara(ARQ_A), prepara(ARQ_B)
    na, nb = len(a), len(b)
    va, vb = a.var(ddof=1) / na, b.var(ddof=1) / nb
    gl = (va + vb) ** 2 / (va ** 2 / (na - 1) + vb ** 2 / (nb - 1))
    dif = a.mean() - b.mean()
    meia_dif = stats.t.ppf(1 - ALFA / 2, gl) * math.sqrt(va + vb)
    print(f"A = {a.mean():.2f} (n={na})   B = {b.mean():.2f} (n={nb})")
    print(f"Diferença A - B = {dif:.2f} ± {meia_dif:.2f}  ->  [{dif - meia_dif:.2f}, {dif + meia_dif:.2f}]  (gl = {gl:.1f})")
    if dif - meia_dif <= 0 <= dif + meia_dif:
        print("O intervalo contém 0: sem evidência estatística de diferença entre A e B.")
    else:
        print("O intervalo não contém 0: A e B diferem de forma estatisticamente significativa.")
