# SSH Mesh Keys — 3-Machine Bidirectional Setup

Generated 2026-04-22. Three ED25519 key pairs for full bidirectional SSH between all machines.

## Machines

| Machine | Key Name | Comment |
|---------|----------|---------|
| MacBook | `macbook/macbook_ed25519` | user@MacBook |
| Win11 Laptop (i7) | `laptop/laptop_ed25519` | user@Win11-Laptop |
| Desktop (CLX-DESKTOP) | `desktop/desktop_ed25519` | user@DESKTOP-PHMUM56 |

## How It Works

Each machine gets its own private key + all three public keys in `authorized_keys`. Any machine can SSH into any other.

## Setup

Run the setup script **on each machine**:

- **MacBook:** `chmod +x setup-macbook.sh && ./setup-macbook.sh`
- **Laptop:** `powershell -ExecutionPolicy Bypass -File setup-laptop.ps1`
- **Desktop:** `powershell -ExecutionPolicy Bypass -File setup-desktop.ps1`

Each script installs the private key, updates `authorized_keys`, and adds SSH config aliases. You'll need to fill in the `HostName` (IP or hostname) for each remote machine in `~/.ssh/config` after running.

## Requirements

- **Windows machines:** OpenSSH Server must be installed (needs admin). Run `scripts/install-sshd.ps1`.
- **MacBook:** Enable Remote Login in System Settings > General > Sharing.
- After installing sshd on Windows, copy `authorized_keys` to `%ProgramData%\ssh\administrators_authorized_keys` with proper ACLs (the setup scripts show the exact commands).

## Security Note

These private keys have no passphrase. For additional security, you can add one:
```
ssh-keygen -p -f ~/.ssh/id_ed25519_mesh
```
