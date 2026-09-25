[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Monitoramento e diagnóstico de sistema em tempo real, open source, para Windows, Linux e macOS.**

Saiba o que seu computador está fazendo sem sair do terminal.

> **Estado do desenvolvimento:** a visão Textual em tempo real, o explorador
> interativo de processos, a visão System e os comandos atuais funcionam a partir
> de uma cópia do código. Não há versão publicada no PyPI.

O SystemPulse foi concebido como uma aplicação local e inicialmente somente de
leitura. Seus três princípios são **Measure. Understand. Inform.** Observações e
diagnósticos futuros deverão se apoiar em métricas observáveis; a aplicação não
afirmará causalidade sem evidências.

## Capturas de tela e gravações do terminal

Ainda não existem. Gravações estão planejadas antes da primeira versão.

## Funcionalidades

Disponíveis agora:

- Pacote Python instalável com o comando `systempulse`.
- `systempulse` abre uma visão em tempo real com CPU, memória, atividade recente
  da CPU e processos de maior CPU em um terminal interativo.
- A visão Processes oferece busca em tempo real, ordenação por CPU, memória ou
  PID, seleção por teclado e detalhes verificados do processo selecionado.
  Campos bloqueados pelo sistema operacional são marcados como indisponíveis.
- A visão System mostra informações observadas do host, hardware de CPU e
  memória, incluindo uptime quando o horário de inicialização está disponível.
- `systempulse version` informa a versão do pacote instalado.
- `systempulse status` mostra CPU, memória, uptime e processos de maior consumo.
- `systempulse processes` lista processos com ordenação por CPU ou memória, busca
  pelo nome e limite de linhas. Campos indisponíveis aparecem identificados.
- `systempulse doctor` verifica o Python, a plataforma alvo, os collectors
  incluídos e as capacidades do terminal. Falha de collector essencial retorna
  código diferente de zero; ausência de terminal interativo gera aviso.

A meta restante para v0.1 inclui o comando `top` e validação mais ampla entre
plataformas. Essas etapas ainda estão planejadas.

## Instalação

Esta versão de desenvolvimento, ainda não publicada, requer Python 3.12+ e
[uv](https://docs.astral.sh/uv/). Em uma cópia do repositório:

```sh
uv sync
```

O nome planejado para a distribuição é `systempulse-monitor`, mantendo
`systempulse` como comando instalado. Após a publicação, a instalação pretendida
será `pipx install systempulse-monitor`. O nome de distribuição `systempulse` no
PyPI pertence a outro projeto.

## Uso

```sh
uv run systempulse
uv run systempulse version
uv run systempulse status
uv run systempulse processes --sort memory --limit 10
uv run systempulse processes --search python
uv run systempulse doctor
```

O primeiro comando requer um terminal interativo. `status`, `processes` e
`doctor` coletam duas amostras com intervalo de cerca de um segundo para calcular
as taxas de CPU; mostram o resultado e encerram.

## Atalhos de teclado

| Tecla | Ação |
| --- | --- |
| `q`, `Ctrl+C` | Sair |
| `r` | Solicitar uma atualização completa |
| `1` | Abrir Overview |
| `2` | Abrir Processes |
| `3` | Abrir System |
| `/` | Focar a busca de processos em Processes |
| `c`, `m`, `p` | Ordenar processos por CPU, memória ou PID |
| `Enter` | Abrir os detalhes do processo selecionado |
| `Esc` | Voltar da busca para a tabela ou fechar os detalhes |

Digite um termo para filtrar nomes de processos. Pressione `Enter` no campo de
busca para voltar à tabela. Com os detalhes abertos, `q` fecha essa visão.

## Plataformas suportadas

Windows, Linux e macOS são as plataformas planejadas. Os comandos e a TUI foram
executados no Windows; a validação em Linux e macOS ainda está pendente.
É necessário Python 3.12+. A visão pode ser rolada verticalmente quando o terminal
não comporta todos os painéis de uma vez.

## Arquitetura

O fluxo local atual é: collectors tipados → serviço de amostragem → agregador de
métricas → estado da aplicação → interface Textual e CLI. Os collectors executam
fora do loop de eventos da TUI e possuem intervalos de coleta independentes. Um
barramento interno para futuro histórico, regras e alertas ainda está planejado.
Widgets não consultam o `psutil` diretamente. Informações do host são coletadas
uma vez por minuto. Os detalhes de um processo são lidos sob demanda após
verificar sua identidade pelo PID e horário de criação.

A [metodologia de benchmark da varredura de processos](docs/pt-BR/benchmarking.md)
registra como o custo do collector é medido durante o desenvolvimento.

## Privacidade e segurança

O SystemPulse é local-first e somente de leitura. Conta na nuvem, telemetria,
rastreamento e API remota não fazem parte do projeto padrão. Os comandos atuais
coletam métricas localmente e não as transmitem.

## Roadmap

| Versão | Foco planejado |
| --- | --- |
| v0.1 | CPU, memória, processos, TUI em tempo real, CLI básica |
| v0.2 | Disco, rede, árvore de processos |
| v0.3 | Histórico SQLite, gráficos no terminal, relatórios |
| v0.4 | Regras, alertas, observações fundamentadas em evidências |
| v0.5 | GPU, bateria, sensores |
| v1.0 | Suporte multiplataforma estável e API de plugins documentada |

## Contribuição

Contribuições seguirão código-fonte em inglês e documentação criada primeiro em
inglês, com documentação pt-BR equivalente para funcionalidades públicas. O guia
de contribuição e os modelos de issues serão adicionados antes da v0.1. Por
enquanto, execute `uv run pytest`, `uv run ruff check .` e `uv run mypy` antes
de propor alterações.

## Licença

O SystemPulse está licenciado sob a [Apache License 2.0](LICENSE).

A documentação em inglês é a fonte principal. A documentação em português é
mantida como tradução correspondente; quando houver divergência, prevalece a
versão em inglês.
