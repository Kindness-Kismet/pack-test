"""打包流程编排与校验。"""
import platform
import subprocess
from pathlib import Path

_WORK = Path("_work")


# ---- 公共校验 ----

def verify_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"{label} 未产出: {path}")
    size = path.stat().st_size
    print(f"  [OK] {label}: {path.name} ({size:,} bytes)")
    return path


# ---- Windows: Inno Setup ----

def run_windows_test() -> bool:
    from pack_test.fixtures import create_innosetup_fixture
    from pack_test.github import download_latest

    print("==> Windows Inno Setup 打包测试")
    work = _WORK / "win"
    if work.exists():
        import shutil
        shutil.rmtree(work)

    # 1. 下载最新 ISCC
    print("\n-- 下载 Inno Setup")
    iscc_exe = download_latest("jrsoftware/issrc", r"innosetup-.*\.exe$", work / "tools")

    # 2. 安装 Inno Setup
    print("\n-- 安装 Inno Setup")
    subprocess.run([
        str(iscc_exe),
        "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
        f"/DIR={work / 'inno'}",
    ], check=True)

    iscc = work / "inno" / "ISCC.exe"
    if not iscc.is_file():
        raise FileNotFoundError(f"ISCC.exe 安装失败: {iscc}")

    # 3. 生成 .iss + 打包
    print("\n-- 生成 ISS 并打包")
    iss = create_innosetup_fixture(work)
    subprocess.run([str(iscc), str(iss)], check=True)

    # 4. 校验
    print("\n-- 校验产出")
    output = work / "output" / "MyAppSetup.exe"
    verify_file(output, "Inno Setup 安装包")
    print("\n  打包测试通过！")
    return True


# ---- Linux: AppImage ----

def run_appimage_test() -> bool:
    from pack_test.fixtures import create_appdir
    from pack_test.github import download_latest

    print("==> Linux AppImage 打包测试")
    work = _WORK / "appimage"
    if work.exists():
        import shutil
        shutil.rmtree(work)

    # 1. 下载 appimagetool
    print("\n-- 下载 appimagetool")
    import os
    tool = download_latest("AppImage/AppImageKit", r"^appimagetool-x86_64\.AppImage$", work / "tools")
    # 提取绕过 FUSE（CI 环境通常无 FUSE）
    subprocess.run([str(tool), "--appimage-extract"], cwd=work / "tools", check=True)
    appimagetool = work / "tools" / "squashfs-root" / "AppRun"

    # 2. 构造 AppDir
    print("\n-- 生成 AppDir")
    appdir = create_appdir(work)

    # 3. 打包
    print("\n-- 打包 AppImage")
    output = work / "MyApp-x86_64.AppImage"
    subprocess.run(
        [str(appimagetool), str(appdir), str(output)],
        env={**os.environ, "ARCH": "x86_64"},
        check=True,
    )

    # 4. 校验
    print("\n-- 校验产出")
    verify_file(output, "AppImage")
    print("\n  打包测试通过！")
    return True


# ---- Linux: DEB ----

def run_deb_test() -> bool:
    from pack_test.fixtures import create_deb_root

    print("==> Linux deb 打包测试")
    work = _WORK / "deb"
    if work.exists():
        import shutil
        shutil.rmtree(work)

    root = create_deb_root(work)

    print("\n-- 打包 deb")
    output = work / "myapp_1.0.0_amd64.deb"
    subprocess.run(["dpkg-deb", "--build", str(root), str(output)], check=True)

    print("\n-- 校验产出")
    verify_file(output, "deb")
    # 额外校验：尝试解包检查 control
    print("\n-- 校验内容")
    result = subprocess.run(
        ["dpkg-deb", "--info", str(output)],
        capture_output=True, text=True, check=True,
    )
    if "Package: myapp" in result.stdout:
        print("  [OK] deb 内容校验通过")
    else:
        raise RuntimeError("deb content mismatch")

    print("\n  打包测试通过！")
    return True


# ---- Linux: RPM ----

