# Benchmark de custo em execução

[English](../en/benchmarking.md) | [Português Brasileiro](benchmarking.md)

Enumerar processos pode dominar o tempo de um ciclo de monitoramento. O
benchmark atual compara grupos de atributos lidos com
`psutil.process_iter(attrs=..., ad_value=None)` na própria máquina:

```sh
uv run python scripts/benchmark_process_scan.py
```

O script limpa o cache de processos do psutil antes de cada varredura, executa
cada grupo de atributos três vezes e mostra a mediana do tempo decorrido e a
quantidade de processos. Ele não acessa a rede nem grava arquivos de resultado.
Execute primeiro com a máquina relativamente ociosa e repita durante o uso
normal.

O grupo `core` lê PID, nome, horário de criação, tempos de CPU e memória
residente. `table` também lê usuário e número de threads. Outros grupos isolam
status e PID pai. `full` lê todos os campos listados. A quantidade de processos
pode mudar durante a medição; portanto, os tempos são indicativos e não
equivalem a um conjunto sintético de tamanho fixo.

Em uma máquina de desenvolvimento Windows com Python 3.12.14 e 233 processos,
uma medição recente de `core` levou 0,36 segundo de mediana; `table` levou 0,65
segundo. Incluir status ou PID pai elevou a mediana para 0,78 ou 1,96 segundo;
`full` levou 2,71 segundos. São medições locais, não conclusões para as três
plataformas. A coleta periódica agora lê apenas os atributos de `core`. Usuário,
número de threads, status e PID pai são obtidos quando o detalhe ou a árvore de
processos é aberta. O coletor de processos roda a cada dois segundos; coletores
mais leves, a cada segundo.

Para estimar o custo em execução:

```sh
uv run python scripts/benchmark_runtime.py --seconds 10
```

O script executa os coletores padrão e depois a aplicação Textual real em modo
de teste headless, cada fase pela duração indicada. Usa diretórios temporários
de dados. Mostra tempo decorrido, tempo de CPU do processo como percentual de
**um núcleo**, memória residente no fim da fase, quantidade de linhas e tamanho
do SQLite, além da duração dos ciclos de coleta. Os valores incluem
instrumentação e inicialização dentro de cada fase. A renderização headless
difere de um terminal físico. A memória no fim da fase não representa o pico.

No mesmo Windows, uma execução de 10 segundos após a mudança na varredura
mediu 25,7% de um núcleo e 82,7 MiB de RAM para os coletores; a TUI headless
mediu 32,3% de um núcleo e 91,9 MiB. Cada fase gravou 10 linhas de histórico;
os arquivos SQLite ocupavam cerca de 20 KiB naquele momento. Os ciclos de
coleta tiveram mediana de 0,23 segundo e máximo de 0,66 segundo. O custo de
CPU ainda excede a meta inicial de baixo consumo. Precisamos de execuções mais
longas e medições interativas no Linux/macOS antes de afirmar desempenho para
uma release.
