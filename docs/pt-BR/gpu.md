# Coleta de GPU

[English](../en/gpu.md) | [Português Brasileiro](gpu.md)

O SystemPulse lê carga da GPU, VRAM usada e total e temperatura por meio de
ferramentas instaladas dos fabricantes, quando esses dados são expostos:

| Fonte | Ferramenta | Formato |
| --- | --- | --- |
| NVIDIA | `nvidia-smi` | consulta CSV fixa |
| AMD ROCm | `rocm-smi` | consulta JSON fixa |
| Intel XPU Manager | `xpu-smi` | consulta CSV fixa |

Cada consulta é somente de leitura, não utiliza shell e tem timeout de dois
segundos. Campos ausentes permanecem indisponíveis. Valores de memória da
NVIDIA e da Intel são convertidos de MiB para bytes; o ROCm da AMD informa
bytes. Uma fonte com falha não oculta leituras retornadas por outra. A coleta
ocorre a cada dois segundos e é opcional; dispositivos sem suporte não
interrompem o monitoramento de CPU, RAM e processos.

A visão Overview resume a primeira GPU detectada. A visão System lista todos
os dispositivos informados; `systempulse status` indica quando há mais de um.
São leituras do dispositivo. O SystemPulse não atribui VRAM a processos
individuais. O suporte AMD exige uma instalação ROCm compatível; o suporte
Intel exige XPU Manager. A validação em hardware desses providers ainda está
pendente.

Referências: [NVIDIA SMI](https://docs.nvidia.com/deploy/nvidia-smi/),
[ROCm SMI](https://rocm.docs.amd.com/projects/rocm_smi_lib/en/docs-6.1.0/python_usage.html),
[Intel XPU Manager](https://intel.github.io/xpumanager/2.0/xpu-smi/overview.html).
