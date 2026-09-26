# Histórico local de métricas

[English](../en/history.md) | [Português Brasileiro](history.md)

O SystemPulse grava resumos de CPU, memória, disco que contém a pasta pessoal e
rede do host em um banco SQLite no diretório de dados do usuário definido pelo
sistema operacional. Nomes de processos, linhas de comando e destinos de rede
individuais não são armazenados. Nenhum dado sai da máquina.

Execute `systempulse history --range 1h` ou pressione `4` na TUI. Pressione `h`
para alternar entre 10m, 30m, 1h, 6h, 24h, 7d e 30d. A primeira leitura de
uma taxa fica indisponível até que a segunda amostra estabeleça um intervalo.

Amostras originais são mantidas por 10 minutos. As mais antigas são agregadas
em médias por minuto por até 24 horas e, depois, em médias a cada 15 minutos por
até 30 dias. Leituras ausentes não entram nas médias. A compactação ocorre no
máximo uma vez por minuto durante o monitoramento; nenhum dado é coletado com o
SystemPulse fechado. O banco usa SQLite em modo WAL e a gravação acontece fora
da thread da interface. Falhas no banco não interrompem o monitoramento ao vivo.
