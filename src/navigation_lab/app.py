import argparse
import json
from pathlib import Path

from navigation_lab.simulation.scenario import Simulation, SimulationConfig


def positive_float(value: str) -> float:
    parsed = float(value)
    if not 0 < parsed < float("inf"):
        raise argparse.ArgumentTypeError("must be a positive finite number")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="15x15 Navigation Lab / 导航模拟器")
    parser.add_argument("--seed", type=int, default=7, help="reproducible random seed")
    parser.add_argument(
        "--headless", action="store_true", help="run core simulation without pygame"
    )
    parser.add_argument("--no-obstacles", action="store_true", help="disable automatic obstacles")
    parser.add_argument("--no-demo-jam", action="store_true", help="disable automatic motor fault")
    parser.add_argument(
        "--max-seconds", type=positive_float, default=60.0, help="headless time budget"
    )
    parser.add_argument("--report", type=Path, help="write final simulation report as JSON")
    parser.add_argument("--frames", type=positive_int, help="GUI smoke test: exit after N frames")
    parser.add_argument("--screenshot", type=Path, help="save GUI screenshot at exit")
    args = parser.parse_args(argv)
    config = SimulationConfig(
        seed=args.seed,
        auto_obstacles=not args.no_obstacles,
        demo_jam=not args.no_demo_jam,
    )
    simulation = Simulation(config)
    if args.headless:
        if args.frames or args.screenshot:
            parser.error("--frames and --screenshot require GUI mode")
        while simulation.time < args.max_seconds and not simulation.arrived:
            simulation.tick(min(Simulation.FIXED_DT, args.max_seconds - simulation.time))
        result = 0 if simulation.arrived else 1
    else:
        # Deliberately lazy: tests, servers and future renderers do not need pygame imported.
        from navigation_lab.presentation.pygame_app import PygameApp

        app = PygameApp(simulation)
        app.run(frames=args.frames, screenshot=args.screenshot)
        simulation = app.simulation
        result = 0
    report = json.dumps(simulation.report(), ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report + "\n", encoding="utf-8")
    if args.headless:
        print(report)
    return result
