# Collector plugins (experimental)

[English](plugins.md) | [Português Brasileiro](../pt-BR/plugins.md)

SystemPulse can register third-party collectors through Python entry points in
the `systempulse.collectors` group. This API is experimental until v1. Plugins
are disabled by default. `systempulse plugins` lists installed entry points
without importing their code.

An entry point must resolve to a zero-argument factory returning a collector
with `CollectorMetadata`, `is_available()` and `collect()`. The collector name
must be unique. For example, in a plugin's `pyproject.toml`:

```toml
[project.entry-points."systempulse.collectors"]
example = "example_plugin:ExampleCollector"
```

After installing the package, add the entry point name to the optional
`config.toml` path shown by `systempulse doctor`:

```toml
enabled_plugins = ["example"]
```

SystemPulse imports and runs enabled plugin code locally with the current
user's permissions. Only enable packages you trust. An import or factory error
is reported without stopping built-in collectors. Plugins should be read-only,
avoid network requests by default, and return typed measurements with UTC
timestamps. Rule actions and report exporters are not plugin hooks yet.
