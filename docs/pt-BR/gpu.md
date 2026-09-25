# Coleta de GPU

O SystemPulse lê atualmente utilização da GPU, VRAM usada e total, e temperatura
de dispositivos NVIDIA por meio do `nvidia-smi`. O provider é opcional: o restante
do monitor funciona quando não existe uma fonte de GPU suportada. Providers AMD e
Intel estão planejados, mas ainda não foram implementados.

O provider executa uma consulta CSV fixa e somente de leitura a cada dois
segundos, sem shell, com limite de espera de dois segundos. Valores que o driver
não fornece permanecem indisponíveis no SystemPulse. A VRAM informada em MiB é
convertida para bytes no modelo central e formatada na apresentação. A
[documentação do NVIDIA System Management Interface](https://docs.nvidia.com/deploy/nvidia-smi/)
descreve a consulta e a disponibilidade dos campos do dispositivo.

A visão Overview mostra carga, VRAM usada e temperatura da primeira GPU
informada. A visão System lista todas as GPUs informadas, incluindo nome e VRAM
total. `systempulse status` resume a primeira GPU e indica quando existem outros
dispositivos. Essas leituras pertencem ao dispositivo; o SystemPulse ainda não
atribui uso de VRAM a processos individuais.

Se `nvidia-smi` não estiver disponível, o collector de GPU será marcado como
indisponível. Uma falha do driver ou um timeout não interrompe a coleta de CPU,
memória e processos. `systempulse doctor` apresenta a saúde do provider de GPU
como verificação opcional. Nenhuma métrica de GPU sai da máquina.

Para conferir o suporte local, execute:

```sh
uv run systempulse doctor
uv run systempulse status
uv run systempulse
```

Somente o último comando exige um terminal interativo.
