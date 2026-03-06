# Despliegue de TerminalGram en Ubuntu

Este documento te guía paso a paso para desplegar TerminalGram, tu bot de Telegram de máquinas virtuales Linux aisladas.

## 1. Instalar dependencias del sistema (Docker y Docker Compose)

Abre la terminal en tu servidor Ubuntu y actualiza el sistema:
```bash
sudo apt-get update && sudo apt-get upgrade -y
```

Instala Docker Engine:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

Añade tu usuario actual al grupo de Docker para poder usarlo sin `sudo`:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

Instala Docker Compose (normalmente viene incluido en `docker-compose-plugin`, pero por si lo necesitas explícito):
```bash
sudo apt-get install docker-compose-plugin -y
```

## 2. Configurar el bot de Telegram

1. Abre Telegram y busca a **@BotFather**, o haz click en el enlace [t.me/BotFather](https://t.me/BotFather).
2. Envía el comando `/newbot`.
3. Sigue las instrucciones para darle un nombre y un username (`tu_nombre_bot`).
4. BotFather te dará un **Token HTTP API** (se ve algo como `123456789:ABCdefGHIjkl...`). Guárdalo.

## 3. Preparar el repositorio del Bot

Clona o mueve tu proyecto a una carpeta del servidor, por ejemplo `/opt/terminalgram` o dentro de tu usuario `/home/usuario/TerminalGram`:
```bash
cd /opt/terminalgram
```

Crea el archivo `.env` en la misma carpeta e introduce el Token que te dio BotFather:
```bash
nano .env
```
Dentro de `.env`, escribe:
```text
TELEGRAM_BOT_TOKEN=tu_token_aqui_pegado
```
Guarda y sal (en nano: `Ctrl+O`, `Enter`, `Ctrl+X`).

## 4. Ejecutar el despliegue automático con Docker Compose

Estando dentro de la carpeta del proyecto y con todos los archivos subidos, ejecuta el siguiente comando:
```bash
docker compose up -d --build
```

Esto hará lo siguiente:
1. Compilará la imagen de Docker base para el bot mismo.
2. Descargará y compilará la imagen base `Ubuntu` requerida para las terminales de los usuarios (solo la primera vez tardará algunos minutos).
3. Levanta el bot en segundo plano.

## 5. Mantener el bot siempre activo y consultar registros
Docker Compose mantiene el bot ejecutándose en un contenedor llamado `terminalgram_bot`. Además, configuramos `restart: always` para que si el servidor o Docker se reinician, tu bot se iniciará automáticamente.

Para consultar los logs y ver si todo va bien:
```bash
docker logs -f terminalgram_bot
```
(Usa `Ctrl+C` para salirte de la vista de logs).

¡Felicidades! Ya puedes abrir tu bot en Telegram, enviar `/start` y disfrutar de un entorno Linux aislado real.
