# Relatórios locais

[English](../en/reports.md) | [Português Brasileiro](reports.md)

Execute `systempulse report --format json` para exportar um snapshot observado.
Os formatos disponíveis são `json`, `csv`, `markdown` e `html`. HTML é apenas
uma exportação estática, sem interface web. O atalho `e` na TUI exporta o
snapshot mais recente em Markdown.

Por padrão, os arquivos ficam na pasta `reports` do diretório de dados do
usuário do SystemPulse; o comando informa o caminho completo. Use
`--output CAMINHO` para escolher o arquivo. Arquivos existentes nunca são
sobrescritos. Os relatórios incluem métricas atuais do sistema e os dez
processos com maior CPU, com nomes, PIDs, CPU e memória residente quando
disponíveis. Revise o relatório antes de compartilhá-lo: nomes de processos e
métricas podem revelar atividade local.
