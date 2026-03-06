import threading
import time
import logging
from container_manager import get_container_name, client

logger = logging.getLogger(__name__)

last_activity_cache = {}
IDLE_TIMEOUT = 3600  # 1 hora

def update_activity(user_id: int):
    last_activity_cache[user_id] = time.time()

def cleanup_job():
    while True:
        try:
            now = time.time()
            to_remove = []
            for user_id, last_time in list(last_activity_cache.items()):
                if now - last_time > IDLE_TIMEOUT:
                    to_remove.append(user_id)
            
            for user_id in to_remove:
                logger.info(f"Container for user {user_id} idle for >1h. Removing.")
                try:
                    if client:
                        container = client.containers.get(get_container_name(user_id))
                        container.stop(timeout=2)
                        container.remove(force=True)
                except Exception as e:
                    pass
                
                last_activity_cache.pop(user_id, None)
                from terminal_executor import user_pwd_cache
                user_pwd_cache.pop(user_id, None)
                
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}")
            
        time.sleep(60)

def start_cleanup_worker():
    t = threading.Thread(target=cleanup_job, daemon=True)
    t.start()
    logger.info("Cleanup worker started.")
