#!/usr/bin/env bash
# Cria no WordPress os posts dos 3 cenários e grava os IDs em locust/posts.env.
# Pré-requisito: aplicação no ar (docker compose up -d) e WordPress já instalado.
# Pode ser executado de novo: posts com o mesmo título são reaproveitados.
set -euo pipefail
cd "$(dirname "$0")"

POSTS_ENV="locust/posts.env"
CONTEUDO_NO_WPCLI="/conteudo"   # pasta ./conteudo montada no contêiner wpcli

TITULO_1="Cenário 1 - Imagem de 1MB"
ARQUIVO_1="imagem_1mb.jpg"
TITULO_2="Cenário 2 - Texto de 400KB"
ARQUIVO_2="texto_400kb.html"
TITULO_3="Cenário 3 - Imagem de 300KB"
ARQUIVO_3="imagem_300kb.jpg"

wp() {
  docker compose --progress quiet run --rm -T wpcli wp "$@"
}

verificar_wordpress() {
  if ! wp core is-installed; then
    echo "WordPress não instalado. Suba com 'docker compose up -d' e instale em http://localhost" >&2
    exit 1
  fi
}

buscar_post() {  # $1 = título -> ID do post publicado com esse título (vazio se não existir)
  wp post list --post_type=post --post_status=publish --title="$1" --field=ID | head -n1
}

criar_post_com_imagem() {  # $1 = título, $2 = arquivo de imagem
  local id anexo url
  id=$(wp post create --post_title="$1" --post_status=publish --porcelain)
  anexo=$(wp media import "$CONTEUDO_NO_WPCLI/$2" --post_id="$id" --porcelain)
  url=$(wp post get "$anexo" --field=guid)
  wp post update "$id" --post_content="<p>$1</p><img src=\"$url\" />" >/dev/null
  echo "$id"
}

criar_post_com_texto() {  # $1 = título, $2 = arquivo HTML com o conteúdo
  wp post create "$CONTEUDO_NO_WPCLI/$2" --post_title="$1" --post_status=publish --porcelain
}

garantir_post() {  # $1 = tipo (imagem|texto), $2 = título, $3 = arquivo
  local id
  id=$(buscar_post "$2")
  if [ -z "$id" ]; then
    id=$("criar_post_com_$1" "$2" "$3")
  fi
  echo "$id"
}

main() {
  python3 gerar_conteudo.py
  verificar_wordpress

  local s1 s2 s3
  s1=$(garantir_post imagem "$TITULO_1" "$ARQUIVO_1")
  s2=$(garantir_post texto  "$TITULO_2" "$ARQUIVO_2")
  s3=$(garantir_post imagem "$TITULO_3" "$ARQUIVO_3")

  printf 'S1=%s\nS2=%s\nS3=%s\n' "$s1" "$s2" "$s3" | tee "$POSTS_ENV"
}

main
