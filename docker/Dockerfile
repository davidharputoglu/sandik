# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
# Image sandik — multi-architecture : linux/amd64, linux/arm64, linux/arm/v7 (Raspberry Pi 3+).
# Construction (depuis la racine du dépôt) : docker build -f docker/Dockerfile -t sandik .

# 1) Interface : compilée une seule fois, sur la machine de construction (rapide, même pour ARM)
FROM --platform=$BUILDPLATFORM node:22-alpine AS front
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN SANDIK_STATIC_DIR=/static npx vite build

# 2) Serveur
FROM python:3.12-slim
ARG TARGETARCH
ARG VERSION=0.1.0
LABEL org.opencontainers.image.title="sandik" \
      org.opencontainers.image.description="CRM, devis et factures — logiciel libre" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.authors="David HARPUTOGLU <kasparof57@gmail.com>" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later" \
      org.opencontainers.image.source="https://github.com/davidharputoglu/sandik"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SANDIK_DATA_DIR=/data SANDIK_AUTH=1 SANDIK_PORT=8460
WORKDIR /app
COPY pyproject.toml README.md LICENSE NOTICE.md THIRD_PARTY_NOTICES.md ./
COPY licenses ./licenses
COPY sandik ./sandik
COPY --from=front /static ./sandik/static
# PostgreSQL : pilote binaire sur amd64/arm64 ; sur ARM 32 bits, pilote pur Python + libpq du système
RUN if [ "$TARGETARCH" = "arm" ]; then \
        apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/* \
        && pip install . "psycopg>=3.1"; \
    else pip install ".[postgres]"; fi \
    && useradd --system --uid 1000 --home /data sandik && mkdir -p /data && chown sandik:sandik /data
USER sandik
VOLUME ["/data"]
# Port d'écoute : variable SANDIK_PORT (8460 par défaut)
EXPOSE 8460
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/health' % os.environ.get('SANDIK_PORT', '8460'), timeout=4)" || exit 1
CMD ["sandik", "--host", "0.0.0.0"]
