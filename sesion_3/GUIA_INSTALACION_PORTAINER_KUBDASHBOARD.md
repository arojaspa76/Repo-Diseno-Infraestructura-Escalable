# Guía de Instalación desde Cero
## Docker · Minikube · kubectl · Ollama · Portainer · Kubernetes Dashboard
**BSG Institute — Diseño de Infraestructura Escalable para LLMs · Sesión 3**

> **Sistema operativo:** Ubuntu 24.04 LTS (también funciona en WSL2 con Ubuntu 24.04)  
> **Última actualización:** 2026-10-28  
> **Tiempo estimado:** 30–45 minutos (depende de la velocidad de internet)

---

## Antes de empezar — verificar requisitos mínimos

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| RAM | 8 GB | 16 GB |
| Disco libre | 20 GB | 40 GB |
| CPU | 2 núcleos | 4 núcleos |
| Internet | Requerido para descargas | — |

```bash
# Ver cuánta RAM tiene el equipo
free -h

# Ver espacio en disco
df -h /

# Ver cuántos núcleos CPU hay
nproc
```

---

## INSTALACIÓN 1 — Docker Engine

Docker es el motor de contenedores que necesitan tanto Minikube como Portainer.

> **¿Qué es Docker?**  
> Un motor que permite empaquetar aplicaciones con todo lo que necesitan (código, dependencias, configuración) en "contenedores" — unidades aisladas que corren de forma idéntica en cualquier equipo.

### 1.1 Desinstalar versiones antiguas (si existen)

```bash
# Elimina paquetes viejos que puedan generar conflictos
# Si no están instalados, el comando simplemente no hace nada
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null
```

### 1.2 Instalar dependencias previas

```bash
# Actualizar la lista de paquetes disponibles
sudo apt-get update

# Instalar herramientas necesarias para agregar repositorios externos
sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release
```

> **¿Qué son estas herramientas?**
> - `ca-certificates` — certificados para conexiones seguras HTTPS
> - `curl` — herramienta para descargar archivos desde internet
> - `gnupg` — para verificar la firma digital de los paquetes de Docker
> - `lsb-release` — para detectar la versión de Ubuntu automáticamente

### 1.3 Agregar el repositorio oficial de Docker

```bash
# Crear directorio para guardar la llave GPG de Docker
sudo install -m 0755 -d /etc/apt/keyrings

# Descargar la llave GPG oficial de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Dar permisos de lectura a la llave
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Agregar el repositorio de Docker a la lista de fuentes de apt
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

> **¿Por qué este paso?**  
> Ubuntu tiene su propio paquete `docker.io` en sus repositorios pero suele ser una versión antigua. Al agregar el repositorio oficial de Docker, `apt` descargará siempre la versión más reciente y estable directamente de Docker Inc.

### 1.4 Instalar Docker Engine

```bash
# Actualizar la lista de paquetes (ahora incluye el repositorio de Docker)
sudo apt-get update

# Instalar Docker Engine y sus componentes
sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

### 1.5 Verificar que Docker instaló correctamente

```bash
# Ver la versión instalada
docker --version
# Esperado: Docker version 26.x.x o superior

# Ejecutar el contenedor de prueba oficial de Docker
sudo docker run hello-world
```

Si aparece el mensaje `Hello from Docker!`, la instalación fue exitosa.

### 1.6 Configurar Docker para usarlo sin `sudo`

Por defecto, Docker requiere `sudo` en cada comando. Para usarlo como usuario normal:

```bash
# Agregar tu usuario al grupo docker
sudo usermod -aG docker $USER

# Aplicar el cambio de grupo SIN cerrar sesión
newgrp docker

# Verificar que funciona sin sudo
docker run hello-world
```

> **¿Por qué `newgrp docker`?**  
> Los cambios de grupo de Linux normalmente requieren cerrar sesión y volver a entrar para que tomen efecto. `newgrp docker` aplica el cambio en la sesión actual sin necesidad de salir.

### 1.7 Configurar Docker para que inicie automáticamente

