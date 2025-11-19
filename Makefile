# Makefile for django project
-include makefiles/fail2ban.mk
-include makefiles/vps.mk

include .env
export

install_whl:
	pip install requirements/django_nose-1.4.7-py2.py3-none-any.whl

install_prod: install_whl
	pip install -r requirements/prod.txt

install: install_whl
	pip install -r requirements/dev.txt

uninstall:
	pip uninstall -r requirements/dev.txt

runserver:
# 	python manage.py runserver 9000
	daphne -p 9000 src.asgi:application

run: runserver

check:
	python manage.py check

shell:
	python manage.py shell_plus

migrations:
	python manage.py makemigrations

superuser:
	python manage.py createsuperuser

migrate:
	python manage.py migrate

collectstatic:
	python manage.py collectstatic

collectstatic_force:
	python manage.py collectstatic --noinput --clear


import_countries:
	python manage.py update_countries_plus

import_cities:
	python manage.py cities_light


diff:
	git add -N .
	git diff > a.diff
	code a.diff

rmdiff:
	rm a.diff

env:
	python3 -m venv env

g:
	gunicorn src.wsgi:application --bind 0.0.0.0:8000

render-start-command:
	gunicorn src.wsgi:application --bind 0.0.0.0:$PORT

# wsl/linux
redis:
	@echo "Starting Redis..."
	sudo service redis-server start

check-redis:
	@echo "Checking Redis..."
	sudo service redis-server status

stop-redis:
	@echo "Stopping Redis..."
	sudo service redis-server stop

websocket:
	@echo "Running Websocket Test..."
	websocat ws://127.0.0.1:9000/api/v1/ws/





# ----------------------------------------------------------------------------------
# THESE ARE ALL LOADED FROM .ENV

# DOMAIN ?= api.zeefas.com
# EMAIL ?= williamusanga23@gmail.com
# COMPOSE_FILE ?= docker-compose.yaml

# # Container names
# CERTBOT_CONTAINER ?= certbot
# NGINX_CONTAINER ?= nginx
# POSTGRES_CONTAINER ?= postgres
# REDIS_CONTAINER ?= redis
# DJANGO_APP_CONTAINER ?= django_app

# # NETWORK
# NETWORK_NAME ?= zeefas_app_network
# POSTGRES_VOLUME_NAME ?= zeefas_postgres_data
# STATIC_VOLUME_NAME ?= zeefas_static_volume
# MEDIA_VOLUME_NAME ?= zeefas_media_volume

.PHONY: up certs restart https down help setup-cert 


up:
	@echo "Starting initial run with HTTP only..."
	docker compose -f $(COMPOSE_FILE) up -d

certs: up
	@echo "Waiting for Nginx to be ready..."
	python3 scripts/wait_for_nginx.py
	@echo "Generating Let's Encrypt certificates for $(DOMAIN)..."
	docker compose -f $(COMPOSE_FILE) run --rm $(CERTBOT_CONTAINER) certonly --webroot --webroot-path=/var/www/certbot \
		--email "$(DOCKER_EMAIL)" --agree-tos --no-eff-email --force-renewal -d $(DOMAIN)
	@echo "Certificate generation complete."

restart:
	@echo "Regenerating Nginx config with HTTPS..."
	docker compose -f $(COMPOSE_FILE) exec $(NGINX_CONTAINER) /bin/bash /start-nginx.sh
	@echo "Restarting Nginx..."
	docker compose -f $(COMPOSE_FILE) restart $(NGINX_CONTAINER)

https: up certs restart
	@echo "HTTPS setup complete! Access via https://$(DOMAIN)"

down:
	@echo "Stopping all services..."
	docker compose -f $(COMPOSE_FILE) down

setup-cert:
	@echo "Generating Let's Encrypt certificates for $(DOMAIN)..."
	docker run --rm --name temp_certbot --network $(NETWORK_NAME) \
		-v ./certbot/conf:/etc/letsencrypt \
		-v ./certbot/www:/var/www/certbot \
		certbot/certbot certonly --webroot -w /var/www/certbot \
		--email $(DOCKER_EMAIL) --agree-tos --no-eff-email -d $(DOMAIN)
	@echo "Certificate generation complete."

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  up      Start services (HTTP only)."
	@echo "  certs   Generate/renew certificates (requires 'up')."
	@echo "  restart Reload Nginx with HTTPS (requires 'certs')."
	@echo "  https   Full HTTPS setup (up -> certs -> restart)."
	@echo "  down    Stop and remove services."
	@echo "  help    Show this help."

rebuild:
	@echo "Rebuilding everything..."
	docker compose -f docker-compose.yaml up -d --build

rebuild-app:
	@echo "Rebuilding Django app container..."
	docker compose -f docker-compose.yaml up -d --build ${DJANGO_APP_CONTAINER}


collectstatic:
	docker compose exec ${DJANGO_APP_CONTAINER} python manage.py collectstatic --noinput

manual-collectstatic:
	docker run --rm \
		-v $$(pwd)/src/static:/source \
		-v static_volume:/dest \
		alpine sh -c "cp -r /source/* /dest/"


list-containers:
	docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

list-volumes:
	docker volume ls --format "table {{.Name}}\t{{.Driver}}"

list-networks:
	docker network ls --format "table {{.Name}}\t{{.Driver}}"

list-images:
	docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"

health-check:
	docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $(docker ps -q)

dockerness:
	@echo "====== CONTAINERS ======="
	@docker ps -a --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "====== VOLUMES =========="
	@docker volume ls --format "table {{.Name}}\t{{.Driver}}"
	@echo ""
	@echo "====== NETWORKS ========="
	@docker network ls --format "table {{.Name}}\t{{.Driver}}"
	@echo ""
	@echo "====== IMAGES ==========="
	@docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"
	@echo ""
	@echo "====== HEALTH CHECK ====="
	@containers=$$(docker ps -q); \
	if [ -n "$$containers" ]; then \
		docker inspect --format='{{.Name}}: {{.State.Health.Status}}' $$containers; \
	else \
		echo "No running containers"; \
	fi


	
lazydocker:
	docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock -v /your/config:/.config/jesseduffield/lazydocker lazyteam/lazydocker
