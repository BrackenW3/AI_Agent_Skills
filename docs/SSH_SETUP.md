# SSH Key Setup — Complete Reference

## Current Status
- i9 (192.168.1.21) SSH server: Running ✅
- Mac → i9: NOT working (passphrase issue)  
- i7 → i9: NOT tested
- WSL → i9: Needs own key
- Mac → i7: NOT set up

## Mac → i9 Fix (run in Mac Terminal once)
```bash
# Add key to macOS Keychain permanently (no passphrase prompt ever again)
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# Add to ~/.ssh/config so it persists across reboots
cat >> ~/.ssh/config << 'SSHCONF'
Host i9
  HostName 192.168.1.21
  User User
  IdentityFile ~/.ssh/id_ed25519
  AddKeysToAgent yes
  UseKeychain yes

Host i7
  HostName 192.168.1.23
  User willb
  IdentityFile ~/.ssh/id_ed25519
  AddKeysToAgent yes
  UseKeychain yes
SSHCONF

# Test
ssh i9 "echo connected to i9"
ssh i7 "echo connected to i7"
```

## Mac's Public Key (already known, add to i7)
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDcqeWeM11haiSDsvSvY4FeI79YD/m7XFqJaxMMi0n5y willbracken@MacBook-Pro.local
```

## Add Mac key to i7 (run on i7)
```powershell
# On i7 PowerShell as admin
$key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDcqeWeM11haiSDsvSvY4FeI79YD/m7XFqJaxMMi0n5y willbracken@MacBook-Pro.local"
Add-Content "$env:USERPROFILE\.ssh\authorized_keys" $key

# Ensure SSH server is running on i7
Get-Service sshd
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

## i7 → i9 (run on i7)
```cmd
ssh-keygen -t ed25519 -C "willb@i7" -f %USERPROFILE%\.ssh\id_ed25519_i7
# Then copy public key to i9:
type %USERPROFILE%\.ssh\id_ed25519_i7.pub | ssh User@192.168.1.21 "cat >> ~/.ssh/authorized_keys"
```

## WSL — Does it need its own key?
YES and NO:
- WSL has its own ~/.ssh/ separate from Windows
- But you can symlink Windows keys: ln -s /mnt/c/Users/User/.ssh/id_ed25519 ~/.ssh/id_ed25519
- Or generate a new WSL key: ssh-keygen -t ed25519 -C "wsl@i9"
- Simplest: just symlink from WSL to Windows keys

## WSL Key Symlink (run in WSL)
```bash
mkdir -p ~/.ssh
ln -sf /mnt/c/Users/User/.ssh/id_ed25519 ~/.ssh/id_ed25519
ln -sf /mnt/c/Users/User/.ssh/id_ed25519.pub ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/id_ed25519
ssh User@192.168.1.21 "echo WSL connected"
```

## Summary: What to run and where
| Task | Where | Command |
|------|-------|---------|
| Fix Mac passphrase | Mac Terminal | `ssh-add --apple-use-keychain ~/.ssh/id_ed25519` |
| Add Mac SSH config | Mac Terminal | Edit ~/.ssh/config (above) |
| Add Mac key to i7 | i7 PowerShell | Add to authorized_keys (above) |
| Enable SSH on i7 | i7 PowerShell as Admin | `Start-Service sshd` |
| WSL keys | WSL terminal | Symlink from Windows (above) |
