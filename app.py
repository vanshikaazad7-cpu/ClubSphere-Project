import argparse
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

# Enable ANSI colors on Windows console if available
if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# Terminal Color Styling
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_CYAN = "\033[96m"
CLR_MAGENTA = "\033[95m"
CLR_GREEN = "\033[92m"
CLR_YELLOW = "\033[93m"
CLR_RED = "\033[91m"
CLR_BLUE = "\033[94m"

TAG_BACKEND = f"{CLR_MAGENTA}{CLR_BOLD}[BACKEND]{CLR_RESET} "
TAG_FRONTEND = f"{CLR_CYAN}{CLR_BOLD}[FRONTEND]{CLR_RESET} "
TAG_SYSTEM = f"{CLR_GREEN}{CLR_BOLD}[SYSTEM]{CLR_RESET} "
TAG_WARN = f"{CLR_YELLOW}{CLR_BOLD}[WARN]{CLR_RESET} "
TAG_ERROR = f"{CLR_RED}{CLR_BOLD}[ERROR]{CLR_RESET} "

# Directory constants
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

running_processes = []
shutdown_event = threading.Event()


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a specific network port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def kill_process_tree(proc: subprocess.Popen):
    """Terminates a process and all of its child processes cleanly."""
    if proc.poll() is not None:
        return

    pid = proc.pid
    if os.name == "nt":
        # Windows taskkill forcefully terminates child processes (e.g. node, uvicorn workers)
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass
    else:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def stream_output(pipe, prefix: str):
    """Reads lines from process pipe and prints them with a stylized prefix."""
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            cleaned = line.rstrip()
            if cleaned:
                print(f"{prefix}{cleaned}")
    except (ValueError, OSError):
        pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def check_prerequisites():
    """Verify backend and frontend dependencies are ready before starting."""
    print(f"{TAG_SYSTEM}Checking development prerequisites...")

    # 1. Verify backend structure
    if not BACKEND_DIR.exists():
        print(f"{TAG_ERROR}Backend directory not found at: {BACKEND_DIR}")
        sys.exit(1)

    # 2. Verify frontend structure
    if not FRONTEND_DIR.exists():
        print(f"{TAG_ERROR}Frontend directory not found at: {FRONTEND_DIR}")
        sys.exit(1)

    # 3. Ensure backend .env exists
    env_file = BACKEND_DIR / ".env"
    env_example = BACKEND_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        print(f"{TAG_SYSTEM}Initializing backend/.env from .env.example...")
        shutil.copyfile(env_example, env_file)

    # 4. Ensure backend uploads directory exists
    (BACKEND_DIR / "uploads").mkdir(exist_ok=True)


    # 5. Check frontend node_modules
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print(f"{TAG_WARN}Frontend node_modules not found. Running 'npm install'...")
        npm_cmd = find_npm()
        install_res = subprocess.run([npm_cmd, "install"], cwd=str(FRONTEND_DIR), check=False)
        if install_res.returncode != 0:
            print(f"{TAG_ERROR}Failed to run 'npm install'. Please run manually in frontend/.")
            sys.exit(1)
        print(f"{TAG_SYSTEM}Frontend dependencies installed successfully.")

    print(f"{TAG_SYSTEM}Prerequisites verified successfully.")


def find_npm() -> str:
    """Find the appropriate npm executable on the system."""
    if os.name == "nt":
        found = shutil.which("npm.cmd") or shutil.which("npm")
        if found:
            return found
        # Fallback to standard installation paths
        common_path = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs" / "npm.cmd"
        if common_path.exists():
            return str(common_path)
    return shutil.which("npm") or "npm"


def wait_for_backend_health(port: int, timeout_secs: int = 20) -> bool:
    """Poll backend health check until it responds 200 OK or times out."""
    url = f"http://127.0.0.1:{port}/health"
    start_time = time.time()
    while time.time() - start_time < timeout_secs:
        if shutdown_event.is_set():
            return False
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ClubSphere-Launcher"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def print_banner(backend_port: int, frontend_port: int):
    """Display the formatted ClubSphere service launch banner."""
    backend_url = f"http://127.0.0.1:{backend_port}"
    frontend_url = f"http://localhost:{frontend_port}"

    print("\n" + f"{CLR_BOLD}{CLR_MAGENTA}" + "=" * 70 + f"{CLR_RESET}")
    print(f" {CLR_BOLD}{CLR_GREEN}🌟 CLUBSPHERE UNIFIED PLATFORM IS LIVE & READY 🌟{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_MAGENTA}" + "=" * 70 + f"{CLR_RESET}")
    print(f"  {CLR_BOLD}🌐 Frontend Web App:{CLR_RESET}      {CLR_CYAN}{frontend_url}{CLR_RESET}")
    print(f"  {CLR_BOLD}⚙️  Backend REST API:{CLR_RESET}      {CLR_CYAN}{backend_url}{CLR_RESET}")
    print(f"  {CLR_BOLD}📖 Interactive Docs:{CLR_RESET}      {CLR_CYAN}{backend_url}/docs{CLR_RESET}")
    print(f"  {CLR_BOLD}📑 Alternative Docs:{CLR_RESET}      {CLR_CYAN}{backend_url}/redoc{CLR_RESET}")
    print(f"  {CLR_BOLD}🩺 System Health Check:{CLR_RESET}   {CLR_CYAN}{backend_url}/health{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_MAGENTA}" + "-" * 70 + f"{CLR_RESET}")
    print(f"  {CLR_YELLOW}⚡ Hot-reloading active on both servers.{CLR_RESET}")
    print(f"  {CLR_YELLOW}🛑 Press Ctrl + C to gracefully stop all services.{CLR_RESET}")
    print(f"{CLR_BOLD}{CLR_MAGENTA}" + "=" * 70 + f"{CLR_RESET}\n")


