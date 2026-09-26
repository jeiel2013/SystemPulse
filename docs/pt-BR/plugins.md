# Plugins de coleta (experimental)

[English](../en/plugins.md) | [Português Brasileiro](plugins.md)

O SystemPulse registra coletores de terceiros por entry points Python no grupo
`systempulse.collectors`. Esta API é experimental até a v1. Plugins começam
desativados. `systempulse plugins` lista os entry points instalados sem importar
o código deles.

O entry point deve apontar para uma factory sem argumentos que devolva um
coletor com `CollectorMetadata`, `is_available()` e `collect()`. O nome do
coletor deve ser único. Exemplo no `pyproject.toml` do plugin:

```toml
[project.entry-points."systempulse.collectors"]
example = "example_plugin:ExampleCollector"
```

Depois de instalar o pacote, adicione o nome do entry point ao `config.toml`
opcional no caminho exibido por `systempulse doctor`:

```toml
enabled_plugins = ["example"]
```

O SystemPulse importa e executa o código de plugins ativados localmente com as
permissões do usuário atual. Ative apenas pacotes confiáveis. Falhas de
importação ou criação são informadas sem interromper os coletores internos.
Plugins devem ser somente de leitura, evitar requisições de rede por padrão e
retornar métricas tipadas com timestamps UTC. Ações de regras e exportadores de
relatórios ainda não são pontos de extensão.
