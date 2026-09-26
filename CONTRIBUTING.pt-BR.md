# Contribuição

[English](CONTRIBUTING.md) | [Português Brasileiro](CONTRIBUTING.pt-BR.md)

Obrigado por ajudar a melhorar o SystemPulse. Abra uma issue para relatar um
bug, uma observação específica de plataforma ou uma proposta objetiva. Boas
primeiras contribuições incluem melhorar estados vazios, adicionar fixtures
de collectors baseadas em saídas reais sem dados privados e esclarecer a
documentação.

Prepare o projeto com `uv sync --locked`. Antes de abrir um pull request,
execute os mesmos comandos de teste, Ruff e mypy do
[guia de desenvolvimento](docs/pt-BR/development.md).
Para mudanças na instalação, execute também `uv build --no-sources` e
`uv run python scripts/smoke_install.py`.

Faça mudanças focadas e descreva o que foi medido ou testado. Informe sistema
operacional e terminal ao relatar problemas visuais ou de plataforma. Não
afirme causas sem evidência. Novos collectors devem falhar isoladamente e
preservar timestamps UTC. Não adicione acesso à rede ou ações destrutivas em
processos por padrão. Código e documentação principal são escritos em inglês;
atualize a versão pt-BR correspondente em mudanças públicas. Use Conventional
Commits.

Problemas de segurança seguem a [política de segurança](SECURITY.md), sem
issue pública. Todos seguem o [código de conduta](CODE_OF_CONDUCT.md).
