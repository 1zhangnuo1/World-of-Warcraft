from pathlib import Path

import pygame

from navigation_lab.core.controller import NavigationState
from navigation_lab.core.geometry import Vec3
from navigation_lab.simulation.scenario import Simulation

BG = (12, 18, 28)
PANEL = (20, 29, 42)
GRID = (30, 42, 56)
TEXT = (231, 237, 243)
MUTED = (135, 155, 177)
TEAL = (65, 218, 184)
ORANGE = (250, 171, 88)
RED = (255, 105, 120)
BLUE = (109, 172, 252)


class PygameApp:
    WIDTH, HEIGHT = 1120, 840
    CELL, MAP_X, MAP_Y = 40, 48, 138

    def __init__(self, simulation: Simulation) -> None:
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Navigation Lab | 2D 导航模拟器")
        self.simulation = simulation
        self.running = True
        self.font_path = pygame.font.match_font(
            "microsoftyahei,notosanscjksc,wenquanyimicrohei,simhei"
        )
        self.chinese = self.font_path is not None
        self.fonts = {
            size: pygame.font.Font(self.font_path, size) for size in (12, 14, 16, 18, 22, 30)
        }
        self.buttons = {
            "pause": pygame.Rect(696, 691, 182, 39),
            "reset": pygame.Rect(890, 691, 182, 39),
            "obstacle": pygame.Rect(696, 741, 182, 39),
            "jam": pygame.Rect(890, 741, 182, 39),
        }

    def tr(self, zh: str, en: str) -> str:
        return zh if self.chinese else en

    def text(
        self, message: str, x: int, y: int, size: int = 16, color: tuple[int, int, int] = TEXT
    ) -> None:
        self.screen.blit(self.fonts[size].render(message, True, color), (x, y))

    def screen_point(self, position: Vec3) -> tuple[int, int]:
        return (
            round(self.MAP_X + (position.x + 0.5) * self.CELL),
            round(self.MAP_Y + (position.y + 0.5) * self.CELL),
        )

    def action(self, name: str) -> None:
        if name == "pause":
            self.simulation.paused = not self.simulation.paused
        elif name == "reset":
            self.simulation = Simulation(self.simulation.config)
        elif name == "obstacle":
            self.simulation.spawn_obstacle()
        elif name == "jam":
            self.simulation.inject_jam()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            actions = {
                pygame.K_SPACE: "pause",
                pygame.K_r: "reset",
                pygame.K_o: "obstacle",
                pygame.K_j: "jam",
            }
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key in actions:
                self.action(actions[event.key])
            elif event.key == pygame.K_d:
                self.simulation.auto_obstacles = not self.simulation.auto_obstacles
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for action, rect in self.buttons.items():
                    if rect.collidepoint(event.pos):
                        self.action(action)
                        return
            x = (event.pos[0] - self.MAP_X) // self.CELL
            y = (event.pos[1] - self.MAP_Y) // self.CELL
            if self.simulation.grid.in_bounds((x, y)):
                if event.button == 1:
                    self.simulation.toggle_obstacle((x, y))
                elif event.button == 3:
                    self.simulation.change_goal((x, y))

    def draw_map(self) -> None:
        sim = self.simulation
        for index in range(15):
            self.text(f"{index:02}", self.MAP_X + index * self.CELL + 11, 114, 12, MUTED)
            self.text(f"{index:02}", 22, self.MAP_Y + index * self.CELL + 12, 12, MUTED)
        for y in range(15):
            for x in range(15):
                cell = (x, y)
                rect = pygame.Rect(self.MAP_X + x * self.CELL, self.MAP_Y + y * self.CELL, 39, 39)
                pygame.draw.rect(self.screen, (22, 33, 47), rect, border_radius=4)
                if cell in sim.grid.walls:
                    pygame.draw.rect(
                        self.screen, (60, 70, 88), rect.inflate(-4, -4), border_radius=4
                    )
                elif cell in sim.grid.obstacles:
                    pygame.draw.rect(
                        self.screen, (99, 65, 37), rect.inflate(-4, -4), border_radius=4
                    )
                    pygame.draw.rect(self.screen, ORANGE, rect.inflate(-4, -4), 2, border_radius=4)
                    pygame.draw.line(
                        self.screen,
                        ORANGE,
                        rect.move(12, 12).topleft,
                        rect.move(-12, -12).bottomright,
                        2,
                    )
        if len(sim.previous_route) > 1:
            pygame.draw.lines(
                self.screen,
                (60, 70, 80),
                False,
                [self.screen_point(p) for p in sim.previous_route],
                2,
            )
        if len(sim.trail) > 1:
            pygame.draw.lines(
                self.screen, (44, 82, 105), False, [self.screen_point(p) for p in sim.trail], 3
            )
        path = [
            self.screen_point(sim.motor.position),
            *[self.screen_point(p) for p in sim.controller.waypoints],
        ]
        if len(path) > 1:
            pygame.draw.lines(self.screen, TEAL, False, path, 3)
            for point in path[1:]:
                pygame.draw.circle(self.screen, TEAL, point, 3)
        start = self.screen_point(sim.backend.center(sim.start))
        goal = self.screen_point(sim.backend.center(sim.goal))
        pygame.draw.circle(self.screen, BLUE, start, 12, 2)
        self.text("S", start[0] - 5, start[1] - 10, 14, BLUE)
        pygame.draw.circle(self.screen, TEAL, goal, 14, 2)
        pygame.draw.circle(self.screen, TEAL, goal, 7, 2)
        agent = self.screen_point(sim.motor.position)
        pygame.draw.circle(self.screen, (70, 38, 54), agent, 17)
        pygame.draw.circle(self.screen, RED, agent, 10)
        pygame.draw.circle(self.screen, (255, 225, 227), agent, 4)
        if sim.motor.blocked:
            pygame.draw.circle(self.screen, ORANGE, agent, 20, 2)

    def draw(self) -> None:
        sim, controller = self.simulation, self.simulation.controller
        self.screen.fill(BG)
        self.text(self.tr("导航实验室", "NAVIGATION LAB"), 46, 26, 30)
        self.text("PHASE 01  /  AUTONOMOUS NAVIGATION", 48, 70, 12, TEAL)
        self.text(f"15 × 15   |   A*   |   SEED {sim.config.seed:02}", 805, 40, 16, MUTED)
        pygame.draw.line(self.screen, GRID, (48, 99), (1072, 99))
        self.draw_map()
        legend = [
            (RED, "Agent"),
            (TEAL, self.tr("当前路线", "Route")),
            (ORANGE, self.tr("动态障碍", "Obstacle")),
            (BLUE, self.tr("起点", "Start")),
        ]
        for i, (color, label) in enumerate(legend):
            pygame.draw.circle(self.screen, color, (57 + i * 151, 763), 5)
            self.text(label, 70 + i * 151, 751, 14, MUTED)
        self.text(
            self.tr(
                "左键：增删障碍    右键：设置目标    D：切换自动障碍",
                "Left: obstacle   Right: goal   D: auto obstacles",
            ),
            48,
            799,
            14,
            MUTED,
        )
        pygame.draw.rect(self.screen, PANEL, (676, 116, 416, 556), border_radius=14)
        states = {
            NavigationState.IDLE: ("待机", "IDLE"),
            NavigationState.MOVING: ("沿路径移动", "MOVING"),
            NavigationState.RECOVERING: ("卡死恢复中", "RECOVERING"),
            NavigationState.WAITING: ("暂无可行路线 · 等待重试", "NO PATH / RETRYING"),
            NavigationState.ARRIVED: ("已实际到达目标", "GOAL REACHED"),
        }
        label = self.tr(*states[controller.state])
        if sim.paused:
            label = self.tr("已暂停 · 模拟时间冻结", "PAUSED")
        self.text(self.tr("任务状态", "MISSION STATUS"), 696, 134, 12, MUTED)
        self.text(label, 696, 158, 22, TEAL if sim.arrived else TEXT)
        position = sim.motor.position
        self.text(f"({position.x:05.2f}, {position.y:05.2f})  →  {sim.goal}", 696, 198, 16, MUTED)
        metrics = [
            (self.tr("运行时间", "TIME"), f"{sim.time:05.1f}s"),
            (self.tr("重新规划", "REPLANS"), f"{controller.replan_count:02}"),
            (self.tr("卡死检测", "STALLS"), f"{controller.stuck_count:02}"),
            (self.tr("实际路程", "DISTANCE"), f"{sim.motor.distance_travelled:.1f}"),
        ]
        for i, (title, value) in enumerate(metrics):
            x, y = 696 + i % 2 * 194, 236 + i // 2 * 70
            self.text(title, x, y, 12, MUTED)
            self.text(value, x, y + 20, 22)
        self.text(self.tr("无有效位移", "NO PROGRESS"), 696, 384, 12, MUTED)
        self.text(
            f"{controller.detector.stalled_for:.2f} / {controller.detector.timeout:.2f}s",
            929,
            384,
            12,
            ORANGE,
        )
        pygame.draw.rect(self.screen, GRID, (696, 414, 376, 6), border_radius=3)
        progress = min(1, controller.detector.stalled_for / controller.detector.timeout)
        if progress > 0:
            pygame.draw.rect(
                self.screen, ORANGE, (696, 414, int(376 * progress), 6), border_radius=3
            )
        automatic = "ON" if sim.auto_obstacles else "OFF"
        self.text(
            self.tr("自动障碍", "AUTO OBSTACLES")
            + f"  {automatic}  ·  {sim.obstacles_created}/{sim.config.obstacle_budget}",
            696,
            436,
            14,
            MUTED,
        )
        self.text(self.tr("事件记录", "EVENT LOG"), 696, 476, 12, MUTED)
        event_names = {
            "plan": "已规划",
            "stuck": "检测到卡死",
            "arrived": "到达目标",
            "invalidated": "原路线失效",
            "no_path": "无路，等待重试",
            "obstacle": "出现障碍",
            "cleared": "障碍已移除",
            "jam": "注入移动故障",
            "released": "移动故障解除",
            "edit": "保护格不可编辑",
        }
        for i, event in enumerate(list(controller.events)[-6:]):
            color = ORANGE if event.kind in ("stuck", "jam", "no_path", "invalidated") else MUTED
            event_label = event_names.get(event.kind, event.kind) if self.chinese else event.kind
            self.text(f"{event.time:05.1f}s   {event_label}", 696, 502 + i * 24, 14, color)
        labels = {
            "pause": self.tr("继续 / 暂停", "Pause / Resume") + "  [SPACE]",
            "reset": self.tr("重新开始", "Restart") + "  [R]",
            "obstacle": self.tr("随机挡路", "Add obstacle") + "  [O]",
            "jam": self.tr("模拟卡死", "Freeze motor") + "  [J]",
        }
        for name, rect in self.buttons.items():
            pygame.draw.rect(self.screen, GRID, rect, border_radius=7)
            self.text(labels[name], rect.x + 10, rect.y + 8, 12)
        self.text(
            self.tr(
                "灰线：上次路线   蓝灰线：实际移动轨迹", "Gray: old route   Blue-gray: actual trail"
            ),
            696,
            799,
            12,
            MUTED,
        )
        pygame.display.flip()

    def run(self, *, frames: int | None = None, screenshot: Path | None = None) -> None:
        clock = pygame.time.Clock()
        accumulator = 0.0
        frame = 0
        try:
            while self.running:
                elapsed = min(clock.tick(60) / 1000.0, 0.25)
                for event in pygame.event.get():
                    self.handle_event(event)
                if self.simulation.paused:
                    accumulator = 0.0
                else:
                    accumulator += elapsed
                    while accumulator >= Simulation.FIXED_DT:
                        self.simulation.tick()
                        accumulator -= Simulation.FIXED_DT
                self.draw()
                frame += 1
                if frames is not None and frame >= frames:
                    break
            if screenshot is not None:
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                pygame.image.save(self.screen, str(screenshot))
        finally:
            pygame.quit()
