#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "env" / "repository-bootstrap.json"
DEFAULT_ENV_CANDIDATES = [
    Path.home() / "VSCodespace" / ".env",
    Path.home() / ".env",
    REPO_ROOT / ".env.local",
]
ENV_KEY_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate GitHub repository variables and secrets from the canonical bootstrap inventory."
    )
    parser.add_argument("--owner", help="GitHub owner/org to target. Defaults to manifest owner.")
    parser.add_argument(
        "--repo",
        action="append",
        default=[],
        help="Repository name, full owner/repo, or comma-separated list. Repeat as needed.",
    )
    parser.add_argument(
        "--all-default-repos",
        action="store_true",
        help="Populate every repository listed in env/repository-bootstrap.json.",
    )
    parser.add_argument("--env-file", help="Optional .env file to load before current process env.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Bootstrap manifest path.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned updates without calling gh.")
    return parser.parse_args()


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not ENV_KEY_PATTERN.match(key):
            continue
        value = value.strip().strip('"').strip("'")
        data[key] = value
    return data


def load_env_map(env_file: str | None) -> tuple[dict[str, str], Path | None]:
    env_map: dict[str, str] = {}
    loaded_file: Path | None = None

    if env_file:
        candidate = Path(env_file).expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f".env file not found: {candidate}")
        env_map.update(parse_env_file(candidate))
        loaded_file = candidate
    else:
        for candidate in DEFAULT_ENV_CANDIDATES:
            expanded = candidate.expanduser()
            if expanded.is_file():
                env_map.update(parse_env_file(expanded))
                loaded_file = expanded.resolve()
                break

    for key, value in os.environ.items():
        if ENV_KEY_PATTERN.match(key):
            env_map[key] = value

    if env_map.get("GITHUB_MCP_PAT") and not env_map.get("GITHUB_TOKEN"):
        env_map["GITHUB_TOKEN"] = env_map["GITHUB_MCP_PAT"]

    return env_map, loaded_file


def expand_repositories(repo_args: list[str]) -> list[str]:
    repos: list[str] = []
    seen: set[str] = set()
    for raw in repo_args:
        for repo in [item.strip() for item in raw.split(",")]:
            if not repo:
                continue
            if repo not in seen:
                repos.append(repo)
                seen.add(repo)
    return repos


def qualify_repo(owner: str, repo: str) -> str:
    return repo if "/" in repo else f"{owner}/{repo}"


def gh_set(setting_type: str, qualified_repo: str, name: str, value: str, dry_run: bool) -> None:
    command = ["gh", setting_type, "set", name, "--repo", qualified_repo, "--body", value]
    if dry_run:
        print(f"DRY-RUN {setting_type} {qualified_repo} {name}")
        return
    subprocess.run(command, check=True, text=True, capture_output=True)


def main() -> int:
    args = parse_args()
    manifest = load_manifest(Path(args.manifest).expanduser().resolve())
    owner = args.owner or manifest.get("owner") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not owner:
        raise SystemExit("No owner provided. Use --owner or set owner in the manifest.")

    repos = expand_repositories(args.repo)
    if args.all_default_repos:
        repos.extend(expand_repositories(manifest.get("defaultRepositories", [])))

    deduped_repos = []
    seen_repos: set[str] = set()
    for repo in repos:
        if repo not in seen_repos:
            deduped_repos.append(repo)
            seen_repos.add(repo)

    if not deduped_repos:
        raise SystemExit("No repositories selected. Pass --repo or --all-default-repos.")

    env_map, loaded_file = load_env_map(args.env_file)

    if args.dry_run:
        print("Running in dry-run mode.")

    if loaded_file:
        print(f"Loaded baseline values from {loaded_file}")
    else:
        print("No local .env file found; using current process environment only.")

    if not args.dry_run and not shutil.which("gh"):
        raise SystemExit("GitHub CLI (gh) is required.")

    secret_names = manifest.get("secrets", [])
    variable_names = manifest.get("variables", [])

    overall_missing: dict[str, list[str]] = {}
    for repo in deduped_repos:
        qualified_repo = qualify_repo(owner, repo)
        updated_secrets = 0
        updated_variables = 0
        missing: list[str] = []
        print(f"\n==> {qualified_repo}")

        for name in secret_names:
            value = env_map.get(name, "")
            if not value:
                missing.append(name)
                continue
            gh_set("secret", qualified_repo, name, value, args.dry_run)
            updated_secrets += 1

        for name in variable_names:
            value = env_map.get(name, "")
            if not value:
                missing.append(name)
                continue
            gh_set("variable", qualified_repo, name, value, args.dry_run)
            updated_variables += 1

        overall_missing[qualified_repo] = missing
        print(f"Updated secrets: {updated_secrets}")
        print(f"Updated variables: {updated_variables}")
        if missing:
            print(f"Skipped missing values: {', '.join(sorted(missing))}")

    missing_total = sum(len(values) for values in overall_missing.values())
    print("\nDone.")
    print(f"Repositories processed: {len(deduped_repos)}")
    print(f"Missing values skipped: {missing_total}")
    return 0
if __name__ == "__main__":
    sys.exit(main())
