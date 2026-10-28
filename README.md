# Scripts do seminário: Medição de sistemas com Python (psutil)

Os scripts seguem o roteiro. Cada bloco "# %%" dos arquivos `demo1_...` e `analise.py` é uma célula:
execute uma por vez (VS Code: Shift+Enter; Spyder e PyCharm também aceitam). Cada bloco traz
o que **mostrar** e uma frase para **dizer**.

## Instalação
```
pip install -r requirements.txt
```

## Ordem da apresentação

| Parte | Min | Arquivo | Como rodar |
| --- | --- | --- | --- |
| Demonstração 1: psutil ao vivo | 14 | `demo1_psutil_ao_vivo.py` | célula por célula |
| Demonstração 2: coleta com carga | 12 | `coletor.py` + `carga.py` + `grafico.py` | dois terminais (abaixo) |
| Demonstração 3: análise (cap. 10) | 13 | `analise.py` | célula por célula |
| Ensaio e plano B | - | `gerar_exemplo.py` | gera CSVs **simulados** |

## Demonstração 2: dois terminais

Terminal 1 (coletor, deixe rodando):
```
python coletor.py --saida coleta_A.csv
```
Terminal 2 (carga; a sequência completa leva 12 min, como no roteiro):
```
python carga.py sequencia
```
Variações úteis:
- ensaio rápido: `python carga.py sequencia --escala 0.1`
- fases isoladas: `python carga.py cpu --segundos 60 --nucleos 2`, `python carga.py memoria --segundos 60`, `python carga.py disco --segundos 30`
- mostrar o overhead: rode o coletor com `--intervalo 1` e depois com `--intervalo 0.1` e compare a coluna `coletor_cpu_pct`.

Ao final, pare o coletor com Ctrl+C e plote:
```
python grafico.py coleta_A.csv
```
Aponte o início instável, o patamar e a volta ao repouso.

## Demonstração 3: análise

1. Em `analise.py`, confira `ARQ_A`, `METRICA` e `FASE` no bloco 0.
2. Para comparar dois cenários, faça uma segunda coleta com outra configuração (por exemplo, `carga.py cpu --nucleos 2` em vez de 1), salve como `coleta_B.csv` e defina `ARQ_B`.
3. Método dos lotes: o livro pede lote de 10 x lag e 10 lotes. Com o lag típico de poucos segundos, a fase de CPU de 180 s não basta. Use `python carga.py sequencia --cpu-segundos 600` para ter dados suficientes. Se a coleta for curta, o script avisa e usa 10 lotes menores.

## Plano B

`python gerar_exemplo.py` cria `exemplo_A.csv` e `exemplo_B.csv` com dados **simulados** (transiente e ruído autocorrelacionado). Use em `ARQ_A` e `ARQ_B` para ensaiar ou se a coleta ao vivo falhar. Avise a plateia de que são dados simulados.

## Cuidados
- A fase de memória aloca no máximo 50% da memória disponível (e `--max-mb`). Ajuste se a máquina tiver pouca RAM.
- A fase de disco escreve arquivos de 256 MB na pasta temporária e apaga ao final.
- Sensores (`sensors_*`) podem não existir ou vir vazios, dependendo do sistema; o bloco 9 da demonstração 1 já trata isso.
- No Windows, `sin` e `sout` do swap não têm significado, e a carga média é emulada.
- Testei os scripts em Linux. Ensaie na máquina da apresentação, principalmente `coletor.py` e `carga.py`.
