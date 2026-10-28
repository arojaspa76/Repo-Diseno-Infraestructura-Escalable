# Guía de Despliegue Local — LLM Gateway
## Sesión 3: Kubernetes, Docker y Contenedores para LLMs
**BSG Institute — Diseño de Infraestructura Escalable para LLMs**

> **Entorno:** Ubuntu 24.04 LTS · Docker · Minikube · Ollama local  
> **Última actualización:** 2026-10-28

## Asignación de puertos

Para evitar conflictos con otras aplicaciones que usan el puerto 8000, este stack usa los siguientes puertos en el host:

| Servicio | Puerto host | Puerto interno | Protocolo |
|----------|-------------|----------------|-----------|
| llm-gateway (Docker test) | **8081** | 8000 | HTTP |
| llm-gateway (Kubernetes NodePort) | **30880** | 8000 | HTTP |
| Ollama | 11434 | 11434 | HTTP |
| Portainer CE | 9443 | 9443 | HTTPS |
| Kubernetes Dashboard | 8443 | 8443 | HTTPS |

> El puerto interno 8000 es invisible fuera del contenedor — solo los puertos del host importan para evitar conflictos.

---

## Prerrequisitos

Antes de iniciar, verificar que estén instalados:

```bash
docker --version        # Docker Engine 24+
kubectl version --client # kubectl v1.28+
minikube version        # Minikube v1.32+
ollama --version        # Ollama 0.4+
curl --version
```

Ollama debe estar corriendo con al menos un modelo descargado:

```bash
# Verificar que Ollama responde
curl http://localhost:11434/api/tags

# Si no está corriendo, iniciarlo
ollama serve &

# Modelos recomendados para esta sesión
ollama pull llama3.2:1b   # ~1.3 GB — rápido, ideal para demos
ollama pull llama3.2:3b   # ~2.0 GB — mejor calidad
```

---

## PASO 0 — Configurar Ollama para escuchar en todas las interfaces

> **¿Por qué este paso?**  
> Por defecto, Ollama solo escucha en `127.0.0.1:11434` (solo accesible desde el mismo equipo, proceso a proceso).  
> Los pods de Kubernetes corren en una red interna separada de Ubuntu — no son el mismo equipo desde la perspectiva de red.  
> Para que los pods puedan llegar a Ollama, este debe escuchar en `0.0.0.0:11434` (todas las interfaces de red del host).

### 0.1 Verificar en qué dirección está escuchando Ollama actualmente

```bash
ss -tlnp | grep 11434
```

Interpreta la salida:

| Salida | Significado |
|--------|-------------|
| `127.0.0.1:11434` | ❌ Solo local — los pods NO pueden alcanzarlo |
| `0.0.0.0:11434` o `*:11434` | ✅ Todas las interfaces — los pods SÍ pueden alcanzarlo |

Si ya aparece `0.0.0.0` o `*`, puedes saltar al PASO 0.3.

### 0.2 Reconfigurar el servicio systemd de Ollama

Ollama en Ubuntu corre como un servicio del sistema (similar a un proceso en segundo plano que se inicia automáticamente). Para cambiar cómo arranca, se crea un archivo de configuración de "sobrescritura" (override):

```bash
# Crear el directorio de override (si no existe)
sudo mkdir -p /etc/systemd/system/ollama.service.d

# Crear el archivo de configuración que cambia la dirección de escucha
sudo tee /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
```

> **¿Qué hace este archivo?**  
> Le dice al servicio Ollama que use la variable de entorno `OLLAMA_HOST=0.0.0.0:11434` cuando arranque.  
> `0.0.0.0` significa "escuchar en todas las interfaces de red disponibles".

```bash
# Recargar la configuración de systemd para que lea el nuevo archivo
sudo systemctl daemon-reload

# Reiniciar Ollama con la nueva configuración
sudo systemctl restart ollama

# Esperar 3 segundos y verificar el estado
sleep 3 && sudo systemctl status ollama
```

