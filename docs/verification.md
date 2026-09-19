# 第一阶段验收记录

日期：2026-09-19。目标是验证实际移动闭环，而不只检查能否生成路径。

## 本机环境

- Ubuntu 24.04.4 LTS，x86_64，glibc 2.39。
- Python 3.12.3；uv 0.10.9。
- pygame-ce 2.5.8；PyInstaller 6.22.3；具体依赖见根目录 `uv.lock`。
- 本机 `.venv` 已创建，可以直接运行 `uv run navigation-lab`。

## 已完成的检查

`uv run python scripts/check.py` 通过：Ruff 代码检查、格式检查、16 个源码文件的 mypy 严格类型检查，以及 50 项 pytest 测试。

测试包括：20 组随机地图对照独立 BFS 验证 A* 最短距离；非网格加权节点寻路；连续运动与途中改道；大步长碰撞与禁止切墙角；无路等待和清障恢复；移动故障与卡死重规划；地图变化不掩盖卡死；暂停计时；边界格保护；12 个随机种子的完整闭环；不导入 Pygame 的无窗口执行；超时失败退出码；GUI 绘制、按键与鼠标操作。

## 完整演示结果

同一默认场景 seed=7 分别在源码无窗口模式、打包后的无窗口模式、打包后的真实桌面窗口运行。三种方式的最终报告一致：

| 项目 | 实测结果 |
| --- | --- |
| 最终状态 | arrived |
| 实际终点 | (13, 13, 0)，浮点误差小于 1e-6 |
| 模拟耗时 | 14.983 秒 |
| 实际移动距离 | 31.167 格 |
| 自动障碍 | 5 次 |
| 剩余路线失效 | 5 次 |
| 卡死检测 | 2 次 |
| 重规划 | 7 次 |

原始报告保存在本机 `artifacts/acceptance.json`、`artifacts/packaged-acceptance.json`、`artifacts/packaged-gui-report.json`。卡死恢复截图为 `artifacts/gui-recovery.png`，打包程序到达截图为 `artifacts/packaged-arrived.png`。已检查中文、布局、状态与轨迹显示。`artifacts` 是生成目录，不随源码提交。

## 原生打包和验证范围

`uv run python scripts/build.py` 在本机成功，生成约 39 MB 的 `dist/NavigationLab/`。其可执行文件已通过无窗口闭环及真实桌面窗口完整到达验证。

Windows 已提供 PowerShell 启动脚本、相同的 uv 锁文件、VS Code 调试配置和 Windows / Ubuntu CI 构建矩阵；**本轮没有 Windows 主机，因此没有声称 Windows 已实测通过，也没有生成 Windows exe**。后续在 Windows 执行 `uv sync --locked`、`uv run python scripts/check.py`、`uv run python scripts/build.py` 即可做原生验收。GitHub Actions 需要把源码放入 GitHub 仓库后才会执行。

当前已交付 2D 验证环境。3D Navmesh、多 Agent、有限半径碰撞和真实外部执行器属于下一阶段，详见 `architecture.md`。
