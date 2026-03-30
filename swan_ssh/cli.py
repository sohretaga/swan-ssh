import typer
from rich.console import Console
from rich.table import Table
import sys
import shutil

from . import storage
from . import git_manager
from . import ssh
from . import __version__

# Name it "swan" so help text is "swan". Disable default completion flags for a cleaner UI.
app = typer.Typer(help="Swan SSH: Sync and manage SSH servers via Git", add_completion=False)
console = Console()

def check_initialized():
    """Ensure that the local Git repository exists before allowing mutations."""
    if not (storage.get_swan_dir() / ".git").exists():
        console.print("[bold red]Swan SSH is not initialized yet![/bold red]")
        console.print("[yellow]Please run 'swan init' first to configure your GitHub repository.[/yellow]")
        raise typer.Exit(1)

@app.command()
def init(url: str = typer.Option(..., prompt="Enter your config repo URL", help="The Git repository URL for storing server configs")):
    """Initialize Swan SSH with a Git repository."""
    storage.init_directory()
    git_manager.init_repo(url)

@app.command()
def add():
    """Add a new SSH server configuration."""
    check_initialized()
    label = typer.prompt("Label")
    ip = typer.prompt("Server IP")
    port = typer.prompt("Port", default="22")
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)

    # First, silently grab any remote changes so we don't conflict 
    git_manager.pull_silent()

    server_id = storage.add_server(label, ip, int(port), username, password)
    console.print(f"[green]Server added successfully with ID: {server_id}[/green]")
    
    git_manager.commit_and_push(f"feat: add server '{label}' ({server_id})")

@app.command()
def rm(server_id: str):
    """Remove a server by its container-style ID."""
    check_initialized()
    # First, silently grab any remote changes to ensure exact ID match
    git_manager.pull_silent()
    
    servers = storage.load_servers()
    matches = [s for s in servers if s["id"].startswith(server_id)]
    
    if not matches:
         console.print(f"[bold red]Server ID '{server_id}' not found.[/bold red]")
         raise typer.Exit(1)
         
    if len(matches) > 1:
         console.print(f"[bold red]Multiple servers match ID {server_id}. Please be more specific.[/bold red]")
         raise typer.Exit(1)
         
    target = matches[0]
    console.print(f"Server found: [cyan]{target['label']}[/cyan] ({target['username']}@{target['ip']}:{target['port']})")
    confirm = typer.confirm("Are you sure you want to delete this server?")
    
    if not confirm:
        console.print("[yellow]Deletion cancelled.[/yellow]")
        return
        
    storage.remove_server(target["id"])
    console.print(f"[green]Server {target['id']} removed locally.[/green]")
    git_manager.commit_and_push(f"del: remove server '{target['label']}' ({target['id']})")

@app.command(name="list")
def list_cmd():
    """List all saved server configurations."""
    check_initialized()
    servers = storage.load_servers()
    if not servers:
        console.print("[yellow]No servers found. Add one with 'swan add'.[/yellow]")
        return
        
    table = Table(title="Swan SSH Servers")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("LABEL", style="magenta")
    table.add_column("IP", style="green")
    table.add_column("PORT", style="blue")
    
    for s in servers:
        table.add_row(s["id"], s["label"], s["ip"], str(s["port"]))
        
    console.print(table)

@app.command(name="connect")
def connect_cmd(server_id: str):
    """Connect to a server by its ID."""
    check_initialized()
    server = storage.get_server(server_id)
    if not server:
        # get_server already prints error on multiple matches
        if server is None:
            console.print(f"[bold red]Server ID '{server_id}' not found.[/bold red]")
        raise typer.Exit(1)
        
    ssh.connect(server["ip"], server["port"], server["username"], server["password"])

@app.command()
def sync():
    """Pull the latest server configurations from the remote repository."""
    check_initialized()
    git_manager.sync_repo()

@app.command()
def destroy():
    """Completely remove the local ~/.swan-ssh directory to prepare for uninstallation."""
    console.print("[bold red]WARNING: This will delete ALL local configurations and the cloned git repository![/bold red]")
    console.print("[yellow]Note: Your data will remain safe and sound on your remote GitHub repository.[/yellow]")
    confirm = typer.confirm("Are you ABSOLUTELY sure you want to delete the local Swan SSH root directory?")
    
    if confirm:
        swan_dir = storage.get_swan_dir()
        if swan_dir.exists():
            shutil.rmtree(swan_dir)
            console.print(f"[green]Successfully removed {swan_dir}. You can now safely run 'pipx uninstall swan-ssh'.[/green]")
        else:
            console.print("[yellow]The directory does not exist. Nothing to do.[/yellow]")
    else:
        console.print("[cyan]Destroy operation cancelled.[/cyan]")

def version_callback(value: bool):
    if value:
        console.print(f"Swan SSH version {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(None, "--version", callback=version_callback, is_eager=True, help="Show the tool version."),
):
    pass

if __name__ == "__main__":
    app()