def cleanup_all():
    """Terminate all running sub-processes."""
    shutdown_event.set()
    print(f"\n{TAG_SYSTEM}Initiating graceful shutdown of ClubSphere services...")
    for proc, name in running_processes:
        if proc.poll() is None:
            print(f"{TAG_SYSTEM}Stopping {name} (PID: {proc.pid})...")
            kill_process_tree(proc)
    print(f"{TAG_SYSTEM}All ClubSphere services stopped cleanly. Goodbye!")


def main():
    parser = argparse.ArgumentParser(
        description="ClubSphere Full-Stack Unified Development Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--backend-port", type=int, default=8000, help="Backend API port")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Frontend dev server port")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address to bind")
    parser.add_argument("--no-reload", action="store_true", help="Disable backend code hot-reloading")
    parser.add_argument("--no-browser", action="store_true", help="Do not open web browser automatically")

    args = parser.parse_args()

    # Pre-flight check
    check_prerequisites()

    # Port validation
    #
    # A busy port is fatal: uvicorn exits with code 3 (ERROR 10048) when it
    # cannot bind, and the supervisor below would then tear down the whole
    # stack. Failing fast here gives a clear message instead of a confusing
    # "Backend Server exited unexpectedly with code 3" half a second later.
    if is_port_in_use(args.backend_port, args.host):
        print(
            f"{TAG_ERROR}Port {args.backend_port} is already in use. "
            "Stop the process using it, or pass a different --backend-port."
        )
        sys.exit(1)
    if is_port_in_use(args.frontend_port, args.host):
        print(
            f"{TAG_ERROR}Port {args.frontend_port} is already in use. "
            "Stop the process using it, or pass a different --frontend-port."
        )
        sys.exit(1)

    # Configure signal handlers
    def sig_handler(sig, frame):
        cleanup_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    print(f"{TAG_SYSTEM}Starting ClubSphere full-stack servers...")

    # 1. Launch Backend (FastAPI via Uvicorn)
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.backend_port),
    ]
    if not args.no_reload:
        backend_cmd.append("--reload")

    env_backend = os.environ.copy()
    env_backend["PYTHONPATH"] = str(BACKEND_DIR)

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(BACKEND_DIR),
        env=env_backend,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    running_processes.append((backend_proc, "Backend Server"))

    # Thread to stream backend logs
    backend_thread = threading.Thread(
        target=stream_output,
        args=(backend_proc.stdout, TAG_BACKEND),
        daemon=True,
    )
    backend_thread.start()

    # 2. Launch Frontend (Vite dev server)
    npm_cmd = find_npm()
    frontend_cmd = [
        npm_cmd,
        "run",
        "dev",
        "--",
        "--host",
        args.host,
        "--port",
        str(args.frontend_port),
    ]

    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    running_processes.append((frontend_proc, "Frontend Server"))

    # Thread to stream frontend logs
    frontend_thread = threading.Thread(
        target=stream_output,
        args=(frontend_proc.stdout, TAG_FRONTEND),
        daemon=True,
    )
    frontend_thread.start()

    # 3. Health check monitor & browser launcher in separate background thread
    def monitor_and_announce():
        is_healthy = wait_for_backend_health(args.backend_port, timeout_secs=15)
        if is_healthy:
            print_banner(args.backend_port, args.frontend_port)
            if not args.no_browser:
                try:
                    time.sleep(1.0)
                    webbrowser.open(f"http://localhost:{args.frontend_port}")
                except Exception:
                    pass
        else:
            print(f"{TAG_WARN}Backend health check did not respond within timeout, but server may still be booting.")

    monitor_thread = threading.Thread(target=monitor_and_announce, daemon=True)
    monitor_thread.start()

    # 4. Supervise child processes
    try:
        while not shutdown_event.is_set():
            time.sleep(0.5)
            # Check if any process terminated unexpectedly
            for proc, name in running_processes:
                ret = proc.poll()
                if ret is not None and not shutdown_event.is_set():
                    print(f"{TAG_ERROR}{name} exited unexpectedly with code {ret}!")
                    cleanup_all()
                    sys.exit(ret)
    except KeyboardInterrupt:
        cleanup_all()
        sys.exit(0)


if __name__ == "__main__":
    main()
