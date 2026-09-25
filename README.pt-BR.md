[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Saiba o que seu computador está fazendo sem sair do terminal.**

O SystemPulse é um monitor de sistema open source, local e somente de leitura.
Ele mostra CPU, memória, processos e métricas de GPU disponíveis em uma interface
de terminal controlada pelo teclado. Não há dashboard web, conta ou telemetria.
Diagnósticos baseados em evidências e alertas estão planejados; hoje, `doctor`
verifica o próprio SystemPulse.

> **Versão de desenvolvimento:** execute a partir de uma cópia do repositório.
> O projeto ainda não foi publicado no PyPI. O nome planejado da distribuição é
> `systempulse-monitor`; o comando instalado será `systempulse`.

## Como executar

Requer Python 3.12+ e [uv](https://docs.astral.sh/uv/). Na pasta do projeto:

```sh
uv sync
uv run systempulse
```

O segundo comando abre a TUI em um terminal interativo. A experiência padrão
dispensa configuração e permissões elevadas.

## O que é exibido

- **Overview:** CPU e RAM em tempo real, gráfico recente de CPU, carga/VRAM/
  temperatura opcionais da GPU e listas separadas de Top CPU e Top RAM.
- **Processes:** busca, ordenação por CPU, memória ou PID e detalhes verificados
  do processo selecionado. Campos protegidos aparecem como indisponíveis.
- **System:** sistema operacional, uptime, informações de CPU e memória e todas
  as GPUs informadas pelo provider ativo.

As métricas de GPU exigem atualmente o `nvidia-smi` da NVIDIA. Sem ele, o
SystemPulse continua funcionando e marca a GPU como indisponível. Providers AMD
e Intel ainda não foram implementados. Veja a [coleta de GPU](docs/pt-BR/gpu.md).

## Outros comandos

```sh
uv run systempulse status
uv run systempulse processes --sort memory --limit 10
uv run systempulse processes --search python
uv run systempulse doctor
uv run systempulse version
```

`status` mostra um snapshot do sistema. `processes` lista processos com filtros.
`doctor` verifica o ambiente, os collectors, o provider de GPU e o terminal.
Esses comandos encerram após mostrar o resultado.

## Atalhos de teclado

| Tecla | Ação |
| --- | --- |
| `1` / `2` / `3` | Overview / Processes / System |
| `/` | Buscar processos |
| `c` / `m` / `p` | Ordenar por CPU / memória / PID |
| `Enter` | Voltar da busca para a tabela ou abrir o processo selecionado |
| `Esc` | Sair da busca ou fechar os detalhes do processo |
| `PageUp` / `PageDown` | Rolar Overview em um terminal baixo |
| `t` | Alternar tema claro/escuro nesta sessão |
| `r` | Atualizar todos os collectors |
| `q` / `Ctrl+C` | Sair (`q` primeiro fecha os detalhes) |

## Estado atual

A TUI e a CLI foram executadas no Windows. Linux e macOS são plataformas alvo;
a validação nelas ainda está pendente. Disco, rede, histórico, alertas e o
comando contínuo `top` ainda não foram implementados. CI multiplataforma e `top`
são os próximos passos.

Collectors tipados alimentam o estado da aplicação, que abastece Textual e a
CLI. A coleta executa fora do loop da interface. As métricas permanecem na
máquina e o SystemPulse não realiza ações destrutivas. Consulte o
[benchmark da varredura de processos](docs/pt-BR/benchmarking.md) para a
metodologia atual de medição.

## Contribuição

Execute `uv run pytest`, `uv run ruff check .` e `uv run mypy` antes de propor
alterações. Código e documentação principal são escritos em inglês; a
documentação pública também possui versão pt-BR. Em caso de divergência,
prevalece a versão inglesa.

Licenciado sob [Apache 2.0](LICENSE).
