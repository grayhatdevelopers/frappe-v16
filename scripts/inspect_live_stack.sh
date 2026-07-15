#!/usr/bin/env bash
set -Eeuo pipefail

backend_container="${1:?usage: inspect_live_stack.sh BACKEND_CONTAINER [DB_CONTAINER]}"
db_container="${2:-}"

print_container_image() {
  local container="$1"
  local image_id
  image_id="$(docker inspect --format '{{.Image}}' "${container}")"
  printf 'container=%s configured_image=%s image_id=%s\n' \
    "${container}" \
    "$(docker inspect --format '{{.Config.Image}}' "${container}")" \
    "${image_id}"
  docker image inspect --format 'repo_digests={{json .RepoDigests}}' "${image_id}"
}

echo '== Backend image =='
print_container_image "${backend_container}"

echo '== Backend persistent mounts =='
docker inspect --format '{{range .Mounts}}{{println .Destination "=" .Name}}{{end}}' "${backend_container}"

echo '== Bench applications =='
if ! docker exec "${backend_container}" bench version --format plain; then
  docker exec "${backend_container}" bench version
fi

echo '== Bench sites =='
docker exec "${backend_container}" bench list-sites

echo '== Non-secret common database endpoint =='
docker exec "${backend_container}" python -c \
  'import json; data=json.load(open("sites/common_site_config.json")); print(json.dumps({key: data.get(key) for key in ("db_host", "db_port")}))'

if [[ -n "${db_container}" && "${db_container}" != '-' ]]; then
  echo '== Database image =='
  print_container_image "${db_container}"

  echo '== Database version =='
  docker exec "${db_container}" sh -lc \
    'password="${MARIADB_ROOT_PASSWORD:-${MYSQL_ROOT_PASSWORD:-}}"; test -n "$password"; mariadb --batch --skip-column-names -uroot --password="$password" -e "SELECT VERSION();"'
else
  echo 'Database container not supplied; confirm the external database version separately.'
fi