La salida del status debe mostrar `Active: active (running)`.

### 0.3 Confirmar que Ollama ahora escucha en todas las interfaces

```bash
ss -tlnp | grep 11434
```

Ahora debe aparecer `0.0.0.0:11434` o `*:11434`. Si sigue en `127.0.0.1`, verificar que el archivo se guardó correctamente:

```bash
cat /etc/systemd/system/ollama.service.d/override.conf
```

---

## PASO 1 — Obtener la IP del host que usarán los pods de Kubernetes

> **¿Por qué necesitamos la IP?**  
> Los pods de Kubernetes no conocen el término "localhost" del host Ubuntu.  
> Necesitan una dirección IP concreta para poder comunicarse con Ollama.  
> Esta IP cambia según el equipo y la red — por eso hay que obtenerla dinámicamente.

### 1.1 Ver las IPs del equipo

```bash
hostname -I
```

Ejemplo de salida:
```
172.23.35.21 172.17.0.1 192.168.49.1
```

Cada número separado por espacio es una dirección IP de una interfaz de red diferente:

| IP (ejemplo) | Interfaz | Descripción |
|--------------|----------|-------------|
| `172.23.35.21` | eth0 / WSL2 | ✅ IP principal del host — la que deben usar los pods |
| `172.17.0.1` | docker0 | Bridge de Docker |
| `192.168.49.1` | br-minikube | Gateway de Minikube hacia el host — **NO usar** |

**La IP que necesitas es la primera** (la más a la izquierda), que corresponde a la interfaz principal de red del equipo.

### 1.2 Verificar que Ollama responde desde esa IP

```bash
# Reemplaza 172.23.35.21 con la IP que obtuviste en el paso anterior
curl http://172.23.35.21:11434/api/tags
```

Respuesta esperada (lista de modelos disponibles):
```json
{"models":[{"name":"llama3.2:1b","model":"llama3.2:1b",...}]}
```

Si no responde, Ollama todavía no está escuchando en esa interfaz. Volver al PASO 0.

### 1.3 Anotar la IP para usarla en el deployment

Guarda la IP en una variable de shell para usarla en los siguientes pasos:

```bash
# Extrae automáticamente la primera IP
HOST_IP=$(hostname -I | awk '{print $1}')
echo "IP del host: $HOST_IP"
```

---

## PASO 2 — Clonar el repositorio

```bash
git clone https://github.com/arojaspa76/Repo-Diseno-Infraestructura-Escalable.git
cd Repo-Diseno-Infraestructura-Escalable/sesion_3
```

Verificar la estructura:

```bash
ls -la
# Debe mostrar: app/  docker/  kubernetes/  requirements.txt
# requirements-docker-local.txt  .env.example
```

---

## PASO 3 — Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar con el editor de preferencia
nano .env
```

Contenido mínimo para ejecución local (solo Ollama):

```env
ENVIRONMENT=production
OLLAMA_BASE_URL=http://localhost:11434
LOG_LEVEL=INFO
PORT=8000
```

> **Nota:** Las variables de Azure, GCP y AWS pueden dejarse vacías para la demo local.

---

## PASO 4 — Construir la imagen Docker

Se usa `requirements-docker-local.txt` en lugar de `requirements.txt` para obtener una imagen de ~258 MB en lugar de ~10 GB, eliminando las SDKs de cloud que el código no utiliza en modo local.

```bash
# Desde el directorio sesion_3/
docker build -t llm-gateway:latest -f docker/Dockerfile .
```

Verificar que la imagen se construyó correctamente:

```bash
docker images llm-gateway
# REPOSITORY     TAG       SIZE
# llm-gateway    latest    ~258MB
```

> **¿Por qué tan pequeña?** El Dockerfile usa multi-stage build:  
> - Stage 1 (builder): instala dependencias con pip  
> - Stage 2 (runtime): copia solo los archivos necesarios, sin herramientas de build  
> - `requirements-docker-local.txt` excluye SDKs cloud, LangChain, ChromaDB y sentence-transformers

---

## PASO 5 — Probar la imagen localmente (Docker)

Este paso valida que la imagen funciona antes de desplegarla en Kubernetes.

### 5.1 Levantar el contenedor

```bash
docker run -d \
  --name llm-gateway-test \
  -p 8081:8000 \
  --env-file .env \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --add-host=host.docker.internal:host-gateway \
  llm-gateway:latest