```bash
# Habilitar Docker para que arranque cuando Ubuntu inicia
sudo systemctl enable docker
sudo systemctl enable containerd

# Verificar que está corriendo
sudo systemctl status docker
```

Debe mostrar `Active: active (running)`.

---

## INSTALACIÓN 2 — kubectl

`kubectl` es la herramienta de línea de comandos para gestionar clusters de Kubernetes. Es el equivalente a tener el control remoto del cluster.

> **¿Qué es kubectl?**  
> Un cliente que se comunica con la API de Kubernetes. Con él se pueden crear pods, ver logs, escalar deployments, aplicar manifiestos YAML, etc.

### 2.1 Descargar e instalar kubectl

```bash
# Descargar la última versión estable de kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Instalar el binario en /usr/local/bin (disponible para todos los usuarios)
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Eliminar el archivo descargado (ya no se necesita)
rm kubectl
```

### 2.2 Verificar la instalación

```bash
kubectl version --client
```

Salida esperada:
```
Client Version: v1.31.x
Kustomize Version: v5.x.x
```

---

## INSTALACIÓN 3 — Minikube

Minikube crea un cluster de Kubernetes completo dentro de tu equipo, usando Docker como base. Es ideal para desarrollo y aprendizaje.

> **¿Qué es Minikube?**  
> Una versión de Kubernetes que corre localmente. Crea un nodo (servidor) de Kubernetes dentro de un contenedor Docker. Incluye todo lo necesario: API server, scheduler, etcd, kubelet, etc.

### 3.1 Descargar e instalar Minikube

```bash
# Descargar el binario de Minikube para Linux x86_64
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Instalar en /usr/local/bin
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Eliminar el archivo descargado
rm minikube-linux-amd64
```

### 3.2 Verificar la instalación

```bash
minikube version
```

Salida esperada:
```
minikube version: v1.34.x
```

### 3.3 Iniciar el cluster de Minikube

```bash
# Iniciar con el driver Docker, 2 CPUs y 4 GB de RAM
minikube start --driver=docker --cpus=2 --memory=4096
```

> **¿Qué significa cada parámetro?**
> - `--driver=docker` — usa Docker para crear el nodo (en lugar de una VM)
> - `--cpus=2` — asigna 2 núcleos al cluster
> - `--memory=4096` — asigna 4 GB de RAM al cluster

Este proceso tarda 2–5 minutos la primera vez porque descarga la imagen base de Kubernetes.

Salida esperada al finalizar:
```
✅  minikube v1.34.x on Ubuntu 24.04
✅  Using the docker driver based on user configuration
✅  Started controls plane node minikube in cluster minikube
✅  Done! kubectl is now configured to use "minikube" cluster
```

### 3.4 Verificar que el cluster funciona

```bash
# Ver el estado del cluster
minikube status

# Ver el nodo del cluster
kubectl get nodes
```

Salida esperada de `kubectl get nodes`:
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   1m    v1.31.x
```

`Ready` significa que el cluster está operativo.

---

## INSTALACIÓN 4 — Ollama

Ollama permite descargar y correr modelos de lenguaje (LLMs) localmente, sin necesidad de internet ni APIs de pago.

> **¿Qué es Ollama?**  
> Un servidor local que descarga modelos LLM open-weight (como Llama 3.2) y los expone a través de una API HTTP. El gateway de esta sesión se conecta a Ollama en lugar de a servicios cloud.

### 4.1 Instalar Ollama

```bash
# El instalador oficial descarga e instala Ollama automáticamente
curl -fsSL https://ollama.com/install.sh | sh
```

Este comando:
1. Detecta la arquitectura del sistema (x86_64 o ARM)
2. Descarga el binario de Ollama
3. Instala y configura el servicio systemd
4. Inicia el servicio automáticamente

### 4.2 Verificar que Ollama está corriendo

```bash
ollama --version

