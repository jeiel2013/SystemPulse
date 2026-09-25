[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Monitoramento e diagnóstico de sistema em tempo real, open source, para Windows, Linux e macOS.**

Saiba o que seu computador está fazendo sem sair do terminal.

> **Estado do desenvolvimento:** comandos pontuais de CPU, memória e processos já
> funcionam a partir de uma cópia do código. A interface Textual em tempo real
> ainda está em desenvolvimento. Não há versão deste projeto publicada no PyPI.

O SystemPulse foi concebido como uma aplicação local e inicialmente somente de
leitura. Seus três princípios são **Measure. Understand. Inform.** Observações e
diagnósticos futuros deverão se apoiar em métricas observáveis; a aplicação não
afirmará causalidade sem evidências.

## Capturas de tela e gravações do terminal

Ainda não existem. As gravações serão adicionadas quando a interface estiver
funcional.

## Funcionalidades

Disponíveis agora:

- Pacote Python instalável com o comando `systempulse`.
- `systempulse version` informa a versão do pacote instalado.
- `systempulse status` mostra CPU, memória e processos de maior consumo.
- `systempulse processes` lista processos com ordenação por CPU ou memória, busca
  pelo nome e limite de linhas. Campos indisponíveis aparecem identificados.

A meta para v0.1 também inclui explorador de processos em tempo real, gráficos
recentes no terminal, informações do sistema e os comandos `top` e `doctor`.
Essas funcionalidades ainda estão planejadas.

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
uv run systempulse version
uv run systempulse status
uv run systempulse processes --sort memory --limit 10
uv run systempulse processes --search python
uv run systempulse
```

O último comando ainda informa que a interface em tempo real está em
desenvolvimento. `status` e `processes` coletam duas amostras com intervalo de
cerca de um segundo para calcular as taxas de CPU; mostram o resultado e encerram.

## Atalhos de teclado

Esta versão de desenvolvimento ainda não possui atalhos da TUI. A navegação por
teclado será documentada quando a interface for implementada.

## Plataformas suportadas

Windows, Linux e macOS são as plataformas planejadas. Os comandos atuais foram
executados no Windows; a validação em Linux e macOS ainda está pendente.
É necessário Python 3.12+.

## Arquitetura

O fluxo local atual é: collectors tipados → serviço de amostragem → agregador de
métricas → estado da aplicação → CLI. A interface Textual e um barramento interno
para futuro histórico, regras e alertas ainda estão planejados. Widgets não
consultarão o `psutil` diretamente.

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
