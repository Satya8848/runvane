#!/bin/bash
# Copyright (c) 2026, Satya and contributors
# For license information, please see license.txt
#
# Start one StackPilot component. Writes common_site_config.json from env vars
# so the same image works in every namespace.
#   web | nginx | worker | scheduler | socketio | migrate | new-site | shell
set -euo pipefail
cd /home/frappe/frappe-bench

cat > sites/common_site_config.json <<JSON
{
  "db_host": "${DB_HOST:-mariadb.launchpad.svc.cluster.local}",
  "db_port": ${DB_PORT:-3306},
  "redis_cache": "redis://${REDIS_HOST:-redis}:6379/0",
  "redis_queue": "redis://${REDIS_HOST:-redis}:6379/1",
  "redis_socketio": "redis://${REDIS_HOST:-redis}:6379/2",
  "socketio_port": 9000,
  "default_site": "${SITE_NAME:-}",
  "serve_default_site": true,
  "use_redis_auth": false,
  "webserver_port": 8000
}
JSON
ls -1 apps > sites/apps.txt

case "${1:-web}" in
  web)
    exec gunicorn --chdir sites --bind 0.0.0.0:8001 --workers "${GUNICORN_WORKERS:-2}" --threads "${GUNICORN_THREADS:-4}" \
      --worker-class gthread --timeout 120 --graceful-timeout 30 --max-requests 2000 --max-requests-jitter 200 \
      --access-logfile - --error-logfile - frappe.app:application --preload ;;
  nginx)
    exec nginx -c /home/frappe/nginx-sidecar.conf -g 'daemon off;' ;;
  worker)
    exec bench worker --queue "${WORKER_QUEUES:-long,default,short}" ;;
  scheduler)
    exec bench schedule ;;
  socketio)
    exec node apps/frappe/socketio.js ;;
  migrate)
    bench --site "${SITE_NAME}" migrate
    exec bench --site "${SITE_NAME}" execute stackpilot.utils.search.rebuild ;;
  new-site)
    # Create the site once (--force: the mounted volume already makes the empty folder);
    # a re-run on an existing site only re-applies its config.
    if [ ! -f "sites/${SITE_NAME}/site_config.json" ]; then
      bench new-site "${SITE_NAME}" --db-root-username root --db-root-password "${DB_ROOT_PASSWORD}" \
        --admin-password "${ADMIN_PASSWORD}" --install-app stackpilot ${DB_NAME:+--db-name "$DB_NAME"} --force \
        --mariadb-user-host-login-scope="%"
    fi
    bench --site "${SITE_NAME}" set-config sp_env "${SP_ENV:-production}"
    bench --site "${SITE_NAME}" set-config meili_url "${MEILI_URL:-http://meilisearch:7700}"
    bench --site "${SITE_NAME}" set-config host_name "https://${SITE_NAME}"
    bench --site "${SITE_NAME}" set-config meili_key "${MEILI_KEY:-}"
    bench --site "${SITE_NAME}" execute stackpilot.install.seed
    exec bench --site "${SITE_NAME}" execute stackpilot.utils.search.rebuild ;;
  shell)
    exec bash ;;
  *)
    exec "$@" ;;
esac