```

> **¿Por qué `host.docker.internal`?**  
> El contenedor tiene su propio namespace de red. `localhost` dentro del contenedor apunta al contenedor, no al host. `host.docker.internal` es el DNS especial que Docker resuelve hacia la IP del host, permitiendo que el contenedor alcance el Ollama que corre en Ubuntu.  
> En Linux se requiere `--add-host=host.docker.internal:host-gateway` porque no se resuelve automáticamente (en Mac/Windows sí).

### 5.2 Verificar que arrancó

```bash
# Ver estado del contenedor
docker ps

# Ver logs (esperar: "Application startup complete")
docker logs llm-gateway-test
```

### 5.3 Probar el health check

```bash
curl -s http://localhost:8081/health | python3 -m json.tool
```

Respuesta esperada (HTTP 200):

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ollama_connected": true,
  "ollama_models": ["llama3.2:1b", "llama3.2:3b"],
  "timestamp": "2026-10-28T03:57:16.906507",
  "environment": "production"
}
```

> Si `status` es `degraded`, Ollama no está accesible desde el contenedor. Verificar que `ollama serve` esté corriendo en el host.

### 5.4 Probar un chat

```bash
curl -s -X POST http://localhost:8081/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es Kubernetes en una oración?", "model": "llama3.2:1b", "provider": "ollama"}' \
  | python3 -m json.tool
```

### 5.5 Ver métricas Prometheus

```bash
curl http://localhost:8081/metrics
```

O abrir en el navegador: `http://localhost:8081/metrics`

Salida esperada (formato Prometheus text exposition):

```
# HELP llm_gateway_requests_total Total de requests recibidos
# TYPE llm_gateway_requests_total counter
# HELP llm_gateway_request_duration_seconds Latencia de requests en segundos
# TYPE llm_gateway_request_duration_seconds histogram
# HELP llm_gateway_ollama_requests_total Total de requests enviados a Ollama
# TYPE llm_gateway_ollama_requests_total counter
# HELP llm_gateway_active_requests Requests activos en este momento
# TYPE llm_gateway_active_requests gauge
llm_gateway_active_requests 0.0
```

También se incluyen métricas estándar del proceso Python: `python_gc_*`, `process_virtual_memory_bytes`, `process_cpu_seconds_total`, etc.

> **¿Por qué Prometheus?** El endpoint `/metrics` expone telemetría en el formato estándar que Prometheus puede scrapear. En producción, un Prometheus Server consume este endpoint periódicamente y Grafana visualiza las series de tiempo. En esta demo local, el endpoint confirma que la instrumentación está activa y funcionando.

### 5.6 Ver la documentación interactiva

Abrir en el navegador:

```
http://localhost:8081/docs
```

> Swagger UI permite explorar y ejecutar todos los endpoints directamente desde el navegador. El endpoint `/metrics` no aparece en Swagger por diseño (`include_in_schema=False`) — es consumido por Prometheus, no por usuarios.

### 5.7 Detener y limpiar el contenedor de prueba

```bash
docker stop llm-gateway-test
docker rm llm-gateway-test
```

---

## PASO 6 — Actualizar el manifest de Kubernetes con tu IP

Antes de desplegar en Kubernetes, hay que informarle al manifest cuál es la IP del host donde corre Ollama. Esto se hace en el archivo `kubernetes/local/deployment.yaml`.

