"""各平台最小打包测试 fixture 生成。"""
from pathlib import Path


def create_innosetup_fixture(work_dir: Path) -> Path:
    src = work_dir / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "myapp.exe").write_bytes(b"MZ\x00\x00")
    (src / "readme.txt").write_text("test\n")

    output_dir = work_dir / "output"
    output_dir.mkdir(exist_ok=True)

    iss = work_dir / "setup.iss"
    iss.write_text(
        "[Setup]\n"
        "AppName=MyApp\n"
        "AppVersion=1.0.0\n"
        "DefaultDirName={pf}\\MyApp\n"
        "OutputDir=output\n"
        "OutputBaseFilename=MyAppSetup\n"
        "Compression=lzma\n"
        "SolidCompression=yes\n\n"
        "[Files]\n"
        'Source: "src\\*"; DestDir: "{app}"; Flags: ignoreversion\n',
        encoding="utf-8",
    )
    return iss


def create_appdir(work_dir: Path) -> Path:
    appdir = work_dir / "MyApp.AppDir"
    appdir.mkdir(parents=True)

    (appdir / "AppRun").write_text("#!/bin/sh\necho hello\n")
    (appdir / "AppRun").chmod(0o755)

    (appdir / "myapp.desktop").write_text(
        "[Desktop Entry]\nType=Application\nName=MyApp\nExec=AppRun\nIcon=myapp\n"
    )
    (appdir / "myapp.png").write_bytes(b"")

    return appdir


def create_deb_root(work_dir: Path) -> Path:
    root = work_dir / "myapp_1.0.0"
    debian = root / "DEBIAN"
    debian.mkdir(parents=True)
    (debian / "control").write_text(
        "Package: myapp\nVersion: 1.0.0\nArchitecture: amd64\n"
        "Maintainer: test@example.com\nDescription: test\n"
    )

    bin_dir = root / "usr" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "myapp").write_text("#!/bin/sh\necho hello\n")
    (bin_dir / "myapp").chmod(0o755)

    return root


def create_rpm_spec(work_dir: Path) -> Path:
    spec = work_dir / "myapp.spec"
    spec.write_text(
        "Name: myapp\n"
        "Version: 1.0.0\n"
        "Release: 1\n"
        "Summary: test package\n"
        "License: MIT\n"
        "BuildArch: x86_64\n\n"
        "%description\n"
        "test\n\n"
        "%install\n"
        "mkdir -p %{buildroot}/usr/bin\n"
        "echo '#!/bin/sh' > %{buildroot}/usr/bin/myapp\n"
        "echo 'echo hello' >> %{buildroot}/usr/bin/myapp\n"
        "chmod 755 %{buildroot}/usr/bin/myapp\n\n"
        "%files\n"
        "/usr/bin/myapp\n"
    )
    return spec


def create_macos_app(work_dir: Path) -> Path:
    app = work_dir / "MyApp.app"
    macos = app / "Contents" / "MacOS"
    macos.mkdir(parents=True)

    plist = app / "Contents" / "Info.plist"
    plist.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"\n'
        '  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "    <key>CFBundleName</key><string>MyApp</string>\n"
        "    <key>CFBundleIdentifier</key><string>com.example.myapp</string>\n"
        "    <key>CFBundleVersion</key><string>1.0.0</string>\n"
        "    <key>CFBundleExecutable</key><string>myapp</string>\n"
        "</dict>\n"
        "</plist>\n"
    )

    exe = macos / "myapp"
    exe.write_text("#!/bin/sh\necho hello\n")
    exe.chmod(0o755)

    return app
