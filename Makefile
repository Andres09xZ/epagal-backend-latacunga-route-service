# Makefile para gestión de Docker - Backend EPAGAL Latacunga
# Uso: make <comando>

.PHONY: help build up down restart logs clean test

# Variables
COMPOSE=docker-compose
SERVICE_BACKEND=backend
SERVICE_OSRM=osrm
SERVICE_RABBITMQ=rabbitmq

# Comando por defecto
.DEFAULT_GOAL := help

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Comandos de construcción
build: ## Construir todas las imágenes
	$(COMPOSE) build

build-backend: ## Construir solo la imagen del backend
	$(COMPOSE) build $(SERVICE_BACKEND)

build-no-cache: ## Construir sin usar caché
	$(COMPOSE) build --no-cache

# Comandos de ejecución
up: ## Iniciar todos los servicios
	$(COMPOSE) up -d

up-logs: ## Iniciar todos los servicios y ver logs
	$(COMPOSE) up

down: ## Detener todos los servicios
	$(COMPOSE) down

down-volumes: ## Detener servicios y eliminar volúmenes
	$(COMPOSE) down -v

restart: ## Reiniciar todos los servicios
	$(COMPOSE) restart

restart-backend: ## Reiniciar solo el backend
	$(COMPOSE) restart $(SERVICE_BACKEND)

# Comandos de logs
logs: ## Ver logs de todos los servicios
	$(COMPOSE) logs -f

logs-backend: ## Ver logs del backend
	$(COMPOSE) logs -f $(SERVICE_BACKEND)

logs-osrm: ## Ver logs de OSRM
	$(COMPOSE) logs -f $(SERVICE_OSRM)

logs-rabbitmq: ## Ver logs de RabbitMQ
	$(COMPOSE) logs -f $(SERVICE_RABBITMQ)

# Comandos de estado
ps: ## Ver estado de los contenedores
	$(COMPOSE) ps

stats: ## Ver estadísticas de recursos
	docker stats

health: ## Verificar salud de los servicios
	@echo "Verificando backend..."
	@curl -f http://localhost:8081/health || echo "Backend no responde"
	@echo "\nVerificando OSRM..."
	@curl -f http://localhost:5000/health || echo "OSRM no responde"

# Comandos de acceso
shell: ## Acceder al shell del backend
	$(COMPOSE) exec $(SERVICE_BACKEND) bash

shell-python: ## Acceder al shell de Python
	$(COMPOSE) exec $(SERVICE_BACKEND) python

# Comandos de base de datos
db-migrate: ## Ejecutar migraciones
	$(COMPOSE) exec $(SERVICE_BACKEND) alembic upgrade head

db-current: ## Ver estado actual de migraciones
	$(COMPOSE) exec $(SERVICE_BACKEND) alembic current

db-history: ## Ver historial de migraciones
	$(COMPOSE) exec $(SERVICE_BACKEND) alembic history

# Comandos de desarrollo
dev: build up logs ## Setup completo para desarrollo

dev-quick: up logs ## Iniciar servicios existentes y ver logs

reload: down build up ## Reconstruir y reiniciar todo

# Comandos de limpieza
clean: ## Detener servicios y limpiar contenedores
	$(COMPOSE) down
	docker container prune -f

clean-all: ## Limpieza completa (contenedores, imágenes, volúmenes)
	$(COMPOSE) down -v
	docker system prune -a -f --volumes

clean-images: ## Eliminar imágenes del proyecto
	docker images | grep epagal | awk '{print $$3}' | xargs docker rmi -f

# Comandos de testing
test: ## Ejecutar tests en el contenedor
	$(COMPOSE) exec $(SERVICE_BACKEND) pytest

test-coverage: ## Ejecutar tests con cobertura
	$(COMPOSE) exec $(SERVICE_BACKEND) pytest --cov=app --cov-report=html

# Comandos de producción
prod-build: ## Construir para producción
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml build

prod-up: ## Iniciar en modo producción
	$(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d

# Comandos de utilidad
env-example: ## Copiar .env.example a .env
	cp .env.example .env
	@echo ".env creado. Edita las variables antes de continuar."

backup-logs: ## Hacer backup de logs
	mkdir -p logs
	$(COMPOSE) logs > logs/docker-logs-$$(date +%Y%m%d-%H%M%S).log
	@echo "Logs guardados en logs/"

pull: ## Actualizar imágenes base
	$(COMPOSE) pull

# Comandos de información
info: ## Mostrar información del sistema
	@echo "=== Docker Version ==="
	@docker --version
	@echo "\n=== Docker Compose Version ==="
	@docker-compose --version
	@echo "\n=== Contenedores Activos ==="
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo "\n=== Uso de Disco ==="
	@docker system df
