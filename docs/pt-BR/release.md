# Verificações de release

O SystemPulse é uma versão de desenvolvimento. O nome do pacote é
`systempulse-monitor`; o comando instalado é `systempulse`. Ainda não há release
publicada no PyPI.

O [workflow de CI](../../.github/workflows/ci.yml) foi configurado para Ubuntu, Windows e
macOS. Cada job verifica Ruff, mypy, os testes da CLI e da TUI, gera as
distribuições de código e wheel, instala o wheel como ferramenta isolada do uv e
executa `systempulse version`, `status`, `top --help`, `processes`, `doctor`,
`history`, `alerts`, `tree`, `report` e `plugins` fora do
repositório. Também verifica se o wheel inclui a folha de estilos da TUI, se o
pacote fonte contém a licença e se o relatório exportado fica nos dados
isolados do teste.

Execute as mesmas verificações localmente antes de uma release:

```sh
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest -q
uv build --no-sources
uv run --locked python scripts/smoke_install.py
```

Para desenvolvimento e testes isolados, `SYSTEMPULSE_DATA_DIR` e
`SYSTEMPULSE_CONFIG_DIR` substituem os diretórios padrão de dados e
configuração do usuário. Sem essas variáveis, o programa utiliza os caminhos
apropriados para cada sistema.

A publicação exige jobs verdes nos três sistemas e revisão dos artefatos e das
notas de release. Testes automatizados da TUI não comprovam que todos os
terminais renderizam de forma idêntica. O mantenedor relatou execuções
interativas bem-sucedidas no Windows e Linux; a validação interativa no macOS
continua pendente. Ainda não devemos afirmar validação de todas as combinações
de sistemas e terminais.

Antes de publicar, confirme que este projeto pode usar o nome
`systempulse-monitor` no PyPI e configure uma identidade de publicação
confiável. Revise o [changelog](../../CHANGELOG.pt-BR.md) e a
[política de segurança](../../SECURITY.pt-BR.md), execute o teste isolado do
wheel e use o comando instalado `systempulse` em terminais físicos Windows,
Linux e macOS. Confira os dois temas, resize, busca/detalhes de processos,
saída por `q`/`Ctrl+C` e o estado do terminal depois de sair. O benchmark atual
no Windows excede a meta inicial de CPU ociosa; repita medições mais longas
antes de afirmar um desempenho garantido. Publicar e enviar os commits locais
são ações separadas de manutenção.

Depois dessas verificações, crie e envie uma tag idêntica à versão do
`pyproject.toml`, como `v0.1.0.dev0`. Na aba **Actions** do repositório, abra
**Publish to PyPI**, clique em **Run workflow**, mantenha o branch `main` e
preencha **Release tag** com a tag. Clique em **Run workflow** para iniciar a
publicação; aprove o ambiente `pypi` se solicitado. Não é necessário GitHub CLI.

O [workflow](../../.github/workflows/publish.yml) faz checkout da tag informada,
rejeita divergências de versão, repete as verificações, gera e testa a
distribuição e publica por Trusted Publishing. Uma tag inexistente falha no
checkout. Configure o ambiente GitHub
`pypi` com revisão obrigatória e cadastre esse workflow como
[publicador confiável no PyPI](https://docs.pypi.org/trusted-publishers/)
antes de acioná-lo. Um push comum não publica o pacote.