### 6.1 Ver la sección que hay que modificar

Abrir el archivo:

```bash
nano kubernetes/local/deployment.yaml
```

Buscar la sección `hostAliases` (aproximadamente en la línea 74):

```yaml
      hostAliases:
        - ip: "172.23.35.21"      # <-- CAMBIAR ESTA IP
          hostnames:
            - "host.docker.internal"
```

### 6.2 Reemplazar la IP con la tuya

Usando la variable `HOST_IP` obtenida en el PASO 1:

```bash
# Ver tu IP (si cerraste la terminal)
HOST_IP=$(hostname -I | awk '{print $1}')
echo "Tu IP es: $HOST_IP"

# Reemplazar en el archivo de forma automática
sed -i "s/- ip: \".*\"/- ip: \"$HOST_IP\"/" kubernetes/local/deployment.yaml

# Verificar el cambio
grep -A2 "hostAliases" kubernetes/local/deployment.yaml
```

Debe mostrar tu IP actualizada:
```yaml
      hostAliases:
        - ip: "172.23.35.21"      # <-- tu IP real
          hostnames:
```

> **¿Qué hace `hostAliases`?**  
> Es como editar el archivo `/etc/hosts` dentro de cada pod.  
> Cuando el código en el pod intenta conectarse a `host.docker.internal`, Kubernetes lo resuelve a la IP que pusiste aquí.  
> Sin este paso, los pods no sabrían cómo llegar al Ollama del host.

> **⚠️ Nota importante:** La IP `192.168.49.1` que aparece en algunos tutoriales es la IP del gateway de Minikube hacia el host en configuraciones con VirtualBox. Con el driver Docker en Linux (o WSL2), esa IP NO es alcanzable desde los pods. Siempre usar la IP obtenida con `hostname -I`.

---

## PASO 7 — Iniciar Minikube

```bash
# Verificar estado actual
minikube status

# Si no está corriendo, iniciarlo
minikube start --driver=docker --cpus=2 --memory=4096

# Verificar que el cluster responde
kubectl cluster-info
kubectl get nodes
```

Salida esperada de `kubectl get nodes`:

```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.31.x
```

---

## PASO 8 — Cargar la imagen en Minikube

Minikube tiene su propio registro de imágenes interno, separado del Docker del host. La imagen debe cargarse explícitamente.

```bash
minikube image load llm-gateway:latest

# Verificar que quedó cargada
minikube image ls | grep llm-gateway
# Debe mostrar: docker.io/library/llm-gateway:latest
```

> **¿Por qué este paso?** En producción se usaría un registry (Docker Hub, ECR, GCR, ACR). En local, `minikube image load` es el equivalente: copia la imagen al daemon Docker interno de Minikube sin necesidad de un registry externo. El `deployment.yaml` usa `imagePullPolicy: IfNotPresent` para que Kubernetes use la imagen local sin intentar descargarla.

---

## PASO 9 — Desplegar en Kubernetes

```bash
kubectl apply -f kubernetes/local/deployment.yaml
```

Este comando crea todos los recursos definidos en el manifiesto:

| Recurso | Nombre | Descripción |
|---------|--------|-------------|
| Namespace | `llm-session3` | Aísla los recursos de esta demo |
| ConfigMap | `llm-gateway-config` | Variables de configuración no secretas |
| Deployment | `llm-gateway` | 2 réplicas del API Gateway |
| Service | `llm-gateway-service` | NodePort en puerto **30880** |
| HPA | `llm-gateway-hpa` | Autoscaling CPU 70%, mem 80% |

> **Nota:** Ollama NO se despliega dentro del cluster — usa el Ollama instalado en el host Ubuntu (configurado en los pasos anteriores).

---

## PASO 10 — Verificar el despliegue

### 10.1 Ver todos los recursos del namespace

