#!/bin/python3

from collections.abc import Iterable
from typing import List
import os
from dotenv import load_dotenv

from github import Github
from github.Repository import Repository as GithubRepository

from pyforgejo import PyforgejoApi
from pyforgejo.errors.conflict_error import ConflictError


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


def get_github_com_repos() -> Iterable[Repo]:
    print("getting github repos")
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
    return []


def create_mirror(forgejo_client: PyforgejoApi, repo: Repo) -> None:
    print(f"create mirror: {repo.orig_url}")
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

    forgejo_client = PyforgejoApi(
        base_url="https://code.chris-besch.com/api/v1",
        api_key=os.environ["CHRIS_CODE_TOKEN"],
        timeout=1000000,
    )
    for repo in repos:
        create_mirror(forgejo_client, repo)


if __name__ == "__main__":
    main()
