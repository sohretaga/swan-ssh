import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def run_git_cmd(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)

def init_repo(repo_url: str):
    cwd = Path("~/.swan-ssh").expanduser()
    git_dir = cwd / ".git"
    
    if not git_dir.exists():
        console.print("[cyan]Initializing local git repository...[/cyan]")
        subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=cwd, check=True, capture_output=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=cwd, check=True, capture_output=True)

    console.print("[cyan]Checking remote repository status...[/cyan]")
    ls_remote = run_git_cmd(["git", "ls-remote", "--heads", "origin", "main"], cwd)
    
    if ls_remote.returncode != 0:
        console.print("[bold red]Failed to connect to remote repository. Please ensure the URL is correct and you have git access.[/bold red]")
        console.print(f"[dim]{ls_remote.stderr.strip()}[/dim]")
        return
        
    if not ls_remote.stdout.strip():
        console.print("[yellow]Remote repository appears to be empty. It will be initialized automatically on your first 'swan add'.[/yellow]")
        return

    console.print("[cyan]Attempting to pull existing servers config from remote...[/cyan]")
    res = run_git_cmd(["git", "pull", "origin", "main"], cwd)
    if res.returncode == 0:
        console.print("[green]Successfully synced from remote![/green]")
    else:
        console.print("[bold red]Failed to sync from remote. Please check your connection.[/bold red]")
        console.print(f"[dim]{res.stderr.strip()}[/dim]")

def commit_and_push(message: str):
    cwd = Path("~/.swan-ssh").expanduser()
    run_git_cmd(["git", "add", "."], cwd)
    
    # Check if there are changes
    status = run_git_cmd(["git", "status", "--porcelain"], cwd)
    if not status.stdout.strip():
        # Nothing to commit
        return

    commit = run_git_cmd(["git", "commit", "-m", message], cwd)
    if commit.returncode != 0:
        console.print("[bold red]Failed to commit changes locally.[/bold red]")
        console.print(commit.stderr)
        return

    console.print("[cyan]Pushing changes to remote repository...[/cyan]")
    push = run_git_cmd(["git", "push", "-u", "origin", "main"], cwd)
    
    if push.returncode == 0:
        console.print(f"[green]Successfully pushed: '{message}'[/green]")
    else:
        # Check if push was rejected due to sync issues (conflict)
        if "fetch first" in push.stderr or "rejected" in push.stderr:
            console.print("[yellow]Remote repository has newer commits (Conflict). Attempting auto-merge...[/yellow]")
            # Pull with rebase to keep linear history without noisy merge commits
            pull_res = run_git_cmd(["git", "pull", "--rebase", "origin", "main"], cwd)
            if pull_res.returncode == 0:
                push2 = run_git_cmd(["git", "push", "-u", "origin", "main"], cwd)
                if push2.returncode == 0:
                    console.print(f"[green]Successfully auto-merged and pushed: '{message}'[/green]")
                    return
            else:
                # Abort rebase if auto-merge fails so user isn't stuck
                run_git_cmd(["git", "rebase", "--abort"], cwd)
                console.print("[bold red]Hard conflict detected! Could not auto-merge. Please fix 'servers.json' manually.[/bold red]")
                
        console.print("[bold red]Failed to push changes to remote repository. Check auth or conflicts.[/bold red]")
        console.print(f"[dim]{push.stderr.strip()}[/dim]")

def pull_silent():
    """Silently pulls from remote prior to operations to prevent most out-of-sync conflicts."""
    cwd = Path("~/.swan-ssh").expanduser()
    if (cwd / ".git").exists():
        run_git_cmd(["git", "pull", "--rebase", "origin", "main"], cwd)

def sync_repo():
    cwd = Path("~/.swan-ssh").expanduser()
    console.print("[cyan]Syncing repository...[/cyan]")
    pull = run_git_cmd(["git", "pull", "origin", "main"], cwd)
    if pull.returncode == 0:
         console.print("[green]Successfully synced with remote.[/green]")
    else:
         console.print("[bold red]Failed to sync. Check network or git auth.[/bold red]")
         console.print(pull.stderr)
