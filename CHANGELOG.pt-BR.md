# Histórico de alterações

[English](CHANGELOG.md) | [Português Brasileiro](CHANGELOG.pt-BR.md)

As mudanças são agrupadas por release. O SystemPulse seguirá Semantic
Versioning após começar a publicar versões.

## Não publicado — prévia em código fonte 0.1.0.dev0

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

Ainda não há publicação no PyPI. Validação interativa em Linux/macOS e redução
do custo de CPU continuam como critérios de release.
