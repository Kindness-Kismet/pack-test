# pack-test

多平台安装器打包验证工具 — 动态下载各平台最新安装器，用最小 fixture 跑通完整打包流程，验证工具链是否正常。

## 覆盖范围

| 平台 | 格式 | 工具 | 来源 |
|------|------|------|------|
| Windows | `.exe` 安装包 | Inno Setup | [jrsoftware/issrc](https://github.com/jrsoftware/issrc) |
| Linux | `.AppImage` | appimagetool | [AppImage/AppImageKit](https://github.com/AppImage/AppImageKit) |
| Linux | `.deb` | dpkg-deb | 系统自带 |
| Linux | `.rpm` | rpmbuild | 系统 apt 安装 |
| Linux | `.pkg.tar.zst` (AUR) | makepkg | archlinux 容器 |
| macOS | `.dmg` | hdiutil | 系统自带 |
| macOS | `.pkg` | pkgbuild + productbuild | 系统自带 |

## 使用

```bash
pip install -e .
pack-test          # 自动检测平台，跑对应所有测试
pack-test win      # 指定平台
pack-test dmg
pack-test deb
```

## GitHub Actions

三个工作流各自独立，按需触发：

- `test-win.yml` — windows-latest runner
- `test-linux.yml` — AppImage / deb / RPM / AUR 四个并行 job
- `test-macos.yml` — DMG + PKG 两个并行 job

触发条件：push 到相关源文件路径，或手动 `workflow_dispatch`。

## 项目结构

```
src/pack_test/
  cli.py        CLI 入口
  github.py     GitHub Releases 最新版下载
  fixtures.py   各平台最小打包测试 fixture
  pack.py       打包流程编排与校验
PKGBUILD        AUR 测试用 PKGBUILD
```
