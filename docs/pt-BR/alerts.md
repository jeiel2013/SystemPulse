# Alertas por limite e configuração local

[English](../en/alerts.md) | [Português Brasileiro](alerts.md)

O SystemPulse avalia atualmente limites sustentados de CPU, memória e uso do
disco que contém a pasta pessoal. As regras padrão disparam quando CPU ou
memória permanecem acima de 90%, ou o disco acima de 95%, por 120 segundos.
Uma métrica ausente ou antiga reinicia a contagem. O alerta descreve apenas o
limite observado, sem afirmar uma causa. Pressione `5` na TUI para ver os
alertas e `d` para dispensar o alerta ativo selecionado. `systempulse alerts`
lista os registros locais. Um alerta dispensado só pode disparar novamente
depois que a condição terminar e voltar a ocorrer.

A configuração é opcional. Execute `systempulse doctor` para localizar o
`config.toml` do usuário no seu sistema operacional. Para substituir as regras
padrão, crie o arquivo com entradas como esta:

```toml
[[rules]]
id = "high-memory"
metric = "memory.percent"
threshold_percent = 85
for_seconds = 60
severity = "warning"
enabled = true
```

As métricas aceitas são `cpu.percent`, `memory.percent` e `disk.percent`.
A severidade pode ser `warning` ou `critical`. A lista `rules` substitui as
regras padrão; uma lista vazia desativa os alertas por limite. TOML ou valores
inválidos fazem o programa usar os padrões, e `systempulse doctor` informa o
erro. As regras são carregadas na inicialização; reinicie o SystemPulse após
editar o arquivo.

O ciclo de vida dos alertas é armazenado no mesmo banco SQLite local que o
histórico de métricas. Não há notificações nem requisições de rede. Outras
observações diagnósticas e ações de regras estão planejadas.
