#!/usr/bin/env bash
# Bateria: 4 tecnologias x USUARIOS. Resultado: resultados/<tecnologia>_u<usuarios>_stats.csv
# Ex.: DURACAO=60s USUARIOS="10 100" ./testes.sh
set -uo pipefail
cd "$(dirname "$0")"
DURACAO="${DURACAO:-30s}"; USUARIOS="${USUARIOS:-10 50 200 500}"; PROCESSOS="${PROCESSOS:-2}"
mkdir -p resultados
docker compose up -d --build rest graphql soap grpc
sleep 5
for u in $USUARIOS; do
  for t in rest:RestUser:http://rest:8000 graphql:GraphqlUser:http://graphql:8000 soap:SoapUser:http://soap:8000 grpc:GrpcUser:grpc:8000; do
    nome=${t%%:*}; resto=${t#*:}; cls=${resto%%:*}; host=${resto#*:}
    docker compose run --rm --no-deps locust locust -f locustfile.py "$cls" --host "$host" \
      --headless -u "$u" -r "$u" -t "$DURACAO" --processes "$PROCESSOS" \
      --csv "/resultados/${nome}_u${u}" --only-summary > /dev/null 2>&1 || true
    sleep 5   # esvazia filas entre execuções
  done
done
docker stats --no-stream > resultados/docker_stats_final.txt 2>/dev/null || true
echo "fim. Rode: python3 graficos.py"
