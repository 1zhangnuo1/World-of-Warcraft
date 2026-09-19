# 源码提交与发布说明

## 目标

远程仓库应让 Ubuntu、Windows 开发者从同一份源码重建环境、验证行为和打包。源码与可复用配置属于输入，虚拟环境、缓存和编译产物属于输出，分开保存可以避免机器差异和大文件污染历史。

## 需要提交的文件

| 内容 | 当前项目位置 | 为什么提交 |
| --- | --- | --- |
| 程序与测试 | `src/`、`tests/` | 实现功能并验证行为 |
| 构建与检查脚本 | `scripts/`、`run.sh`、`run.ps1` | 两系统使用相同流程 |
| 依赖声明与锁文件 | `pyproject.toml`、`uv.lock`、`.python-version` | 重建一致的 Python 和依赖环境；锁文件需要提交 |
| 项目文档 | `README.md`、`docs/` | 说明操作、设计、限制与验收结果 |
| Git 和 CI 配置 | `.gitignore`、`.gitattributes`、`.github/` | 控制提交范围、换行格式和两系统自动验证 |
| 共享编辑器配置 | `.vscode/settings.json`、`launch.json`、`extensions.json` | 提供不含个人路径和凭据的测试、调试入口 |

未来新增的地图原始数据、素材源文件和必要配置也应根据用途提交；不能把所有 JSON、图片或二进制资源一概忽略。较大的必要资源应另行评估存储方式。

## 不需要提交的文件

| 内容 | 当前忽略规则 | 处理方式 |
| --- | --- | --- |
| 虚拟环境 | `.venv/`、`venv/`、`.tox/`、`.nox/` | 每台机器执行 `uv sync --locked` |
| 打包输出及中间文件 | `build/`、`dist/`、`*.egg-info/` | 按目标系统重新构建 |
| 本机截图与运行报告 | `artifacts/` | 本机验收使用，CI 报告通过构建附件保存 |
| 缓存与字节码 | `__pycache__/`、`*.py[cod]`、各工具缓存目录 | 自动重新生成 |
| 日志与覆盖率输出 | `*.log`、`logs/`、`.coverage*` 等 | 保留在本机或 CI 附件 |
| 私密配置 | `.env`、`.env.*`、`secrets/` | 不进入 Git；仅允许不含真实凭据的 example / sample 模板 |
| 个人编辑器和系统状态 | `.idea/`、`*.code-workspace`、交换文件、系统元数据 | 每台机器独立维护 |

本项目的 PyInstaller `.spec` 自动生成在 `build/` 下，随目录一起忽略；若未来维护手写 `.spec` 作为构建输入，应放进版本控制，因此没有全局忽略所有 `.spec`。

`.gitignore` 只影响尚未跟踪的文件。若误把产物加入了索引，应先检查具体路径，再用 `git rm --cached <文件>` 或 `git rm -r --cached <目录>` 从版本控制移除，本机文件仍可保留。它不是密钥检测器，提交前仍需检查暂存内容。

## 提交与发布流程

1. 完成改动并运行 `uv run python scripts/check.py`，必要时验证完整模拟和原生打包。
2. 检查 `git status --short`、`git diff`，仅暂存需要发布的源码与配置。
3. 检查 `git diff --cached --stat` 和 `git diff --cached`，确认没有构建输出、真实凭据、个人机器路径或无关修改。
4. 创建提交并正常推送到对应远程分支；若远程已有新提交，先整合后推送，不使用强制覆盖。
5. GitHub Actions 分别验证 Ubuntu、Windows 并生成构建附件。任务成功后才说明对应平台已验证通过。
6. 正式交付时可将整个 `dist/NavigationLab/` 打包成平台对应的压缩包，作为 Release 附件发布；不将其加入源码历史。

`.gitignore` 不会妨碍 CI 上传构建附件，因为 Git 跟踪和附件发布是两个独立流程。当前工作流只提供自动测试、打包和构建附件，不自动创建 Release。
