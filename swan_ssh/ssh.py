import pexpect
import sys
import signal
import shutil
from rich.console import Console

console = Console()

def connect(ip: str, port: int, user: str, password: str):
    console.print(f"[cyan]Initiating connection to {user}@{ip}:{port}...[/cyan]")
    
    # We use StrictHostKeyChecking=no to avoid getting stuck on the 'Are you sure you want to continue connecting (yes/no/[fingerprint])?' prompt for unverified hosts
    cmd = f"ssh -o StrictHostKeyChecking=no -p {port} {user}@{ip}"
    
    try:
        # Spawn the ssh process
        child = pexpect.spawn(cmd, encoding='utf-8')
        
        def sigwinch_passthrough(sig, data):
            if not child.closed:
                size = shutil.get_terminal_size()
                child.setwinsize(size.lines, size.columns)
                
        # Set initial terminal size
        sigwinch_passthrough(None, None)
        
        # Register the signal handler for terminal resizing
        signal.signal(signal.SIGWINCH, sigwinch_passthrough)
        
        # We expect a password prompt. Wait up to 15 seconds.
        # This will match generic password prompts from ssh
        idx = child.expect(['[Pp]assword:', pexpect.EOF, pexpect.TIMEOUT], timeout=15)
        
        if idx == 0:
            # We got the password prompt, send the password
            child.sendline(password)
        elif idx == 1:
            console.print("[bold red]Connection closed unexpectedly before authentication completed.[/bold red]")
            return
        elif idx == 2:
            console.print("[bold red]Connection timed out waiting for password prompt.[/bold red]")
            return
            
        # Give control directly to the user so they can interact with the server shell
        child.interact()
        
    except Exception as e:
        console.print(f"[bold red]Failed to connect: {e}[/bold red]")
