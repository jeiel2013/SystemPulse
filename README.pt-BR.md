[English](README.md) | [Português Brasileiro](README.pt-BR.md)

# SystemPulse

**Saiba o que seu computador está fazendo sem sair do terminal.**

O SystemPulse é um monitor de sistema open source, local e somente de leitura.
Ele mostra CPU, memória, processos e métricas de GPU disponíveis em uma interface
de terminal controlada pelo teclado. Não há dashboard web, conta ou telemetria.
Diagnósticos baseados em evidências e alertas estão planejados; hoje, `doctor`
verifica o próprio SystemPulse.

> **Versão de desenvolvimento:** instale a partir de uma cópia do repositório.
> O projeto ainda não foi publicado no PyPI. O nome da distribuição é
> `systempulse-monitor`; o comando instalado é `systempulse`.

## Instalação e uso

Instale o [uv](https://docs.astral.sh/uv/getting-started/installation/) uma vez:

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS ou Linux**

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Abra um novo terminal e instale o Python 3.12 com o uv:

```sh
uv python install 3.12
```

Clone o [SystemPulse](https://github.com/jeiel2013/SystemPulse) (ou entre em
uma cópia existente), instale o comando e adicione o diretório de ferramentas
do uv ao `PATH`:

```sh
git clone https://github.com/jeiel2013/SystemPulse.git
cd SystemPulse
uv tool install --python 3.12 .
uv tool update-shell
```

Abra um novo terminal e execute o SystemPulse de qualquer diretório:

```sh
systempulse
```

O comando abre a TUI em um terminal interativo. O uv só é necessário para
instalar ou atualizar o SystemPulse; no uso diário, `uv run` não é necessário.
A experiência padrão dispensa configuração e permissões elevadas.

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
systempulse status
systempulse top --sort memory --limit 10
systempulse processes --sort memory --limit 10
systempulse processes --search python
systempulse doctor
systempulse version
```

`status` mostra um snapshot do sistema. `top` atualiza um monitor compacto de
processos a cada segundo; use `q` ou `Ctrl+C` para sair. Ele exige terminal
interativo. `processes` lista processos com filtros. `doctor` verifica o
ambiente, os collectors, o provider de GPU e o terminal. Os demais comandos
encerram após mostrar o resultado.

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

O SystemPulse adapta os dois temas à capacidade de cores informada pelo terminal.
No Linux, `systempulse doctor` mostra o modo detectado. Se o terminal suporta
truecolor, mas informa menos cores, execute
`TEXTUAL_COLOR_SYSTEM=truecolor systempulse` para usar a paleta completa.

## Estado atual

A TUI e a CLI foram executadas no Windows. Linux e macOS são plataformas alvo;
a validação interativa nelas ainda está pendente. O CI foi configurado para
executar testes, builds e verificações de instalação isolada nos três sistemas.
Disco, rede, histórico e alertas ainda não foram implementados. Veja as
[verificações de release](docs/pt-BR/release.md).

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