```bash
kubectl get all -n llm-session3
```

### 10.2 Esperar que los pods estén Ready

```bash
kubectl get pods -n llm-session3 -w
# Esperar que todos muestren: Running
# Ctrl+C para salir del watch
```

Salida esperada cuando todo está bien:
```
NAME                           READY   STATUS    RESTARTS   AGE
llm-gateway-xxxxxxxxx-xxxxx    1/1     Running   0          30s
llm-gateway-xxxxxxxxx-xxxxx    1/1     Running   0          30s
```

> Si el STATUS es `CrashLoopBackOff`, ver la sección de Troubleshooting.

### 10.3 Ver logs de un pod

```bash
# Obtener el nombre de los pods
kubectl get pods -n llm-session3

# Ver logs de todos los pods del deployment de una vez
kubectl logs -l app=llm-gateway -n llm-session3 --tail=20

# Seguir logs en tiempo real de un pod específico (reemplazar <pod-name>)
kubectl logs -f <pod-name> -n llm-session3
```

Los logs deben mostrar:
```
🚀 Iniciando LLM Gateway API...
✅ LLM Gateway API lista en http://localhost:8000
```

> Si aparece `⚠️ Ollama no está disponible en localhost:11434`, ignorar este warning — es un mensaje informativo del arranque que usa `localhost` como texto fijo, pero la URL real viene del ConfigMap (`host.docker.internal:11434`).

### 10.4 Describir un pod (útil para troubleshooting)

```bash
kubectl describe pod <pod-name> -n llm-session3
```

---

## PASO 11 — Acceder al servicio

En Minikube con driver Docker en Linux, el NodePort no es accesible directamente desde el host. Se necesita crear un **tunnel** (un puente de red temporal):

```bash
# Crear el tunnel — este comando queda bloqueando la terminal
minikube service llm-gateway-service -n llm-session3 --url
```

Salida esperada:
```
http://127.0.0.1:45643
```

> **⚠️ Importante: el tunnel requiere mantener la terminal abierta.**  
> Mientras este comando esté corriendo, el servicio está accesible.  
> Si cierras esta terminal, el acceso se pierde (pero los pods siguen corriendo).  
> Abre una **segunda terminal** para hacer las pruebas.

### Probar el servicio (en una segunda terminal)

```bash
# Reemplazar con la URL del comando anterior
GATEWAY_URL="http://127.0.0.1:45643"

# Health check
curl -s $GATEWAY_URL/health | python3 -m json.tool

# Chat
curl -s -X POST $GATEWAY_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Qué es un pod en Kubernetes?", "model": "llama3.2:1b"}' \
  | python3 -m json.tool
```

Respuesta esperada del health check:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "ollama_connected": true,
    "ollama_models": ["llama3.2:1b"],
    "environment": "local"
}
```

---

## PASO 12 — Kubernetes Dashboard

```bash
# Abrir el dashboard en el navegador (abre automáticamente)
minikube dashboard
```

Desde el dashboard se puede:
- Ver el estado de los pods en tiempo real
- Inspeccionar logs
- Editar manifiestos
- Ver métricas de CPU y memoria
- Escalar deployments manualmente

---

## Troubleshooting

### Pods en estado CrashLoopBackOff

```bash
# Ver los logs del pod que falla
kubectl logs <pod-name> -n llm-session3

# Ver eventos del pod (muestra errores de arranque)
kubectl describe pod <pod-name> -n llm-session3 | grep -A20 "Events:"
```

**Causa más común:** Ollama no es alcanzable desde los pods.

Diagnóstico desde dentro del pod:
```bash
# Abrir una shell dentro del pod
kubectl exec -it <pod-name> -n llm-session3 -- /bin/sh

# Intentar conectarse a Ollama
curl http://host.docker.internal:11434/api/tags

# Ver qué IP tiene host.docker.internal dentro del pod
cat /etc/hosts

