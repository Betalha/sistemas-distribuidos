# Trabalho 6 - SOAP x REST x GraphQL x gRPC

Serviço de streaming de músicas (usuários, músicas, playlists; CRUD + 5 consultas do enunciado) implementado em Python com as 4 tecnologias sobre o mesmo armazenamento em memória (`app/data.py`), com testes de carga comparativos.

## Estrutura
- `app/`: `rest_server.py` (FastAPI), `graphql_server.py` (Strawberry), `soap_server.py` (SOAP 1.2 escrito à mão, sem WSDL), `music.proto` + `grpc_server.py`, `locustfile.py` (mesma carga nas 4)
- `docker-compose.yml`: 4 serviços, cada um com 1 CPU; `locust` no perfil `tools`
- `testes.sh`: bateria completa (4 tecnologias x 10/50/200/500 usuários, 30 s); `graficos.py`: tabela + gráficos
- `resultados/`: CSVs do Locust; `graficos/`, `tabela.csv`

## Reproduzir
```bash
./testes.sh                  # ~12 min; DURACAO=60s USUARIOS="10 100" para variar
python3 graficos.py          # tabela.csv e graficos/*.png (check: python3 graficos.py --test)
```

## Resultados (execução única, 30 s, 0 falhas em todas)
| usuários | REST req/s (p95 ms) | GraphQL | SOAP | gRPC |
|---|---|---|---|---|
| 10 | 112 (5) | 103 (29) | 111 (8) | 115 (4) |
| 50 | 539 (17) | 192 (270) | 555 (8) | 558 (7) |
| 200 | 1364 (93) | 220 (890) | 2074 (19) | 2286 (2) |
| 500 | 1609 (260) | 220 (2300) | 2245 (180) | 4429 (70) |

- Com 10 usuários todas as tecnologias entregam a demanda (~110 req/s): sem diferença.
- GraphQL satura em ~220 req/s (custo de resolvers por requisição); REST em ~1600; SOAP em ~2200; gRPC passa de 4400.
- Payload médio por resposta: gRPC ~700 B, REST/GraphQL ~1500-1900 B, SOAP ~2700 B.

## Limitações (declare na apresentação)
- Gerador e serviços na mesma máquina; com 500 usuários o gerador pode limitar o gRPC.
- Execução única de 30 s, sem repetição (sem dispersão); dados em memória e pequenos.
- O SOAP é um servidor mínimo escrito à mão (sem WSDL nem WS-*): o resultado favorece o SOAP frente a uma stack real. A comparação REST/SOAP também mistura a tecnologia com a implementação (FastAPI valida com pydantic).
- O mix de carga usa a granularidade de chamadas do REST; GraphQL poderia fazer menos chamadas com consultas aninhadas, e isso não é medido.

## Falta fazer
- Prints da máquina dos testes (16 CPUs, 11 GB RAM, Fedora) e, se quiser, repetir a bateria 3x.
