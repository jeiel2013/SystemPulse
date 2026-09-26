# Leituras opcionais de hardware

[English](../en/hardware.md) | [Português Brasileiro](hardware.md)

A visão System mostra carga da bateria, estado da alimentação e tempo restante
quando o sistema operacional fornece esses dados por meio do psutil. Tempo
desconhecido ou ilimitado aparece como indisponível. Temperaturas e ventoinhas
também aparecem quando o psutil as expõe. Cada leitura conserva o grupo e o
rótulo informados; nenhuma temperatura é estimada a partir da carga de CPU ou
GPU.

Esses coletores executam a cada cinco segundos. Um dispositivo sem bateria ou
sem sensores expostos representa uma capacidade normalmente indisponível. O
monitor continua funcionando. A coleta de GPU usa um contrato de providers
separado e atualmente suporta o comando local `nvidia-smi` da NVIDIA.
