# GPU collection

[English](gpu.md) | [Português Brasileiro](../pt-BR/gpu.md)

SystemPulse reads GPU load, used and total VRAM, and temperature through
installed vendor tools when they expose those values:

| Vendor source | Tool | Format |
| --- | --- | --- |
| NVIDIA | `nvidia-smi` | fixed CSV query |
| AMD ROCm | `rocm-smi` | fixed JSON query |
| Intel XPU Manager | `xpu-smi` | fixed CSV query |

Each query is read-only, runs without a shell, and has a two-second timeout.
Missing device fields stay unavailable. NVIDIA and Intel memory values are
converted from MiB to bytes; AMD ROCm reports byte counts. A failed source
cannot hide readings returned by another source. GPU collection runs every two
seconds and is optional; unsupported devices do not stop CPU, RAM, or process
monitoring.

The Overview summarizes the first detected GPU. The System view lists all
reported devices; `systempulse status` indicates when more than one was found.
These are device-level readings. SystemPulse does not attribute VRAM use to
individual processes. AMD support requires a compatible ROCm installation;
Intel support requires XPU Manager. Hardware validation of these providers is
still pending.

References: [NVIDIA SMI](https://docs.nvidia.com/deploy/nvidia-smi/),
[ROCm SMI](https://rocm.docs.amd.com/projects/rocm_smi_lib/en/docs-6.1.0/python_usage.html),
[Intel XPU Manager](https://intel.github.io/xpumanager/2.0/xpu-smi/overview.html).
