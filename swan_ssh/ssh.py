import pexpect
import sys
import signal
import shutil
import os
import stat
import paramiko
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TransferSpeedColumn

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

def get_local_dir_size(local_path: str) -> int:
    total = 0
    for root, dirs, files in os.walk(local_path):
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total

def get_remote_dir_size(sftp: paramiko.SFTPClient, remote_path: str) -> int:
    total = 0
    try:
        for attr in sftp.listdir_attr(remote_path):
            path = f"{remote_path}/{attr.filename}"
            if stat.S_ISDIR(attr.st_mode):
                total += get_remote_dir_size(sftp, path)
            else:
                total += attr.st_size
    except IOError:
        pass
    return total

def copy(ip: str, port: int, user: str, password: str, local_path: str, remote_path: str, recursive: bool, show_progress: bool, compress: bool, download: bool):
    console.print(f"[cyan]Connecting to {user}@{ip}:{port} for transfer...[/cyan]")
    
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh_client.connect(ip, port=port, username=user, password=password, compress=compress)
        sftp = ssh_client.open_sftp()
        
        # 0. Path resolution
        if download:
            if os.path.isdir(local_path):
                try:
                    remote_stat = sftp.stat(remote_path)
                    if not stat.S_ISDIR(remote_stat.st_mode):
                        local_path = os.path.join(local_path, os.path.basename(remote_path))
                except IOError:
                    pass
        else:
            try:
                remote_stat = sftp.stat(remote_path)
                if stat.S_ISDIR(remote_stat.st_mode) and not os.path.isdir(local_path):
                    remote_path = f"{remote_path.rstrip('/')}/{os.path.basename(local_path)}"
            except IOError:
                pass
        
        # 1. Size calculation
        total_size = 0
        if download:
            try:
                remote_stat = sftp.stat(remote_path)
                if stat.S_ISDIR(remote_stat.st_mode):
                    if not recursive:
                        console.print(f"[bold red]Remote path '{remote_path}' is a directory. Use --recursive to copy.[/bold red]")
                        return
                    total_size = get_remote_dir_size(sftp, remote_path)
                else:
                    total_size = remote_stat.st_size
            except IOError:
                console.print(f"[bold red]Remote path '{remote_path}' not found.[/bold red]")
                return
        else:
            if not os.path.exists(local_path):
                console.print(f"[bold red]Local path '{local_path}' not found.[/bold red]")
                return
            if os.path.isdir(local_path):
                if not recursive:
                    console.print(f"[bold red]Local path '{local_path}' is a directory. Use --recursive to copy.[/bold red]")
                    return
                total_size = get_local_dir_size(local_path)
            else:
                total_size = os.path.getsize(local_path)

        # Progress bar setup
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            transient=True,
            disable=not show_progress
        )
        
        with progress:
            desc = f"[cyan]Downloading from {remote_path}[/cyan]" if download else f"[cyan]Uploading to {remote_path}[/cyan]"
            task = progress.add_task(desc, total=total_size)
            
            global_transferred = [0]
            
            def make_callback(file_size):
                file_transferred = [0]
                def cb(transferred, total):
                    delta = transferred - file_transferred[0]
                    file_transferred[0] = transferred
                    global_transferred[0] += delta
                    progress.update(task, completed=global_transferred[0])
                return cb
                
            if download:
                if stat.S_ISDIR(remote_stat.st_mode):
                    def download_dir(rem_dir, loc_dir):
                        os.makedirs(loc_dir, exist_ok=True)
                        for attr in sftp.listdir_attr(rem_dir):
                            r_path = f"{rem_dir}/{attr.filename}"
                            l_path = os.path.join(loc_dir, attr.filename)
                            if stat.S_ISDIR(attr.st_mode):
                                download_dir(r_path, l_path)
                            else:
                                sftp.get(r_path, l_path, callback=make_callback(attr.st_size))
                    download_dir(remote_path, local_path)
                else:
                    sftp.get(remote_path, local_path, callback=make_callback(total_size))
            else:
                if os.path.isdir(local_path):
                    def upload_dir(loc_dir, rem_dir):
                        try:
                            sftp.stat(rem_dir)
                        except IOError:
                            sftp.mkdir(rem_dir)
                        for item in os.listdir(loc_dir):
                            l_path = os.path.join(loc_dir, item)
                            r_path = f"{rem_dir.rstrip('/')}/{item}"
                            if os.path.isdir(l_path):
                                upload_dir(l_path, r_path)
                            else:
                                sftp.put(l_path, r_path, callback=make_callback(os.path.getsize(l_path)))
                    upload_dir(local_path, remote_path)
                else:
                    sftp.put(local_path, remote_path, callback=make_callback(total_size))
                    
        console.print("[green]Transfer completed successfully![/green]")

    except Exception as e:
        console.print(f"[bold red]Transfer failed: {e}[/bold red]")
    finally:
        ssh_client.close()
