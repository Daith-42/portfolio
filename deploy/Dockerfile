# Image du portfolio : nginx officiel, sans droits root, avec le site copié dedans.
FROM nginxinc/nginx-unprivileged:1.30-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY site/ /usr/share/nginx/html/

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q --spider http://127.0.0.1:8080/ || exit 1
