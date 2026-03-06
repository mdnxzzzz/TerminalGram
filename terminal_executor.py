import docker
import shlex
import logging

logger = logging.getLogger(__name__)

user_pwd_cache = {}
COMMAND_TIMEOUT = 60

def get_user_cwd(user_id: int) -> str:
    return user_pwd_cache.get(user_id, "/workspace")

def set_user_cwd(user_id: int, path: str):
    user_pwd_cache[user_id] = path

def execute_command(user_id: int, container, command: str) -> str:
    cwd = get_user_cwd(user_id)
    command = command.strip()
    
    if command.startswith("cd ") or command == "cd":
        target_dir = command[3:].strip()
        if not target_dir:
            target_dir = "/workspace"
        test_cd_cmd = f"cd {shlex.quote(target_dir)} && pwd"
        exit_code, output = container.exec_run(
            cmd=["bash", "-c", test_cd_cmd],
            workdir=cwd
        )
        if exit_code == 0:
            new_path = output.decode('utf-8').strip()
            set_user_cwd(user_id, new_path)
            return ""
        else:
            return output.decode('utf-8')

    wrapped_command = f"timeout {COMMAND_TIMEOUT} bash -c {shlex.quote(command)}"
    
    exit_code, output = container.exec_run(
        cmd=["bash", "-c", wrapped_command],
        workdir=cwd,
        demux=True
    )
    
    stdout, stderr = output
    out_str = ""
    if stdout:
        out_str += stdout.decode('utf-8', errors='replace')
    if stderr:
        out_str += stderr.decode('utf-8', errors='replace')
        
    if exit_code == 124:
        out_str += f"\n[!] Comando interrumpido por timeout ({COMMAND_TIMEOUT}s max)."
        
    return out_str or "(Comando ejecutado sin salida)"

def chunk_output(text: str, max_length: int = 4000) -> list:
    chunks = []
    while len(text) > max_length:
        split_idx = text.rfind('\n', 0, max_length)
        if split_idx == -1:
            split_idx = max_length
        chunks.append(text[:split_idx])
        text = text[split_idx:]
    if text:
        chunks.append(text)
    return chunks
