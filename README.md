# Navigation Lab · 2D 导航模拟器

第一阶段目标：在独立的 15×15 地图中，让 Agent 完成 **寻路 → 实际移动 → 遇障 / 卡死 → 重新规划 → 到达目标**。界面不是路径播放动画，红点位置来自移动执行器的真实模拟反馈。

使用 Python 3.12、Pygame 社区版 `pygame-ce`（代码仍然 `import pygame`）、uv 管理依赖。导航核心不依赖 Pygame，便于下一阶段接入其他地图和移动执行器。

## 1. 先运行起来

Ubuntu 和 Windows 均先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)，然后在项目根目录执行相同命令：

```text
uv sync --locked
uv run navigation-lab
```

uv 根据 `.python-version` 使用 Python 3.12，缺失时可自动下载；首次同步需要联网。它会为当前系统新建 `.venv`，安装锁定版本及开发工具。无需手工安装编译器即可使用预编译依赖开发本阶段项目。

- Ubuntu 快捷入口：`bash run.sh`
- Windows PowerShell 快捷入口：`powershell -ExecutionPolicy Bypass -File .\run.ps1`，或直接使用上面的 uv 命令。
- VS Code 打开此目录，选择 `.venv` 解释器后按 F5，选择 GUI 或无窗口模式。调试扩展见 `.vscode/extensions.json`。

**换电脑时复制源码、`pyproject.toml`、`uv.lock` 和配置文件；不要复制 `.venv`、`build` 或 `dist`。** 每个系统重新执行 `uv sync --locked`。Ubuntu 和 Windows 的虚拟环境及可执行文件不能混用。

## 2. 地图中的组成部分

- 红点：连续移动的 Agent；蓝色 S：起点；绿色双圆：目标。
- 绿色折线：当前路径；灰线：上一次路径；蓝灰线：实际走过的轨迹。
- 灰色方块：固定墙；橙色方块：运行期间出现的障碍。
- 右侧：实际坐标、重规划次数、卡死次数、无位移计时及事件记录。

默认 seed=7。自动演示每隔 2 秒从剩余路径中随机选一个位置放置临时障碍，共最多 5 次，每个 4.5 秒后消失；3.3 秒时注入一次 2.5 秒的移动执行故障。地图仍可走，但执行器暂时不移动，用来验证独立的卡死检测。

| 操作 | 效果 |
| --- | --- |
| Space / 暂停按钮 | 暂停或继续，模拟时钟和卡死计时一同暂停 |
| R | 用相同 seed 重置整个演示 |
| O | 立即在剩余路径上随机放置临时障碍 |
| J | 暂时冻结移动执行器，观察卡死检测与重规划 |
| D | 开关自动障碍，已有障碍仍按时消失 |
| 鼠标左键 | 添加 / 删除手动障碍；手动添加不会自动消失 |
| 鼠标右键 | 在可通行格上设置新的目标，重新出发 |
| Esc | 退出 |

起点、当前目标、Agent 所在格及固定墙不可添加障碍。手工封死所有通路会显示“暂无可行路线”，删除障碍后自动继续。到达后演示停在完成状态，R 重开或右键换目标。

## 3. 文件分层与工作流程

```text
src/navigation_lab/
  core/                   通用逻辑，不导入 pygame 或 adapters
    contracts.py          图、导航后端、移动执行器接口
    geometry.py           Vec3 世界坐标
    astar.py              泛型 A*，不限定节点必须是格子
    stuck.py              基于实际位移的卡死检测
    controller.py         规划、跟随、等待重试、恢复、到达状态
  adapters/               对接口的具体实现
    grid.py               2D 网格、坐标映射、碰撞和导航后端
    simulated_motor.py    带碰撞检查的连续移动执行器
  simulation/
    scenario.py           地图构造、随机事件、故障注入、模拟时钟
  presentation/
    pygame_app.py         绘制画面、处理键鼠、固定步长主循环
  app.py                  装配入口、GUI / headless、JSON 报告
tests/                    搜索正确性、恢复闭环、渲染与交互回归
scripts/                  跨平台质量检查与原生打包
docs/architecture.md      详细设计与 3D 接入边界
.github/workflows/        Ubuntu / Windows 测试与打包矩阵
```

