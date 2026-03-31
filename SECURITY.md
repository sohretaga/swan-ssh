# Security Policy

## Supported Versions

Currently, only the latest version of Swan SSH is supported with security updates. We recommend always keeping your Swan SSH installation up to date.

| Version | Supported          |
| ------- | ------------------ |
| >= 1.0.0| :white_check_mark: |
| < 1.0.0 | :x:                |

## Important Security Considerations

Swan SSH is designed to store your SSH server details, including IP addresses, usernames, and **passwords/credentials**. These details are committed to a Git repository to allow synchronization seamlessly across your devices. 

To ensure the security of your data, please strictly follow these rules:
- **Always use a strictly PRIVATE Git repository** (e.g., a private repo on GitHub, GitLab, or Bitbucket) when running `swan init`.
- **Never** initialize Swan SSH with a public repository, as your server credentials will be exposed to the internet.
- Ensure that the devices where you use Swan SSH are secure, as the local clone (`~/.swan-ssh/`) contains your configuration in its local Git history.

## Reporting a Vulnerability

If you discover a security vulnerability in Swan SSH, please **do not** report it by opening a public GitHub issue.

Instead, please contact the maintainer directly (e.g., via email). 
Please provide a detailed description of the issue, the steps to reproduce it, and any potential impact. We will evaluate the vulnerability and work on a fix as quickly as possible.

We appreciate your help and responsible disclosure in making Swan SSH secure for everyone!