def run_rpm_test() -> bool:
    from pack_test.fixtures import create_rpm_spec

    print("==> Linux RPM 打包测试")
    work = _WORK / "rpm"
    if work.exists():
        import shutil
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)

    spec = create_rpm_spec(work)
    rpmbuild_dir = work / "rpmbuild"
    for d in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
        (rpmbuild_dir / d).mkdir(parents=True, exist_ok=True)

    print("\n-- 打包 RPM")
    subprocess.run([
        "rpmbuild", "-bb", str(spec),
        "--define", f"_topdir {rpmbuild_dir}",
    ], check=True)

    # 产物在 RPMS/x86_64/myapp-1.0.0-1.x86_64.rpm
    rpms = list((rpmbuild_dir / "RPMS").rglob("*.rpm"))
    if not rpms:
        raise FileNotFoundError("RPM 未产出")

    print("\n-- 校验产出")
    verify_file(rpms[0], "RPM")
    print("\n  打包测试通过！")
    return True


# ---- Linux: AUR PKGBUILD (makepkg) ----

def run_aur_test() -> bool:
    print("==> AUR PKGBUILD 构建测试")
    work = _WORK / "aur"
    if work.exists():
        import shutil
        shutil.rmtree(work)
    work.mkdir(parents=True)

    # 优先使用仓库根目录的 PKGBUILD
    repo_pkgbuild = Path("PKGBUILD")
    if repo_pkgbuild.is_file():
        import shutil
        shutil.copy(repo_pkgbuild, work / "PKGBUILD")
    else:
        (work / "PKGBUILD").write_text(
            "pkgname=myapp\n"
            "pkgver=1.0.0\n"
            "pkgrel=1\n"
            "pkgdesc='Test package'\n"
            "arch=('x86_64')\n"
            "url='https://example.com'\n"
            "license=('MIT')\n\n"
            "package() {\n"
            '    mkdir -p "$pkgdir/usr/bin"\n'
            '    echo \'#!/bin/sh\' > "$pkgdir/usr/bin/myapp"\n'
            '    echo \'echo hello\' >> "$pkgdir/usr/bin/myapp"\n'
            '    chmod 755 "$pkgdir/usr/bin/myapp"\n'
            "}\n"
        )

    print(f"-- 构建 PKGBUILD")
    subprocess.run(
        ["makepkg", "-sfc", "--noconfirm"],
        cwd=work,
        check=True,
    )

    # 校验 .pkg.tar.zst
    pkgs = list(work.glob("*.pkg.tar.*"))
    if not pkgs:
        raise FileNotFoundError("AUR 包未产出")

    print("\n-- 校验产出")
    verify_file(pkgs[0], "AUR 包")
    print("\n  打包测试通过！")
    return True


# ---- macOS: DMG ----

def run_dmg_test() -> bool:
    from pack_test.fixtures import create_macos_app

    print("==> macOS DMG 打包测试")
    work = _WORK / "dmg"
    if work.exists():
        import shutil
        shutil.rmtree(work)

    app = create_macos_app(work)

    output = work / "MyApp.dmg"
    subprocess.run([
        "hdiutil", "create",
        "-volname", "MyApp",
        "-srcfolder", str(app),
        "-ov", "-format", "UDZO",
        str(output),
    ], check=True)

    print("\n-- 校验产出")
    verify_file(output, "DMG")
    print("\n  打包测试通过！")
    return True


# ---- macOS: PKG ----

def run_pkg_test() -> bool:
    from pack_test.fixtures import create_macos_app

    print("==> macOS PKG 打包测试")
    work = _WORK / "pkg"
    if work.exists():
        import shutil
        shutil.rmtree(work)

    app = create_macos_app(work)

    component_pkg = work / "MyApp-component.pkg"
    subprocess.run([
        "pkgbuild",
        "--root", str(app),
        "--identifier", "com.example.myapp",
        "--version", "1.0.0",
        "--install-location", "/Applications/MyApp.app",
        str(component_pkg),
    ], check=True)

    output = work / "MyApp.pkg"
    subprocess.run([
        "productbuild",
        "--package", str(component_pkg),
        str(output),
    ], check=True)

    print("\n-- 校验产出")
    verify_file(output, "PKG")
    print("\n  打包测试通过！")
    return True


# ---- 平台分发 ----

def run_platform(platform_name: str) -> bool:
    mapping = {
        "win":     run_windows_test,
        "appimage": run_appimage_test,
        "deb":     run_deb_test,
        "rpm":     run_rpm_test,
        "aur":     run_aur_test,
        "dmg":     run_dmg_test,
        "pkg":     run_pkg_test,
    }
    fn = mapping.get(platform_name)
    if fn is None:
        print(f"未知平台: {platform_name}。支持: {', '.join(mapping)}")
        return False
    return fn()