# Verificar que el servicio está activo
sudo systemctl status ollama
```

Debe mostrar `Active: active (running)`.

### 4.3 Configurar Ollama para escuchar en todas las interfaces

> **Este paso es obligatorio para que Kubernetes pueda conectarse a Ollama.**  
> Por defecto Ollama solo escucha en `127.0.0.1` (solo el equipo local).  
> Los pods de Kubernetes necesitan conectarse desde una red interna diferente.

```bash
# Crear el directorio de configuración del servicio
sudo mkdir -p /etc/systemd/system/ollama.service.d

# Crear el archivo que le indica a Ollama en qué IP escuchar
sudo tee /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF

# Recargar la configuración del sistema
sudo systemctl daemon-reload

# Reiniciar Ollama con la nueva configuración
sudo systemctl restart ollama

# Verificar que ahora escucha en todas las interfaces
sleep 3 && ss -tlnp | grep 11434
```

Salida esperada:
```
LISTEN  0  4096  0.0.0.0:11434  ...
```

`0.0.0.0` confirma que ahora escucha en todas las interfaces.

### 4.4 Descargar los modelos necesarios para la sesión

```bash
# Modelo pequeño y rápido — ideal para demos (~1.3 GB)
ollama pull llama3.2:1b

# Modelo de mayor calidad — opcional (~2.0 GB)
ollama pull llama3.2:3b
```

> La descarga puede tardar varios minutos dependiendo de la velocidad de internet.  
> El progreso se muestra en la terminal.

### 4.5 Verificar que los modelos están disponibles

```bash
# Listar modelos descargados
ollama list
```

Salida esperada:
```
NAME            ID              SIZE    MODIFIED
llama3.2:1b     baf6a787fdff    1.3 GB  X minutes ago
llama3.2:3b     a80c4f17acd5    2.0 GB  X minutes ago
```

### 4.6 Hacer una prueba rápida

```bash
# Probar que Ollama responde a la API
curl http://localhost:11434/api/tags | python3 -m json.tool

# Probar una inferencia directa (puede tardar unos segundos la primera vez)
ollama run llama3.2:1b "¿Qué es Kubernetes en una oración?"
```

Para salir del chat interactivo de Ollama: escribir `/bye` y presionar Enter.

---

## INSTALACIÓN 5 — Portainer CE

Portainer es la interfaz web para gestionar los contenedores Docker del host.

> **¿Qué es Portainer?**  
> Una aplicación web que se conecta al motor Docker de tu equipo y permite gestionar contenedores, imágenes, volúmenes y redes desde el navegador — sin tener que recordar comandos Docker.

### 5.1 Crear el volumen de datos

```bash
# Un volumen Docker es un espacio de almacenamiento persistente
# Portainer guarda aquí su base de datos y configuración
docker volume create portainer_data
```

### 5.2 Instalar Portainer

```bash
docker run -d \
  --name portainer \
  --restart=always \
  -p 9443:9443 \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest
```

> **¿Qué hace cada línea?**
> - `--name portainer` — nombre del contenedor (para referenciarlo fácilmente)
> - `--restart=always` — si Docker se reinicia, Portainer vuelve a levantar solo
> - `-p 9443:9443` — expone la interfaz web en el puerto 9443 del host
> - `-p 8000:8000` — puerto para agentes remotos de Portainer
> - `-v /var/run/docker.sock` — socket de Docker: así Portainer puede ver y controlar los demás contenedores
> - `-v portainer_data:/data` — monta el volumen para que los datos persistan
> - `portainer/portainer-ce:latest` — imagen oficial de Portainer Community Edition

### 5.3 Verificar que está corriendo

```bash
docker ps | grep portainer
```

Debe mostrar el contenedor con STATUS `Up`.

### 5.4 Abrir Portainer en el navegador

```
https://localhost:9443
```

**El navegador mostrará un aviso de seguridad** — esto es normal. Portainer usa un certificado autofirmado (self-signed) porque no tiene un dominio real con certificado oficial.

Cómo aceptarlo:
- **Chrome:** clic en `Avanzado` → `Acceder a localhost (sitio no seguro)`
- **Firefox:** clic en `Avanzado...` → `Aceptar el riesgo y continuar`
- **Edge:** clic en `Más información` → `Ir a localhost (no seguro)`

### 5.5 Crear el usuario administrador (primera vez)

En la pantalla inicial de Portainer:

1. Ingresar un nombre de usuario: `admin`
2. Ingresar una contraseña de mínimo 12 caracteres
3. Confirmar la contraseña
4. Clic en **"Create user"**

> ⚠️ Si la página muestra "Your Portainer instance timed out", significa que tardó más de 5 minutos sin configurar. Ejecutar `docker restart portainer` y volver a abrir `https://localhost:9443`.

