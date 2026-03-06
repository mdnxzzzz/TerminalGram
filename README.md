# TerminalGram 🐧

TerminalGram es un bot de Telegram que proporciona entornos de terminal Linux reales y aislados para cada usuario utilizando contenedores Docker. Es ideal para ejecutar entornos de prueba, clonar repositorios o practicar comandos desde Telegram.

## Características

- 🏗️ **Contenedores Aislados**: Cada usuario recibe su propia máquina Linux independiente.
- 🛠️ **Herramientas Preinstaladas**: Ubuntu con Python3, Node.js, Git, GCC, Nano, VIM y más.
- 🧹 **Auto-Limpieza**: Los contenedores inactivos se destruyen automáticamente después de 1 hora.
- 🛡️ **Seguridad Estricta**: Límites de CPU (1 core), RAM (1GB), disco y procesos para evitar abusos.

## Requisitos

- Docker y Docker Compose (V2 recomendado).
- Un Token de Bot de Telegram ([BotFather](https://t.me/BotFather)).
- Python 3.10+ (si se corre fuera de Docker Compose).

## Instalación y Despliegue

### 1. Clonar el repositorio
```bash
git clone https://github.com/mdnxzzzz/TerminalGram
cd TerminalGram
```

### 2. Configurar variables de entorno
Copia el archivo de ejemplo y edítalo con tu token:
```bash
cp .env.example .env
nano .env
```
Añade tu token en la línea:
`TELEGRAM_BOT_TOKEN=tu_token_aqui`

### 3. Iniciar con Docker Compose
```bash
docker compose up -d --build
```
Esto levantará el bot y preparará la imagen base de Ubuntu para los usuarios.

## Comandos del Bot

- `/start`: Inicia o conecta con tu terminal activa.
- `/status`: Muestra uso de CPU, RAM y límites.
- `/files`: Lista archivos del directorio actual (`ls -la`).
- `/reset`: Reinicia el contenedor de fábrica.
- `/stop`: Destruye el contenedor actual de forma manual.
- `/help`: Muestra la guía de uso.

## Seguridad

Los contenedores se ejecutan con:
- Capadd/Capdrop para minimizar privilegios.
- Ulimits para prevenir fork-bombs.
- Aislamiento de red mediante bridge.
- Sin acceso al sistema de archivos del host.