每一步先更新模拟障碍，再交给控制器检查路线。路线有效时，控制器向移动执行器发出下一路点指令；执行器做碰撞检查后更新实际坐标。控制器根据实际坐标判断是否前进、卡死或到达，最后由 Pygame 显示同一份状态。

路线失效会立即重新规划；预期移动却连续 1.25 秒没有至少 0.06 格的有效位移，会触发卡死重规划。无路时每 0.75 秒重试，地图变化时提前重试。暂停和无路等待不计为卡死。重规划不会瞬移 Agent；途中会先连接回当前格中心，再走新路线。

## 4. 验证和打包

```text
uv run python scripts/check.py
uv run navigation-lab --headless --report artifacts/acceptance.json
uv run navigation-lab --seed 42
uv run navigation-lab --no-obstacles --no-demo-jam
uv run python scripts/build.py
```

无窗口模式复用完整模拟逻辑，不导入 Pygame；实际到达返回退出码 0，超时未到达返回 1。`--max-seconds 60` 限制模拟时长；JSON 包含实际终点、距离、故障和重规划记录。所有参数可用 `uv run navigation-lab --help` 查看。

PyInstaller 输出整个 `dist/NavigationLab/` 文件夹：

- Ubuntu 启动 `./dist/NavigationLab/NavigationLab`。
- Windows 启动 `dist\NavigationLab\NavigationLab.exe`。
- 分发时复制**整个文件夹**，接收方无需安装 Python。

这是将 Python、库和程序打包成原生系统可执行目录。[PyInstaller 需要在对应系统构建](https://pyinstaller.org/en/stable/operating-mode.html)，Ubuntu 不能直接产出 Windows exe。仓库附带两系统 CI，推送到 GitHub 后才会运行；未运行的 CI 不等于已通过 Windows 验证。Linux 本地构建以本机构建环境为兼容基线；CI 在 Ubuntu 22.04 构建用于较广兼容性。

## 5. 后续扩展边界

当前实现是单 Agent、四方向 Grid、点状碰撞模型，所有移动位于 z=0 平面。默认临时障碍有次数和寿命上限，因此基准场景能恢复；任意永久封路或永久执行器故障不能靠重新规划保证到达。

未来接 Navmesh 时保留控制器、卡死检测、世界坐标和报告机制，新增 `NavigationBackend` 实现负责多边形查询与路径走廊 / funnel 路点，同时替换 `MotionDriver` 和显示层。现有 A* 支持任意可哈希节点，但 3D 碰撞、Agent 半径、坡度、跳跃和实际执行反馈需要在新适配器实现；不是只把地图数组换掉就完成 3D。

详细接口、当前取舍和下一阶段建议见 [架构说明](docs/architecture.md)，本轮实测环境与结果见 [验收记录](docs/verification.md)。依赖与用法参考：[Pygame 文档](https://pyga.me/docs/)、[uv 项目管理](https://docs.astral.sh/uv/guides/projects/)。

## 6. 源码提交与交付文件

Git 仓库保存重建项目所需的输入，自动生成的结果由构建流程产出。具体约定见 [提交与发布说明](docs/repository.md)。

- **提交**：`src/`、`tests/`、`scripts/`、文档、`pyproject.toml`、`uv.lock`、`.python-version`、启动脚本、共享 `.vscode/` 配置和 CI 配置。
- **不提交**：`.venv/`、`build/`、`dist/`、`artifacts/`、缓存、日志、覆盖率数据、个人 IDE 状态、`.env` 和密钥。
- **可执行文件交付**：使用 CI 的构建附件；正式版本可发布到 GitHub Releases。不要把 `.exe`、打包依赖目录或生成截图放进源码提交。
