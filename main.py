#!/bin/python3

from collections.abc import Iterable
from typing import List
import os
from dotenv import load_dotenv

from github import Github
from github.Repository import Repository as GithubRepository

from pyforgejo import PyforgejoApi
from pyforgejo.errors.conflict_error import ConflictError
from pyforgejo import Repository as ForgejoRepository

from gitlab import Gitlab
from gitlab.v4.objects import Project as GitlabProject


class Repo:
    def __init__(
        self,
        orig_url: str,
        auth_username: str,
        auth_password: str,
        target_org: str,
        target_name: str,
    ) -> None:
        self.orig_url = orig_url
        self.auth_username = auth_username
        self.auth_password = auth_password
        self.target_org = target_org
        self.target_name = target_name

    def __str__(self) -> str:
        return f"{self.orig_url} -> {self.target_org}/{self.target_name}"


def get_github_com_repos() -> Iterable[Repo]:
    print("getting github.com repos")
    username = os.environ["GITHUB_COM_USERNAME"]
    password = os.environ["GITHUB_COM_PASSWORD"]
    github_client = Github(username, password)

    user = github_client.get_user()

    def github_com_repo_to_forgejo_mirror(repo: GithubRepository) -> Repo:
        return Repo(
            orig_url=repo.html_url,
            auth_username=username,
            auth_password=password,
            target_org="backup_github_com",
            target_name=repo.full_name.replace("/", "_"),
        )

    return map(github_com_repo_to_forgejo_mirror, user.get_repos())


def get_codeberg_org_repos() -> Iterable[Repo]:
    print("getting codeberg.org repos")
    # all repositories
    # repository: read
    # user: read
    username = os.environ["CODEBRG_ORG_USERNAME"]
    password = os.environ["CODEBRG_ORG_PASSWORD"]

    codeberg_client = PyforgejoApi(
        base_url="https://codeberg.org/api/v1",
        api_key=f"token {password}",
        timeout=1000000,
    )
    user = codeberg_client.user.get_current()
    uid = user.id
    search_result = codeberg_client.repository.repo_search(uid=uid)
    if not search_result.ok:
        raise ValueError("codeberg repo query failure")

    def codeberg_org_repo_to_forgejo_mirror(repo: ForgejoRepository) -> Repo:
        return Repo(
            orig_url=str(repo.html_url),
            auth_username=username,
            auth_password=password,
            target_org="backup_codeberg_org",
            target_name=str(repo.full_name).replace("/", "_"),
        )

    if search_result.data is None:
        raise ValueError

    return map(
        codeberg_org_repo_to_forgejo_mirror,
        search_result.data,
    )


def get_gitlab_kit_edu_repos() -> Iterable[Repo]:
    print("getting gitlab.kit.edu repos")
    username = os.environ["GITLAB_KIT_EDU_USERNAME"]
    password = os.environ["GITLAB_KIT_EDU_PASSWORD"]

    gitlab_client = Gitlab(url="https://gitlab.kit.edu", private_token=password)
    projects_list = gitlab_client.projects.list(
        all=True, iterator=True, membership=True
    )

    def gitlab_kit_edu_repo_to_forgejo_mirror(project: GitlabProject) -> Repo:
        return Repo(
            orig_url=project.http_url_to_repo,
            auth_username=username,
            auth_password=password,
            target_org="backup_gitlab_kit_edu",
            target_name=project.name_with_namespace.replace("/", "_")
            .replace(" ", "")
            .replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("Ä", "Ae")
            .replace("Ö", "Oe")
            .replace("Ü", "Ue"),
        )

    return map(gitlab_kit_edu_repo_to_forgejo_mirror, projects_list)


def create_mirror(forgejo_client: PyforgejoApi, repo: Repo) -> None:
    skip_repos = [
        "https://github.com/cct-group/ilias",
        "https://github.com/christopher-besch/literature",
        "https://github.com/christopher-besch/mc_missile",
        "https://github.com/christopher-besch/mc_missile_guidance",
        "https://github.com/christopher-besch/docker_setups",
        # TODO: delete this one from code.chris-besch.com
        "https://github.com/christopher-besch/configs",
        "https://codeberg.org/christopher-besch/forgejo",
        "https://codeberg.org/christopher-besch/forgejo_docs",
    ]
    if repo.orig_url in skip_repos:
        print(f"skipping: {repo}")
        return
    print(f"create mirror: {repo}")
    try:
        forgejo_client.repository.repo_migrate(
            clone_addr=repo.orig_url,
            repo_name=repo.target_name,
            repo_owner=repo.target_org,
            auth_username=repo.auth_username,
            auth_password=repo.auth_password,
            private=True,
            mirror=True,
            mirror_interval="168h0m0s",
            lfs=True,
        )
    except ConflictError as e:
        if e.status_code == 409:
            print("repo already exists")
            return
        raise e


def main():
    load_dotenv()

    repos: List[Repo] = []
    repos += get_github_com_repos()
    repos += get_codeberg_org_repos()
    repos += get_gitlab_kit_edu_repos()

    print(f"creating {len(repos)} mirrors")

    # print("\n".join([str(repo) for repo in repos]))
    # return

    forgejo_client = PyforgejoApi(
        base_url="https://code.chris-besch.com/api/v1",
        api_key=f"token {os.environ['CHRIS_CODE_TOKEN']}",
        timeout=1000000,
    )
    for repo in repos:
        create_mirror(forgejo_client, repo)

    print("All done.")
    print("Have a nice day.")


if __name__ == "__main__":
    main()
