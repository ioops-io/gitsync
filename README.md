# Gitsync - A GIT syncronizer between two unrelated git repositories

## Use case

![diagram](usecase.drawio.png)

You work in different projects and you will not able make references during CI/CD or would you want to share code among unrelated project. The **Gitsync** will help you making two diferrent repositories in sync.

## Implementation

### Configuration example

In yours ```.gitsync``` folder create a file **.yml** (or as many as needed) configuring gitsync.

```yaml
gitsync:
  strategy: patch
  source:
    path: https://git.remote.fqdn/source/folderX
    branch: main
  target:
    path: source/folderY
    branch: develop
---
```

Check [sample gitsync](.gitsync_sample) files for configuration scenarios.

### Install gitsync

Create a ```.gitsync``` folder in your repository root's and install gitsync.

```bash
cd your-git-repo
mkdir .gitsync && cd .gitsync
curl https://gitsync.ioops.io/install.sh | bash
```

### Run gitsync

```bash
cd your-git-repo
python3 .gitsync/gitsync.py
```

You can run manually or thru your CI/CD pipelines as regular shell script.
