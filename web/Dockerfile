FROM php:8.3-cli

# Nainstaluj PostgreSQL extension (pro PDO přístup k Postgres)
RUN apt-get update && apt-get install -y libpq-dev \
    && docker-php-ext-install pdo pdo_pgsql \
    && apt-get clean

WORKDIR /app