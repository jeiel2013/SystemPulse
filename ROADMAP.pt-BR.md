# Roadmap

[English](ROADMAP.md) | [Português Brasileiro](ROADMAP.pt-BR.md)

Este plano descreve trabalho pretendido, não suporte já entregue. A prévia
publicada `0.1.0.dev0` inclui CPU, memória, processos, resumos de disco e
rede em tempo real, providers opcionais de hardware, histórico local, alertas
por limites, árvore de processos, relatórios, CLI e TUI. O README descreve o
comportamento e as limitações exatas.

## Antes de uma versão estável

- Verificar interativamente layout, temas, resize, teclado e saída limpa em
  terminais macOS e ampliar a cobertura de terminais no Windows e Linux.
- Repetir medições longas de CPU/RAM e reduzir o custo da varredura periódica
  de processos.
- Revisar wheel, pacote fonte, licença, notas de release e instruções de
  instalação.

## Marcos posteriores

- **0.2:** melhorar as visões de partições de disco e interfaces de rede;
  ampliar a cobertura dos providers de hardware com fixtures de dispositivos
  reais.
- **0.3:** introduzir migrações de esquema SQLite e refinar histórico de longo
  prazo e gráficos no terminal.
- **0.4:** ampliar diagnósticos factuais e ações de regras configuráveis.
- **1.0:** documentar uma API de plugins estável e validar combinações de
  sistemas e terminais em uma matriz explícita de compatibilidade.

Datas e versões só serão assumidas após cumprir seus critérios de aceitação.
