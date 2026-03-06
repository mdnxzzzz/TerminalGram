import os
import html
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from container_manager import build_image_if_not_exists, get_or_create_container, stop_and_remove_container, get_container_stats
from terminal_executor import execute_command, chunk_output, get_user_cwd
from cleanup_worker import start_cleanup_worker, update_activity

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_activity(user_id)
    await update.message.reply_text("⏳ Inicializando tu terminal Linux... 🐧\nEsto puede tardar unos segundos si es la primera vez.")
    
    try:
        container = await asyncio.to_thread(get_or_create_container, user_id)
        cwd = get_user_cwd(user_id)
        
        reply = (
            f"✅ **Terminal lista y aislada**\n\n"
            f"📂 Directorio: `{cwd}`\n"
            f"💡 *Escribe comandos directamente en el chat.*\n"
            f"Usa /help para ver las funciones extras."
        )
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error starting container: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error al iniciar el contenedor: {e}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("⏳ Destruyendo tu contenedor...")
    stopped = await asyncio.to_thread(stop_and_remove_container, user_id)
    
    from terminal_executor import user_pwd_cache
    user_pwd_cache.pop(user_id, None)
    
    if stopped:
        await update.message.reply_text("✅ Contenedor destruido y recursos liberados.")
    else:
        await update.message.reply_text("No tenías ningún contenedor activo.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("⏳ Reiniciando tu contenedor totalmente de cero...")
    
    await asyncio.to_thread(stop_and_remove_container, user_id)
    
    from terminal_executor import user_pwd_cache
    user_pwd_cache.pop(user_id, None)
    
    try:
        await asyncio.to_thread(get_or_create_container, user_id)
        await update.message.reply_text("✅ Contenedor reiniciado limpiamente. Todo el progreso anterior se ha borrado.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error al reiniciar: {e}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = await asyncio.to_thread(get_container_stats, user_id)
    if not stats:
        await update.message.reply_text("⚠️ No tienes un contenedor activo. Usa /start para crear uno.")
        return
        
    try:
        mem_u = stats.get('memory_stats', {}).get('usage', 0)
        mem_l = stats.get('memory_stats', {}).get('limit', 0)
        
        # Calculate CPU safely
        cpu_percent = 0.0
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            sys_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats'].get('system_cpu_usage', 0)
            if sys_delta > 0 and cpu_delta > 0:
                percpu = len(stats.get('cpu_stats', {}).get('cpu_usage', {}).get('percpu_usage', [1]))
                cpu_percent = (cpu_delta / sys_delta) * percpu * 100.0
        except KeyError:
            pass

        reply = (
            f"📊 *Estado de tu Contenedor*\n"
            f"💻 CPU Uso: `{cpu_percent:.2f}%`\n"
            f"🧠 RAM Uso: `{mem_u / (1024*1024):.2f} MB` / `{mem_l / (1024*1024):.0f} MB`\n"
            f"💾 Disco Límite: `20 GB` (cuotas del docker daemon)\n"
            f"⏳ Auto-destrucción por inactividad: `1 hora`"
        )
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Status error: {e}")
        await update.message.reply_text("Aviso: No se pudieron parsear las métricas de Docker.")

async def files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.text = "ls -la"
    await handle_message(update, context)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *TerminalGram Bot Ayuda*\n\n"
        "Comandos Básicos:\n"
        "/start - Inicia tu máquina Linux\n"
        "/stop - Destruye la máquina y libera recursos\n"
        "/reset - Reinicia todo de fábrica\n"
        "/status - Muestra consumo de RAM/CPU\n"
        "/files - Lista archivos en el directorio actual (`ls -la`)\n"
        "/help - Muestra este menú\n\n"
        "Comandos Extras:\n"
        "/neofetch - Muestra la info del sistema\n"
        "/cpu - Ver top processes (`top -b -n 1 | head -n 15`)\n"
        "/ram - Ver estado de memoria (`free -h`)\n"
        "/disk - Ver particiones y uso (`df -h`)\n\n"
        "Simplemente escribe cualquier comando (ej. `npm init`, `git clone`, `python script.py`) en el chat para ejecutarlo en tu terminal."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def extra_neofetch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.text = "neofetch"
    await handle_message(update, context)

async def extra_cpu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.text = "top -b -n 1 | head -n 15"
    await handle_message(update, context)

async def extra_ram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.text = "free -h"
    await handle_message(update, context)

async def extra_disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update.message.text = "df -h"
    await handle_message(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    command = update.message.text
    update_activity(user_id)
    
    try:
        container = await asyncio.to_thread(get_or_create_container, user_id)
    except Exception as e:
        await update.message.reply_text(f"❌ Error al conectar con tu contenedor: {e}")
        return

    m = None
    if any(command.strip().startswith(x) for x in ["git clone", "npm i", "npm install", "pip install", "apt", "python", "node", "gcc"]):
        m = await update.message.reply_text("⏳ Ejecutando comando... (esto podría tomar unos momentos)")

    try:
        output = await asyncio.to_thread(execute_command, user_id, container, command)
        
        chunks = chunk_output(output)
        
        for i, chunk in enumerate(chunks):
            formatted_chunk = f"<pre><code>{html.escape(chunk)}</code></pre>"
            if len(chunks) > 1:
                formatted_chunk = f"<b>Parte {i+1}/{len(chunks)}</b>\n" + formatted_chunk
                
            if i == 0 and m:
                await m.edit_text(formatted_chunk, parse_mode="HTML")
            else:
                await update.message.reply_text(formatted_chunk, parse_mode="HTML")
                
    except Exception as e:
        await update.message.reply_text(f"❌ Error ejecutando comando: {e}")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No TELEGRAM_BOT_TOKEN provided in .env")
        return
        
    start_cleanup_worker()
    
    import threading
    threading.Thread(target=build_image_if_not_exists, daemon=True).start()
    
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("files", files))
    application.add_handler(CommandHandler("help", help_cmd))
    
    application.add_handler(CommandHandler("neofetch", extra_neofetch))
    application.add_handler(CommandHandler("cpu", extra_cpu))
    application.add_handler(CommandHandler("ram", extra_ram))
    application.add_handler(CommandHandler("disk", extra_disk))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("TerminalGram Bot running...")
    application.run_polling()

if __name__ == "__main__":
    main()
