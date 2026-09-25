# Benchmark de varredura de processos

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

Em uma máquina de desenvolvimento Windows com Python 3.12.14 e 213 processos,
a mediana de `core` foi aproximadamente 0,52 segundo; `table` levou 0,73 segundo.
Acrescentar status ou PID pai separadamente elevou as medianas para
aproximadamente 1,24 e 1,60 segundo; `full` levou 2,35 segundos. Esses são
resultados locais, não metas de desempenho multiplataforma. Por isso, a varredura periódica
lê os campos de tabela menos custosos e deixa status e PID pai para os detalhes
de processo. O intervalo padrão declarado é de dois segundos; o agendamento
por intervalo ainda não foi implementado.

No momento, o script mede **apenas tempo decorrido**. Consumo de CPU, pico de
memória, gravações no banco e custo da TUI exigem benchmarks próprios antes da
v0.1.
