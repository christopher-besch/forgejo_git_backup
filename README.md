# Forgejo Git Backup

- Create `.env` file with in own directory, enter that directory afterwards:
    ```
    GITHUB_COM_USERNAME=christopher-besch
    GITHUB_COM_PASSWORD=

    GITLAB_KIT_EDU_USERNAME=christopher-besch
    GITLAB_KIT_EDU_PASSWORD=

    CODEBRG_ORG_USERNAME=christopher-besch
    CODEBRG_ORG_PASSWORD=

    CHRIS_CODE_TOKEN=
    ```
    Alternatively, load the file from the KeePass db.
- `sudo docker run --rm -ti -v .:/mnt:ro debian`
- `apt update && apt-get install -y git python3 python3-pip python3-venv`
- `python3 -m venv venv && chmod +x venv/bin/activate && . ./venv/bin/activate`
- `python3 -m pip install python-gitlab pyforgejo PyGithub`
- `git clone https://github.com/christopher-besch/forgejo_git_backup && cd forgejo_git_backup`
- `cp /mnt/.env ./.env`
- `python3 main.py`
- `exit`
- rm `.env`

### Other helpful commands
- `git remote add backup git@code.chris-besch.com:backup_gitlab_ext_iosb_fraunhofer_de/${PWD##*/} && git push backup --all`
