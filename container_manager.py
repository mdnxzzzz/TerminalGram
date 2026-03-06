import docker
import os
import logging
from security import get_security_run_args

logger = logging.getLogger(__name__)

try:
    client = docker.from_env()
except Exception as e:
    logger.error(f"Error connecting to Docker: {e}")
    client = None

IMAGE_NAME = "terminalgram_user_env"

def build_image_if_not_exists():
    if not client: return
    try:
        client.images.get(IMAGE_NAME)
        logger.info(f"Image {IMAGE_NAME} already exists.")
    except docker.errors.ImageNotFound:
        logger.info(f"Building image {IMAGE_NAME}... This might take a few minutes.")
        client.images.build(path=".", tag=IMAGE_NAME, rm=True, dockerfile="Dockerfile")
        logger.info("Image built successfully.")

def get_container_name(user_id: int) -> str:
    return f"tg_user_{user_id}"

def get_or_create_container(user_id: int):
    if not client:
        raise Exception("Docker daemon connection failed")
        
    container_name = get_container_name(user_id)
    try:
        container = client.containers.get(container_name)
        if container.status != "running":
            container.start()
        return container
    except docker.errors.NotFound:
        # Check if the base image exists first
        try:
            client.images.get(IMAGE_NAME)
        except docker.errors.ImageNotFound:
            raise Exception("La infraestructura se está preparando. Por favor espera e intenta /start de nuevo.")

        logger.info(f"Creating new container for user {user_id}")
        run_args = get_security_run_args()
        
        container = client.containers.run(
            IMAGE_NAME,
            name=container_name,
            detach=True,
            tty=True,
            stdin_open=True,
            command=["tail", "-f", "/dev/null"],
            **run_args
        )
        return container

def stop_and_remove_container(user_id: int) -> bool:
    if not client: return False
    try:
        container = client.containers.get(get_container_name(user_id))
        container.stop(timeout=2)
        container.remove(force=True)
        return True
    except docker.errors.NotFound:
        return False
        
def get_container_stats(user_id: int) -> dict:
    if not client: return None
    try:
        container = client.containers.get(get_container_name(user_id))
        stats = container.stats(stream=False)
        return stats
    except docker.errors.NotFound:
        return None
