# Arquitetura

[English](../en/architecture.md) | [Português Brasileiro](architecture.md)

O SystemPulse executa em um único processo Python local. A CLI e a TUI Textual
compartilham collectors tipados e `MonitorSession`; nenhuma inicia servidor web.
A sessão padrão registra collectors de CPU, memória, disco, rede, processos,
informações do sistema, GPU, bateria e sensores. Entry points opcionais ficam
desativados até serem nomeados na configuração local.

```text
psutil / ferramentas locais → CollectorRegistry → MetricService
    → MetricAggregator → SystemSnapshot → ApplicationState → Textual
                                    ↘ RuleEngine → alertas e observações
                                    ↘ HistoryStore → resumos SQLite
```

`MetricService` executa collectors síncronos em uma thread de trabalho. Cada
collector declara seu intervalo; resultados em cache preservam seus timestamps
UTC entre ciclos. A falha de um collector gera um estado de indisponibilidade
ou erro, sem interromper os demais. O aggregator publica um snapshot tipado.
Widgets leem o estado da aplicação, sem acessar psutil diretamente.

A tabela varre campos essenciais dos processos a cada dois segundos. Status,
usuário, threads, executável e comando são lidos somente quando um processo é
selecionado. PID e horário de criação identificam a instância para evitar
confusão quando um PID é reutilizado. A árvore faz uma varredura separada sob
demanda.

`HistoryStore` grava resumos de métricas e o ciclo de vida de alertas em SQLite
por usuário, com WAL. Amostras brutas duram 10 minutos; agregados por minuto,
24 horas; agregados de 15 minutos, 30 dias. Nomes e comandos de processos não
são persistidos. O esquema atual é criado no primeiro uso; migrações ainda são
necessárias antes de uma versão estável.

Regras avaliam medições sustentadas com timestamps. Observações descrevem o
que foi medido, sem afirmar causas não observadas. Relatórios exportam um
snapshot localmente. Plugins cobrem apenas collectors e ainda são
experimentais. Um event bus geral ainda não foi implementado.