# Salir del pod
exit
```

Si el curl falla (exit code 7 = "Failed to connect"), verificar:

1. **¿Ollama escucha en 0.0.0.0?** → `ss -tlnp | grep 11434` en el host
2. **¿La IP en hostAliases es correcta?** → `hostname -I` en el host y comparar con el deployment.yaml
3. **¿El firewall bloquea el puerto?** → `sudo ufw status` (si está activo)

### Ollama no disponible desde el contenedor Docker (PASO 5)

```bash
# Síntoma: health retorna "degraded"
# Verificar que Ollama corre en el host
curl http://localhost:11434/api/tags

# Al correr en Docker directo (no Kubernetes), agregar:
--add-host=host.docker.internal:host-gateway \
-e OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Imagen no encontrada en Minikube

```bash
# Síntoma: ErrImagePull o ImagePullBackOff en los pods
kubectl describe pod <pod-name> -n llm-session3 | grep -A5 "Events"

# Solución: recargar la imagen
minikube image load llm-gateway:latest
kubectl rollout restart deployment/llm-gateway -n llm-session3
```

### Pods en estado Pending

```bash
# Ver por qué no schedulean
kubectl describe pod <pod-name> -n llm-session3 | grep -A10 "Events"

# Verificar recursos disponibles en Minikube
kubectl top nodes
minikube status
```

### El tunnel de minikube service se cierra

Si accidentalmente cerraste la terminal con el tunnel:
```bash
# Simplemente volver a ejecutar el comando
minikube service llm-gateway-service -n llm-session3 --url
# La URL puede cambiar (diferente puerto), actualizar las pruebas con la nueva URL
```

### Limpiar y reiniciar desde cero

```bash
# Eliminar TODOS los recursos del namespace (pods, services, configmaps, etc.)
# kubectl delete namespace borra absolutamente todo dentro del namespace
kubectl delete namespace llm-session3

# Detener Minikube
minikube stop

# Eliminar el cluster completo (libera todos los recursos de Docker)
minikube delete

# Eliminar la imagen Docker del host
docker rmi llm-gateway:latest
```

---

## Resumen de cambios aplicados al código base

| Archivo | Cambio | Motivo |
|---------|--------|--------|
| `docker/Dockerfile` | `python:3.11-slim` → `python:3.12-slim` | Versión LTS actual |
| `docker/Dockerfile` | `--target=/install` → `--prefix=/install` | Corrige rutas de binarios (`uvicorn not found`) |
| `docker/Dockerfile` | Dos `COPY --from=builder` separados | Copia libs y binarios correctamente |
| `requirements-docker-local.txt` | Nuevo archivo sin SDKs cloud | Imagen de 10 GB → 258 MB |
| `app/utils/ollama_client.py` | URL hardcodeada → `os.getenv("OLLAMA_BASE_URL", ...)` | Permite configurar Ollama vía variable de entorno |
| `app/models/schemas.py` | `timestamp: datetime` → `timestamp: str` con `.isoformat()` | Corrige `datetime is not JSON serializable` |
| `requirements.txt` | `vertexai==1.71.1`, `google-cloud-aiplatform==1.71.0`, `httpx==0.27.2`, `ollama==0.4.7` | Resuelve conflictos de dependencias |
| `app/main.py` | Endpoint `GET /metrics` con `prometheus_client` | Expone telemetría en formato Prometheus (Counter, Histogram, Gauge) |
| `kubernetes/local/deployment.yaml` | Eliminados Deployment `ollama` y Service `ollama-service` | Usa Ollama del host en lugar de descargarlo dentro del cluster (~1.5 GB) |
| `kubernetes/local/deployment.yaml` | `hostAliases` con IP del host | Permite que los pods resuelvan `host.docker.internal` hacia el host Ubuntu |

---

*BSG Institute · Curso: Diseño de Infraestructura Escalable para LLMs · Sesión 3*