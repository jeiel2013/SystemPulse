# Desenvolvimento

[English](../en/development.md) | [Português Brasileiro](development.md)

Instale o [uv](https://docs.astral.sh/uv/getting-started/installation/) e execute:

```sh
uv python install 3.12
uv sync --locked
uv run systempulse
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

`uv run systempulse` precisa de terminal interativo. Em um shell não interativo,
use `uv run systempulse status`. Execute `uv run python
scripts/benchmark_runtime.py --seconds 10` para medir sua máquina; resultados
variam com processos, permissões e carga. `uv build --no-sources` e `uv run
python scripts/smoke_install.py` verificam o pacote e o comando instalado. O
teste de instalação requer uv e pode baixar Python ou dependências.

Mantenha os modelos de domínio independentes de Textual e psutil. Ao adicionar
uma métrica, crie um collector tipado, registre-o na sessão padrão, trate
indisponibilidade e teste o comportamento observável antes de expor a métrica.
Funcionalidades públicas exigem documentação equivalente em inglês e pt-BR. O
inglês é a referência principal. Use Conventional Commits.

A matriz do GitHub Actions roda em Ubuntu, Windows e macOS. Testes headless da
TUI verificam interações; ainda precisamos conferir a renderização interativa
em cada plataforma antes de afirmar suporte estável.