### 5.6 Configurar el entorno local

Después de crear el usuario, Portainer pregunta qué entorno gestionar:

1. Clic en **"Get Started"**
2. Portainer detecta automáticamente el Docker local y lo agrega como entorno **"local"**
3. Clic en **"local"** para entrar al panel de gestión

---

## INSTALACIÓN 6 — Kubernetes Dashboard

El dashboard oficial de Kubernetes viene incluido en Minikube como un addon. No requiere instalación separada — solo habilitarlo y configurarlo.

> **¿Qué es el Kubernetes Dashboard?**  
> La interfaz web oficial de Kubernetes. Permite ver el estado de todos los recursos del cluster (pods, deployments, services, logs, métricas) sin usar comandos.

### 6.1 Habilitar los addons necesarios

```bash
# Habilitar el dashboard web
minikube addons enable dashboard

# Habilitar el servidor de métricas (necesario para ver CPU/RAM en el dashboard)
minikube addons enable metrics-server
```

Verificar que los pods del dashboard están corriendo:

```bash
kubectl get pods -n kubernetes-dashboard
```

Esperar hasta que todos muestren `Running`:
```
NAME                                         READY   STATUS    RESTARTS
dashboard-metrics-scraper-xxxxxxxxx-xxxxx    1/1     Running   0
kubernetes-dashboard-xxxxxxxxx-xxxxx         1/1     Running   0
```

### 6.2 Configurar acceso sin token — SOLO DEMO LOCAL

> 🔴 **Advertencia importante**
>
> Los siguientes pasos eliminan la autenticación del dashboard y dan permisos de administrador total.  
> **Solo válido para desarrollo local y demostraciones académicas.**  
> **Nunca aplicar en entornos de QA, staging o producción.**  
> En entornos reales se usa autenticación con tokens de corta duración y RBAC con mínimo privilegio.

#### Paso A: Habilitar el botón "Skip" en la pantalla de login

```bash
kubectl patch deployment kubernetes-dashboard \
  -n kubernetes-dashboard \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--enable-skip-login"}]'
```

> **¿Qué hace este comando?**  
> Modifica la configuración del deployment del dashboard para agregar el argumento `--enable-skip-login` al proceso. Esto habilita el botón "Skip" en la pantalla de login, permitiendo entrar sin ingresar un token.

#### Paso B: Dar permisos para ver todos los namespaces

Sin este paso, el dashboard con "Skip" solo puede ver el namespace `default` y no mostrará los pods de `llm-session3`.

```bash
kubectl create clusterrolebinding kubernetes-dashboard-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=kubernetes-dashboard:kubernetes-dashboard
```

> **¿Qué hace este comando?**  
> Crea un "ClusterRoleBinding" — un vínculo entre:
> - La cuenta de servicio `kubernetes-dashboard` (la identidad que usa el dashboard cuando navegas con "Skip")
> - El rol `cluster-admin` (permiso de lectura y escritura en TODOS los recursos del cluster)
>
> Sin este paso, el dashboard solo tiene permisos mínimos sobre `default`.

#### Paso C: Reiniciar el dashboard para aplicar los cambios

```bash
kubectl rollout restart deployment/kubernetes-dashboard -n kubernetes-dashboard

# Esperar que el pod nuevo esté listo
kubectl get pods -n kubernetes-dashboard -w
# Ctrl+C cuando aparezca Running
```

### 6.3 Abrir el dashboard

```bash
minikube dashboard
```

