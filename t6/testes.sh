#!/usr/bin/env bash
# Bateria: 8 serviços (4 tecnologias x Python e Java) x USUARIOS. Resultado: resultados/<tecnologia>_u<usuarios>_stats.csv
# Ex.: DURACAO=60s USUARIOS="10 100" ./testes.sh
set -uo pipefail
cd "$(dirname "$0")"
DURACAO="${DURACAO:-30s}"; USUARIOS="${USUARIOS:-10 50 200 500}"; PROCESSOS="${PROCESSOS:-2}"
mkdir -p resultados
docker compose up -d --build rest graphql soap grpc java-rest java-graphql java-soap java-grpc
sleep 5
SERVICOS="rest:RestUser:http://rest:8000 graphql:GraphqlUser:http://graphql:8000 soap:SoapUser:http://soap:8000 grpc:GrpcUser:grpc:8000 \
java_rest:RestUser:http://java-rest:8000 java_graphql:GraphqlUser:http://java-graphql:8000 java_soap:SoapUser:http://java-soap:8000 java_grpc:GrpcUser:java-grpc:8000"
# aquecimento da JVM (JIT): 15 s por serviço Java, descartado
mkdir -p /tmp/aquecimento
for t in $SERVICOS; do
  case $t in java_*) ;; *) continue;; esac
  resto=${t#*:}; cls=${resto%%:*}; host=${resto#*:}
  docker compose run --rm --no-deps -v /tmp/aquecimento:/resultados locust locust -f locustfile.py "$cls" --host "$host" \
    --headless -u 50 -r 50 -t 15s --processes "$PROCESSOS" --csv /resultados/aq --only-summary > /dev/null 2>&1 || true
done
for u in $USUARIOS; do
  for t in $SERVICOS; do
    nome=${t%%:*}; resto=${t#*:}; cls=${resto%%:*}; host=${resto#*:}
    docker compose run --rm --no-deps locust locust -f locustfile.py "$cls" --host "$host" \
      --headless -u "$u" -r "$u" -t "$DURACAO" --processes "$PROCESSOS" \
      --csv "/resultados/${nome}_u${u}" --only-summary > /dev/null 2>&1 || true
    sleep 5   # esvazia filas entre execuções
  done
done
docker stats --no-stream > resultados/docker_stats_final.txt 2>/dev/null || true
echo "fim. Rode: python3 graficos.py"
