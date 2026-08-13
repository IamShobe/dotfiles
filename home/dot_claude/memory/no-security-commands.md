---
name: No security/SSH commands
description: Never run SSH, credential, or security-sensitive commands — always defer to the user
type: feedback
---

Never run commands that touch SSH keys, SSH agent (`ssh-add`, `ssh-keygen`, etc.), system credentials, GPG keys, or any other security-sensitive settings.

**Why:** User explicitly requires human interaction for anything that could compromise the PC. Running `ssh-add` or similar was rejected as unacceptable.

**How to apply:** If a security-related command is needed (e.g., SSH push fails due to missing agent keys), stop, explain what failed, and tell the user to fix it themselves. Never attempt to resolve it programmatically.
