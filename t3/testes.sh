#!/usr/bin/env bash
# Executa os testes de carga: 3 cenários x INSTANCIAS x USUARIOS, e gera os gráficos.
# Pré-requisito: ./criar_posts.sh já executado (locust/posts.env).
# Atenção: muda a escala do serviço wordpress e reinicia o nginx a cada quantidade de instâncias.
# Valores abaixo podem ser sobrescritos por variáveis de ambiente, ex.: DURACAO=30s ./testes.sh
set -euo pipefail
cd "$(dirname "$0")"

DURACAO="${DURACAO:-60s}"             # duração de cada execução
INSTANCIAS="${INSTANCIAS:-1 2 3}"     # quantidades de instâncias do WordPress
USUARIOS="${USUARIOS:-10 100 1000}"   # quantidades de usuários simultâneos
CENARIOS="${CENARIOS:-1 2 3}"
TAXA_MAXIMA=100                       # usuários criados por segundo (no máximo)
ESPERA_NGINX=5                        # segundos para o nginx subir após reiniciar
ALVO="http://nginx"                   # nome do serviço no docker-compose
POSTS_ENV="locust/posts.env"
RESULTADOS="/mnt/locust/results"      # ./locust/results visto de dentro do contêiner

carregar_posts() {
  if [ ! -f "$POSTS_ENV" ]; then
    echo "$POSTS_ENV não encontrado. Rode ./criar_posts.sh antes." >&2
    exit 1
  fi
  source "$POSTS_ENV"
  mkdir -p locust/results
}

escalar_wordpress() {  # $1 = número de instâncias
  docker compose up -d --scale wordpress="$1" db wordpress nginx
  docker compose restart nginx   # o nginx só resolve os IPs das réplicas ao iniciar
  sleep "$ESPERA_NGINX"
}

rodar_teste() {  # $1 = cenário, $2 = instâncias, $3 = usuários
  local post_var="S$1"
  local taxa=$(( $3 < TAXA_MAXIMA ? $3 : TAXA_MAXIMA ))

  echo ">>> cenário $1 | $2 instância(s) | $3 usuários"
  docker compose run --rm -T -e POST="/?p=${!post_var}" locust \
    -f /mnt/locust/locustfile.py -H "$ALVO" --headless \
    -u "$3" -r "$taxa" -t "$DURACAO" \
    --csv "$RESULTADOS/c$1_i$2_u$3" --only-summary || true
}

main() {
  carregar_posts
  for instancias in $INSTANCIAS; do
    escalar_wordpress "$instancias"
    for cenario in $CENARIOS; do
      for usuarios in $USUARIOS; do
        rodar_teste "$cenario" "$instancias" "$usuarios"
      done
    done
  done
  python3 graficos.py
}

main
