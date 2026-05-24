"""CLI 入口。"""
import argparse
import platform as host_platform
import sys

from pack_test.pack import run_platform


def main() -> None:
    parser = argparse.ArgumentParser(description="多平台安装器打包验证工具")
    parser.add_argument(
        "platform",
        nargs="?",
        help="目标平台 (win / appimage / deb / rpm / aur / dmg / pkg)。不指定则自动检测。",
    )
    args = parser.parse_args()

    if args.platform:
        ok = run_platform(args.platform)
    else:
        ok = run_auto()
    sys.exit(0 if ok else 1)


def run_auto() -> bool:
    system = host_platform.system().lower()
    if system == "windows":
        print("自动检测: Windows -> Inno Setup\n")
        return run_platform("win")
    elif system == "darwin":
        print("自动检测: macOS -> DMG + PKG\n")
        ok1 = run_platform("dmg")
        ok2 = run_platform("pkg")
        return ok1 and ok2
    else:
        print("自动检测: Linux -> AppImage + deb + RPM + AUR\n")
        ok = True
        for p in ("appimage", "deb", "rpm", "aur"):
            if not run_platform(p):
                ok = False
        return ok
