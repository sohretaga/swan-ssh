import json
import uuid
import sys
from pathlib import Path
from rich.console import Console

console = Console()

def get_swan_dir() -> Path:
    return Path("~/.swan-ssh").expanduser()

def get_servers_file() -> Path:
    return get_swan_dir() / "servers.json"

def init_directory():
    d = get_swan_dir()
    d.mkdir(parents=True, exist_ok=True)

def load_servers() -> list:
    f = get_servers_file()
    if not f.exists():
        return []
    try:
        with open(f, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []

def save_servers(servers: list):
    f = get_servers_file()
    with open(f, "w") as file:
        json.dump(servers, file, indent=4)

def generate_short_id() -> str:
    return uuid.uuid4().hex[:8]

def add_server(label: str, ip: str, port: int, username: str, password: str) -> str:
    servers = load_servers()
    server_id = generate_short_id()
    new_server = {
        "id": server_id,
        "label": label,
        "ip": ip,
        "port": port,
        "username": username,
        "password": password
    }
    servers.append(new_server)
    save_servers(servers)
    return server_id

def get_server(server_id: str) -> dict:
    servers = load_servers()
    # Support partial matches like docker
    matches = [s for s in servers if s["id"].startswith(server_id)]
    if not matches:
        return None
    if len(matches) > 1:
        console.print(f"[bold red]Multiple servers match ID {server_id}. Please be more specific.[/bold red]")
        sys.exit(1)
    return matches[0]

def remove_server(server_id: str) -> bool:
    servers = load_servers()
    matches = [s for s in servers if s["id"].startswith(server_id)]
    if not matches:
        return False
    if len(matches) > 1:
        console.print(f"[bold red]Multiple servers match ID {server_id}. Please be more specific.[/bold red]")
        sys.exit(1)
        
    target_id = matches[0]["id"]
    servers = [s for s in servers if s["id"] != target_id]
    save_servers(servers)
    return True
