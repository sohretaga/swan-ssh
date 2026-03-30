# Swan SSH 🦢

A simple, fast, and beautiful CLI tool to manage and synchronize SSH connections seamlessly across all your devices using a private Git repository. Made with Python, Typer, and Rich.

![CLI Flow UI Demo](https://raw.githubusercontent.com/sabahhub/swan-ssh/main/assets/demo.gif) *(Feel free to add your own screenshot here)*

## Installation

The recommended way to install Swan SSH is via `pipx`. This ensures it's installed in an isolated environment without disturbing your system's Python packages.

```bash
pipx install swan-ssh
```

> **⚠️ Important Note on `pipx` PATH:**
> If you see a warning saying `~/.local/bin is not on your PATH`, you simply need to run:
> ```bash
> pipx ensurepath
> ```
> Then close and reopen your terminal. Your `swan` command will now be globally available!

## Usage Flow

1. **Initialize** the workspace:
   First, create a private GitHub repository. Then, run `swan init` and paste its URL.
   ```bash
   swan init
   ```

2. **Add a Server**:
   ```bash
   swan add
   # Prompts for label, ip, port, username, password
   # Automatically commits and pushes to your private repo behind the scenes!
   ```

3. **List Servers**:
   Brings up a beautiful formatting table of your servers.
   ```bash
   swan list
   ```

4. **Connect Instantly**:
   Using the short `ID` from the list command.
   ```bash
   swan connect <id>
   ```

5. **Sync from Another Device**:
   Installed Swan on your Macbook? Just run:
   ```bash
   swan init
   # Provide the same repo URL
   swan sync
   # Ready to connect!
   ```

6. **Remove a Server**:
   ```bash
   swan rm <id>
   ```

7. **Clean up & Uninstall**:
   If you ever want to completely remove the configuration directory (`~/.swan-ssh`) before uninstalling the tool, use:
   ```bash
   swan destroy
   pipx uninstall swan-ssh
   ```
