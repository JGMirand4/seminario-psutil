# Demonstração 1: psutil ao vivo (14 min)
#
# Como usar: abra no VS Code, Spyder ou PyCharm e execute UMA CÉLULA POR VEZ
# (cada bloco "# %%" é uma célula; no VS Code, Shift+Enter). Também funciona
# copiando bloco a bloco para o interpretador (python ou ipython).
# Cada bloco tem: o que MOSTRAR, uma frase para DIZER e o código.
# Deixe um gerenciador de tarefas (ou top/htop) ao lado para comparar valores.

# %% Bloco 0: preparação (30 s)
import os
import tempfile
import time

import psutil

print("psutil", psutil.__version__)

# %% Bloco 1: CPU, a armadilha da primeira leitura (2 min)
# MOSTRAR: o primeiro valor é 0.0 e os seguintes são reais.
# DIZER:   "Sem intervalo, ele compara com a chamada anterior, então a primeira não vale."
print("Bloqueando 1 s:", psutil.cpu_percent(interval=1))
print("Sem intervalo, 1ª chamada:", psutil.cpu_percent(interval=None))
time.sleep(1)
print("Sem intervalo, 2ª chamada:", psutil.cpu_percent(interval=None))
time.sleep(1)
print("Sem intervalo, 3ª chamada:", psutil.cpu_percent(interval=None))

# %% Bloco 2: CPU por núcleo, contagem e frequência (1 min)
# MOSTRAR: uma lista com um valor por núcleo lógico.
# DIZER:   "Um valor por núcleo mostra carga mal distribuída."
print("Por núcleo:", psutil.cpu_percent(interval=1, percpu=True))
print("Núcleos lógicos:", psutil.cpu_count())
print("Núcleos físicos:", psutil.cpu_count(logical=False))
print("Frequência:", psutil.cpu_freq())  # pode ser None em algumas máquinas virtuais

# %% Bloco 3: cpu_times é contador acumulado (1 min)
# MOSTRAR: os números só crescem; a utilização vem da diferença.
# DIZER:   "É tempo acumulado: a utilização vem da diferença."
a = psutil.cpu_times()
time.sleep(2)
b = psutil.cpu_times()
print("Antes: ", a)
print("Depois:", b)
total = sum(b) - sum(a)
print(f"Ocupado (não idle) neste intervalo: {100 * (1 - (b.idle - a.idle) / total):.1f}%")

# %% Bloco 4: memória (2 min)
# MOSTRAR: execute, abra um programa pesado (navegador com várias abas) e execute de novo.
# DIZER:   "Para falta de memória, olhe 'available', não 'free'."
MB = 1024 ** 2
vm = psutil.virtual_memory()
print(f"Total: {vm.total / MB:.0f} MB | disponível: {vm.available / MB:.0f} MB | "
      f"livre: {vm.free / MB:.0f} MB | uso: {vm.percent}%")
print("Swap:", psutil.swap_memory())  # sin/sout são cumulativos e sem sentido no Windows

# %% Bloco 5: disco, contadores acumulados e taxa por diferença (2 min)
# MOSTRAR: bytes escritos/lidos subindo durante a cópia de um arquivo grande.
# DIZER:   "Também é contador acumulado: a taxa é a diferença dividida pelo intervalo."
print("Uso de '/':", psutil.disk_usage(os.path.abspath(os.sep)))
bloco = os.urandom(MB)            # gerado fora da medição: o tempo medido é o do disco
antes = psutil.disk_io_counters()
t0 = time.perf_counter()
caminho = os.path.join(tempfile.gettempdir(), "demo_psutil.bin")
with open(caminho, "wb") as f:
    for _ in range(200):          # 200 MB
        f.write(bloco)
    f.flush()
    os.fsync(f.fileno())
dt = time.perf_counter() - t0
depois = psutil.disk_io_counters()
if antes and depois:
    esc = (depois.write_bytes - antes.write_bytes) / MB
    print(f"Escrito: {esc:.0f} MB em {dt:.2f} s = {esc / dt:.0f} MB/s")
os.remove(caminho)

# %% Bloco 6: rede, mesma lógica do disco (1 min)
# MOSTRAR: abra uma página pesada ou baixe um arquivo durante os 5 s.
# DIZER:   "Mesma lógica do disco."
n0 = psutil.net_io_counters()
time.sleep(5)
n1 = psutil.net_io_counters()
print(f"Recebido: {(n1.bytes_recv - n0.bytes_recv) / 1024 / 5:.1f} KB/s | "
      f"enviado: {(n1.bytes_sent - n0.bytes_sent) / 1024 / 5:.1f} KB/s")

# %% Bloco 7: processo, o próprio interpretador (1,5 min)
# MOSTRAR: o rss sobe depois de alocar uma lista grande.
# DIZER:   "Dá para medir só o programa em teste, e não a máquina inteira."
p = psutil.Process()
print("Antes: ", f"{p.memory_info().rss / MB:.0f} MB")
lista = [0] * 50_000_000          # cerca de 400 MB de ponteiros
print("Depois:", f"{p.memory_info().rss / MB:.0f} MB")
del lista
print("Liberado:", f"{p.memory_info().rss / MB:.0f} MB")

# %% Bloco 8: ranking de processos (1,5 min)
# MOSTRAR: os 5 maiores consumidores de CPU agora.
# DIZER:   "process_iter com lista de atributos é a forma barata de varrer processos."
for proc in psutil.process_iter(["pid", "name"]):
    try:
        proc.cpu_percent(None)    # primeira leitura de cada objeto: descartada
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

# %% Bloco 9: sensores, dependem do sistema (1 min)
# MOSTRAR: dados reais, ou vazio, ou a função nem existe.
# DIZER:   "Depende do sistema e do hardware, então o código deve prever a ausência."
for nome in ("sensors_temperatures", "sensors_fans", "sensors_battery"):
    func = getattr(psutil, nome, None)
    if func is None:
        print(nome, "-> não existe nesta plataforma")
    else:
        print(nome, "->", func() or "sem dados")

# %% Bloco 10: exceção de processo inexistente (1 min)
# MOSTRAR: a exceção NoSuchProcess tratada.
# DIZER:   "Processos terminam, e um coletor robusto trata isso."
try:
    psutil.Process(99_999_999).name()
except psutil.NoSuchProcess as erro:
    print("NoSuchProcess tratada:", erro)

# %% Bloco 11 (extra): custo de cada chamada, o overhead de Jain (1 min)
# MOSTRAR: microssegundos por chamada e a fração de CPU que o coletor consome.
# DIZER:   "O medidor também custa: dá para calcular o overhead para cada intervalo."
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