Este comando:
1. Crea un túnel seguro entre tu navegador y el cluster
2. Abre el navegador automáticamente

> **La terminal queda bloqueada** mientras el dashboard está abierto.  
> Abrir una nueva terminal para seguir trabajando.  
> Si el navegador no abre solo, copiar la URL que imprime el comando.

### 6.4 Navegar el dashboard

En la pantalla de login, clic en **"Skip"** (esquina inferior izquierda).

**Selector de namespace** (arriba a la izquierda):
- Seleccionar `All namespaces` para ver todo
- Seleccionar `llm-session3` para ver solo los recursos del laboratorio

**Secciones útiles:**

| Sección del menú | Para qué sirve |
|-----------------|----------------|
| Workloads → Pods | Ver estado de cada pod, entrar a sus logs |
| Workloads → Deployments | Ver réplicas, escalar manualmente |
| Workloads → HPA | Ver el autoscaler en acción |
| Services | Ver los puertos expuestos |
| Config Maps | Ver las variables de configuración |

---

## Verificación final — todo instalado y funcionando

Ejecutar este bloque completo para confirmar que todo está en orden:

```bash
echo "=== Docker ==="
docker --version
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== kubectl ==="
kubectl version --client --short 2>/dev/null || kubectl version --client

echo ""
echo "=== Minikube ==="
minikube status

echo ""
echo "=== Ollama ==="
ollama --version
ss -tlnp | grep 11434
curl -s http://localhost:11434/api/tags | python3 -m json.tool

echo ""
echo "=== Nodos del cluster ==="
kubectl get nodes

echo ""
echo "=== Pods del dashboard ==="
kubectl get pods -n kubernetes-dashboard
```

Salida esperada (todo en verde):

```
=== Docker ===
Docker version 26.x.x, build xxxxxxx
NAMES       STATUS          PORTS
portainer   Up X minutes    0.0.0.0:9443->9443/tcp

=== kubectl ===
Client Version: v1.31.x

=== Minikube ===
minikube: Running
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured

=== Ollama ===
ollama version is 0.x.x
LISTEN  0  4096  0.0.0.0:11434  ...
{"models":[{"name":"llama3.2:1b",...}]}

=== Nodos del cluster ===
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   Xm    v1.31.x

=== Pods del dashboard ===
NAME                                      READY   STATUS    RESTARTS
dashboard-metrics-scraper-xxx             1/1     Running   0
kubernetes-dashboard-xxx                  1/1     Running   0
```

---

## Resumen de lo instalado

| Herramienta | Versión mínima | Para qué se usa |
|-------------|---------------|-----------------|
| Docker Engine | 24+ | Motor de contenedores |
| kubectl | 1.28+ | CLI para gestionar Kubernetes |
| Minikube | 1.32+ | Cluster Kubernetes local |
| Ollama | 0.4+ | Servidor local de LLMs |
| Portainer CE | latest | UI web para Docker |
| Kubernetes Dashboard | (addon Minikube) | UI web para Kubernetes |

---

## Limpieza completa (opcional)

Si necesitas desinstalar todo y empezar desde cero:

```bash
# 1. Eliminar el cluster de Minikube
minikube delete

# 2. Detener y eliminar Portainer
docker stop portainer
docker rm portainer
docker volume rm portainer_data

# 3. Eliminar todas las imágenes Docker descargadas
docker system prune -a --volumes

# 4. Desinstalar Minikube
sudo rm /usr/local/bin/minikube

# 5. Desinstalar kubectl
sudo rm /usr/local/bin/kubectl

# 6. Desinstalar Docker
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
sudo rm /etc/apt/sources.list.d/docker.list
sudo rm /etc/apt/keyrings/docker.gpg

# 7. Desinstalar Ollama
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo rm /etc/systemd/system/ollama.service
sudo rm -rf /etc/systemd/system/ollama.service.d
sudo rm $(which ollama)
sudo rm -rf /usr/share/ollama
sudo systemctl daemon-reload
```

---

*BSG Institute · Curso: Diseño de Infraestructura Escalable para LLMs · Sesión 3*