# SmartCampus - Plataforma de Gestión de Espacios Universitarios

Proyecto diseñado para el despliegue de una plataforma universitaria multicontenedor (**Frontend**, **Backend**, **PostgreSQL**) utilizando tecnologías de contenerización y orquestación como **Docker Compose** y **Kubernetes**.

---

## 1. Introducción

**SmartCampus** es una solución web moderna diseñada para automatizar y gestionar de forma centralizada la reserva de aulas y espacios universitarios. La plataforma está estructurada bajo una arquitectura desacoplada de 3 capas:
- **Frontend**: Interfaz de usuario interactiva servida mediante Nginx.
- **Backend**: API REST robusta desarrollada en Python con **FastAPI**, encargada de la lógica de negocio, validaciones de horarios y gestión de conexiones.
- **Base de Datos**: Sistema de almacenamiento relacional con **PostgreSQL 16**, que incluye scripts automatizados de inicialización y control de persistencia.

Este repositorio incluye todas las configuraciones necesarias para ejecutar la infraestructura tanto en entornos locales mediante **Docker Compose** como en clústeres de **Kubernetes**.

---

## 2. Requisitos Previos

Antes de inicializar el proyecto desde cero, asegúrate de tener instaladas las siguientes herramientas en tu sistema operativo:
1. **Git**: [Instalar Git](https://git-scm.com/)
2. **Docker Engine y Docker Compose (v2+)**: [Instalar Docker](https://docs.docker.com/get-docker/)
3. **kubectl**: [Instalar kubectl](https://kubernetes.io/docs/tasks/tools/) *(Opcional si solo usas Docker Compose)*
4. **Minikube** (o un entorno equivalente como Docker Desktop Kubernetes / Kind): [Instalar Minikube](https://minikube.sigs.k8s.io/) *(Opcional para Kubernetes)*

---

## 3. Inicialización Paso a Paso (Desde Cero)

### Paso 1: Clonar el Repositorio
Abre tu terminal, clona el repositorio en tu máquina local e ingresa al directorio del proyecto:
```bash
git clone https://github.com/tu-usuario/smartcampus.git
cd smartcampus
```

---

### Opción A: Ejecución Local con Docker Compose (Recomendado para desarrollo)

Docker Compose levantará automáticamente la base de datos, el backend y el frontend conectados mediante una red interna virtual.

1. **Construir y arrancar los contenedores en segundo plano**:
   ```bash
   docker compose up --build -d
   ```

2. **Verificar el estado de los contenedores**:
   ```bash
   docker compose ps
   ```

3. **Acceder a la aplicación**:
   * **Frontend (Interfaz Web)**: Abre tu navegador en [http://localhost:8080](http://localhost:8080)
   * **Backend (Documentación Interactiva Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   * **Base de Datos PostgreSQL**: Accesible internamente en el puerto `5432` (`campus_db`).

4. **Detener los servicios** (cuando termines):
   ```bash
   docker compose down
   ```

---

### Opción B: Despliegue en Kubernetes (Entorno de Orquestación)

Si prefieres simular un entorno de producción mediante Kubernetes:

1. **Iniciar el clúster local (ej. Minikube)**:
   ```bash
   minikube start
   ```

2. **Crear el Namespace dedicado**:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

3. **Aplicar Secretos, ConfigMaps y Volúmenes**:
   ```bash
   kubectl apply -f k8s/secret.yaml
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/database-init-configmap.yaml
   kubectl apply -f k8s/database-pvc.yaml
   ```

4. **Desplegar la Base de Datos, el Backend y el Frontend**:
   ```bash
   kubectl apply -f k8s/database-deployment.yaml
   kubectl apply -f k8s/database-service.yaml
   kubectl apply -f k8s/backend-deployment.yaml
   kubectl apply -f k8s/backend-service.yaml
   kubectl apply -f k8s/frontend-deployment.yaml
   kubectl apply -f k8s/frontend-service.yaml
   ```

5. **Acceder a los servicios**:
   * Para exponer el frontend en Minikube:
     ```bash
     minikube service frontend-service -n smartcampus
     ```

---

## 4. Conclusión

El proyecto **SmartCampus** demuestra la aplicación práctica de arquitecturas desacopladas modernas basadas en microservicios y contenedores. Gracias al uso dual de **Docker Compose** para la fase de desarrollo local y de **Kubernetes** para la orquestación escalable, la plataforma garantiza portabilidad, tolerancia a fallos y un despliegue ágil. Esta estructura sienta una base sólida para futuras expansiones, integración continua (CI/CD) y gestión eficiente de recursos en entornos académicos reales.