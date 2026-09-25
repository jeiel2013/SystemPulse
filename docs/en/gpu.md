# GPU collection

SystemPulse currently reads GPU utilization, used and total VRAM, and GPU
temperature from NVIDIA devices through `nvidia-smi`. This provider is optional:
the rest of the monitor runs when no supported GPU source exists. AMD and Intel
providers are planned, not implemented.

The provider runs a fixed, read-only CSV query every two seconds, without a
shell, and stops waiting after two seconds. Values reported as unavailable by
the driver remain unavailable in SystemPulse. VRAM values are converted from
MiB to bytes in the core model and formatted for display. The
[NVIDIA System Management Interface documentation](https://docs.nvidia.com/deploy/nvidia-smi/)
describes the underlying query and the availability of device fields.

The Overview shows the first reported GPU's load, used VRAM, and temperature.
The System view lists every reported GPU, including its name and total VRAM.
`systempulse status` summarizes the first GPU and indicates when more devices
were found. These are device-level readings; SystemPulse does not attribute
VRAM use to individual processes.

If `nvidia-smi` is absent, the GPU collector is marked unavailable. A driver
failure or query timeout is isolated from CPU, memory, and process collection.
`systempulse doctor` reports GPU provider health as an optional check. No GPU
metrics are sent off the machine.

To check support locally, run:

```sh
uv run systempulse doctor
uv run systempulse status
uv run systempulse
```

The terminal interface is required only for the last command.
