# Árvore de processos

[English](../en/process-tree.md) | [Português Brasileiro](process-tree.md)

Pressione `6` na TUI ou execute `systempulse tree` para consultar relações de
parentesco sob demanda. A tabela periódica não lê os PIDs dos processos pais,
mantendo sua varredura normal mais leve. Navegue pela árvore com as setas;
`Enter` abre os detalhes do processo selecionado e `r` faz uma nova varredura.
O comando CLI aceita `--limit`.

A árvore usa um único snapshot de melhor esforço com PID, nome, PID pai e hora
de criação. Ela rejeita um pai cuja criação seja posterior à do filho, situação
possível após reutilização de PID. Processos protegidos ou encerrados durante a
leitura são ignorados. A árvore não é histórica e pode mudar entre varreduras.
