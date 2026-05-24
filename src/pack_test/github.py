"""GitHub Releases 最新资产下载。"""
import json
import os
import re
import urllib.request
from pathlib import Path


def get_latest_release(repo: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "pack-test")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def find_asset(release: dict, pattern: str) -> dict | None:
    regex = re.compile(pattern, re.IGNORECASE)
    for asset in release.get("assets", []):
        if regex.search(asset["name"]):
            return asset
    return None


def download_asset(asset: dict, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / asset["name"]

    url = asset["browser_download_url"]
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/octet-stream")
    req.add_header("User-Agent", "pack-test")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req) as resp:
        dest_path.write_bytes(resp.read())

    # Linux/macOS: 给二进制加执行权限
    if os.name != "nt":
        ext = dest_path.suffix.lower()
        if ext not in (".exe", ".msi", ".dmg", ".deb", ".rpm", ".zip", ".tar.gz", ".jar"):
            dest_path.chmod(0o755)

    return dest_path


def download_latest(repo: str, pattern: str, dest_dir: Path | None = None) -> Path:
    release = get_latest_release(repo)
    asset = find_asset(release, pattern)
    if asset is None:
        names = [a["name"] for a in release.get("assets", [])]
        raise ValueError(f"未找到匹配 {pattern!r} 的资产。可用: {names}")

    if dest_dir is None:
        dest_dir = Path.cwd() / "tools"

    print(f"  仓库: {repo}")
    print(f"  版本: {release['tag_name']}")
    print(f"  资产: {asset['name']} ({asset['size']:,} bytes)")
    return download_asset(asset, dest_dir)
