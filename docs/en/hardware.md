# Optional hardware readings

[English](hardware.md) | [Português Brasileiro](../pt-BR/hardware.md)

The System view shows battery charge, plugged-in state, and remaining time when
the operating system provides them through psutil. An unknown or unlimited time
is shown as unavailable. Temperature and fan readings are also shown when
psutil exposes them. Each reading retains its reported group and label; no
temperature is guessed from CPU or GPU load.

These collectors run every five seconds. A device without a battery or exposed
sensors is a normal unavailable capability. The live monitor continues without
them. GPU collection has a separate provider contract and currently supports
NVIDIA's local `nvidia-smi` command.
