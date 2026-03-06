import docker
from docker.types import Ulimit

CPU_LIMIT_NANO = 1000000000  # 1 core
MEM_LIMIT = "1g"
PIDS_LIMIT = 256
DISK_LIMIT = "20G"

def get_security_run_args():
    return {
        "nano_cpus": CPU_LIMIT_NANO,
        "mem_limit": MEM_LIMIT,
        "pids_limit": PIDS_LIMIT,
        "network_mode": "bridge",
        "privileged": False,
        "security_opt": ["no-new-privileges:true"],
        "cap_drop": ["ALL"],
        "cap_add": ["CHOWN", "DAC_OVERRIDE", "FOWNER", "FSETID", "KILL", "SETGID", "SETUID", "SETPCAP", "NET_BIND_SERVICE", "NET_RAW", "SYS_CHROOT", "MKNOD", "AUDIT_WRITE", "SETFCAP"],
        "ulimits": [
            Ulimit(name='nofile', soft=1024, hard=2048),
            Ulimit(name='nproc', soft=PIDS_LIMIT, hard=PIDS_LIMIT)
        ]
    }
