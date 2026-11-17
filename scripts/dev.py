import argparse
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Run the isolated Alisan development shop.")
    parser.add_argument("--seed", action="store_true", help="Create or refresh demo products; development only.")
    args = parser.parse_args()
    if ROOT.name != "Alisan-shop":
        raise SystemExit("This runner is restricted to the Alisan-shop copy.")
    os.chdir(ROOT)
    if not (ROOT / ".env").is_file() or not (ROOT / "frontend/node_modules").is_dir():
        raise SystemExit("Configure .env and install frontend dependencies first; see RUN_ALISAN.md.")
    sys.path.insert(0, str(ROOT))
    from config.environment import load_local_environment
    load_local_environment()
    if os.getenv("DEBUG", "false").lower() != "true":
        raise SystemExit("The local runner requires DEBUG=true; use the production compose file for deployment.")
    for port in (3001, 8001):
        with socket.socket() as connection:
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise SystemExit(f"Port {port} is already in use. Stop the previous Alisan preview first.")
    docker = shutil.which("docker")
    if not docker:
        raise SystemExit("Docker Desktop is required for the isolated PostgreSQL and Redis services.")
    context = subprocess.run([docker, "context", "inspect", "desktop-linux"], capture_output=True).returncode
    command = [docker] + (["--context", "desktop-linux"] if context == 0 else [])
    subprocess.run(command + ["compose", "--project-name", "alisan-shop", "up", "--no-build", "--pull", "never", "--wait", "db", "redis"], check=True)
    subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)
    if args.seed:
        subprocess.run([sys.executable, "manage.py", "seed_demo_data"], check=True)
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    children = []
    try:
        children.append(subprocess.Popen([sys.executable, "manage.py", "runserver", "127.0.0.1:8001", "--noreload"]))
        children.append(subprocess.Popen([sys.executable, "-m", "celery", "-A", "config", "worker", "--pool=solo", "--concurrency=1", "-l", "warning"]))
        children.append(subprocess.Popen([sys.executable, "-m", "celery", "-A", "config", "beat", "-l", "warning", "--schedule", str(runtime / "celerybeat-schedule"), "--pidfile", str(runtime / "celerybeat.pid")]))
        environment = {**os.environ, "INTERNAL_API_URL": "http://127.0.0.1:8001/api/v1", "NEXT_PUBLIC_API_URL": "http://localhost:8001/api/v1", "NEXT_PUBLIC_SITE_URL": "http://localhost:3001", "AUTH_COOKIE_SECURE": "false"}
        children.append(subprocess.Popen(["npm", "run", "dev"], cwd=ROOT / "frontend", env=environment, start_new_session=True))
        print("\nAlisan: http://localhost:3001\nAdmin: http://localhost:8001/admin/\nPress Ctrl+C to stop the app; database volumes are kept.\n", flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(1)
        raise SystemExit("One application service stopped; inspect its log above.")
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                if child is children[-1] and len(children) == 4:
                    os.killpg(child.pid, signal.SIGTERM)
                else:
                    child.terminate()
        for child in children:
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.kill()


if __name__ == "__main__":
    main()
