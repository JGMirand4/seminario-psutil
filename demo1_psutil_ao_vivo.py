# %%
import os
import tempfile
import time

import psutil

print("psutil", psutil.__version__)

# %%
print("Bloqueando 1 s:", psutil.cpu_percent(interval=1))
print("Sem intervalo, 1ª chamada:", psutil.cpu_percent(interval=None))
time.sleep(1)
print("Sem intervalo, 2ª chamada:", psutil.cpu_percent(interval=None))
time.sleep(1)
print("Sem intervalo, 3ª chamada:", psutil.cpu_percent(interval=None))

# %%
print("Por núcleo:", psutil.cpu_percent(interval=1, percpu=True))
print("Núcleos lógicos:", psutil.cpu_count())
print("Núcleos físicos:", psutil.cpu_count(logical=False))
print("Frequência:", psutil.cpu_freq())

# %%
a = psutil.cpu_times()
time.sleep(2)
b = psutil.cpu_times()
print("Antes: ", a)
print("Depois:", b)
total = sum(b) - sum(a)
print(f"Ocupado (não idle) neste intervalo: {100 * (1 - (b.idle - a.idle) / total):.1f}%")

# %%
MB = 1024 ** 2
vm = psutil.virtual_memory()
print(f"Total: {vm.total / MB:.0f} MB | disponível: {vm.available / MB:.0f} MB | "
      f"livre: {vm.free / MB:.0f} MB | uso: {vm.percent}%")
print("Swap:", psutil.swap_memory())

# %%
print("Uso de '/':", psutil.disk_usage(os.path.abspath(os.sep)))
bloco = os.urandom(MB)
antes = psutil.disk_io_counters()
t0 = time.perf_counter()
caminho = os.path.join(tempfile.gettempdir(), "demo_psutil.bin")
with open(caminho, "wb") as f:
    for _ in range(200):
        f.write(bloco)
    f.flush()
    os.fsync(f.fileno())
dt = time.perf_counter() - t0
depois = psutil.disk_io_counters()
if antes and depois:
    esc = (depois.write_bytes - antes.write_bytes) / MB
    print(f"Escrito: {esc:.0f} MB em {dt:.2f} s = {esc / dt:.0f} MB/s")
os.remove(caminho)

# %%
n0 = psutil.net_io_counters()
time.sleep(5)
n1 = psutil.net_io_counters()
print(f"Recebido: {(n1.bytes_recv - n0.bytes_recv) / 1024 / 5:.1f} KB/s | "
      f"enviado: {(n1.bytes_sent - n0.bytes_sent) / 1024 / 5:.1f} KB/s")

# %%
p = psutil.Process()
print("Antes: ", f"{p.memory_info().rss / MB:.0f} MB")
lista = [0] * 50_000_000
print("Depois:", f"{p.memory_info().rss / MB:.0f} MB")
del lista
print("Liberado:", f"{p.memory_info().rss / MB:.0f} MB")

# %%
for proc in psutil.process_iter(["pid", "name"]):
    try:
        proc.cpu_percent(None)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
time.sleep(1)
linhas = []
for proc in psutil.process_iter(["pid", "name"]):
    try:
        linhas.append((proc.cpu_percent(None), proc.info["pid"], proc.info["name"]))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
for cpu, pid, nome in sorted(linhas, reverse=True)[:5]:
    print(f"{cpu:5.1f}%  pid={pid:<7} {nome}")

# %%
for nome in ("sensors_temperatures", "sensors_fans", "sensors_battery"):
    func = getattr(psutil, nome, None)
    if func is None:
        print(nome, "-> não existe nesta plataforma")
    else:
        print(nome, "->", func() or "sem dados")

# %%
try:
    psutil.Process(99_999_999).name()
except psutil.NoSuchProcess as erro:
    print("NoSuchProcess tratada:", erro)

# %%
def custo_us(func, n=200):
    t0 = time.perf_counter()
    for _ in range(n):
        func()
    return (time.perf_counter() - t0) / n * 1e6

chamadas = {
    "cpu_percent": lambda: psutil.cpu_percent(None),
    "virtual_memory": psutil.virtual_memory,
    "disk_io_counters": psutil.disk_io_counters,
    "net_io_counters": psutil.net_io_counters,
}
total_us = 0
for nome, func in chamadas.items():
    c = custo_us(func)
    total_us += c
    print(f"{nome:<18} {c:8.1f} µs por chamada")
for intervalo in (1.0, 0.1, 0.01):
    print(f"Intervalo {intervalo:>5} s -> overhead estimado {total_us / 1e6 / intervalo * 100:.3f}% de um núcleo")
