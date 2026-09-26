# Histórico de alterações

[English](CHANGELOG.md) | [Português Brasileiro](CHANGELOG.pt-BR.md)

As mudanças são agrupadas por release. O SystemPulse segue Semantic Versioning.

## 0.1.0.dev1 — Atualização da documentação

- Documentar a instalação pelo PyPI com uv ou pipx e a execução direta de
  `systempulse`, mantendo a instalação pelo código-fonte como alternativa.
- Atualizar a documentação em inglês e português brasileiro com o status de
  publicação, testes manuais em Windows/Linux e CI aprovado nos três sistemas.
- Explicar como publicar novas versões e atualizar o README no PyPI.

## 0.1.0.dev0 — Versão de desenvolvimento

- Overview em tempo real, explorador e detalhes de processos, árvore, troca de
  tema, navegação por teclado e layout responsivo.
- Collectors de CPU, memória, disco, rede, sistema, bateria e sensores;
  providers opcionais de GPU NVIDIA, AMD ROCm e Intel XPU. A validação de AMD e
  Intel em hardware físico ainda está pendente.
- Histórico de métricas e ciclo de vida de alertas em SQLite local; regras de
  limite sustentado com observações baseadas em evidências.
- Comandos CLI de consulta, `top` compacto, diagnóstico `doctor`, exportação de
  relatórios estáticos e entry points experimentais de collectors opt-in.
- Configuração de CI multiplataforma e teste isolado de instalação do wheel.

Disponível no [PyPI](https://pypi.org/project/systempulse-monitor/0.1.0.dev0/).
A validação interativa no macOS e a redução do custo de CPU continuam pendentes
antes de uma versão estável.
