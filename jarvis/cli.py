import argparse
import sys
from datetime import datetime
from . import brain, builder, dashboard, learner, memory, paths, skills

BUILTINS = {"learn", "today", "skills", "teach", "ideas", "build", "approve", "dashboard", "discover",
            "gestures", "schedule", "status", "run", "help"}


def _run_text(text: str) -> int:
    reg = skills.discover()
    skill, args = skills.route(text, reg)
    if skill is None:
        memory.record_gap(text)
        print("I can't do that yet. I've noted it, and it will be first in line for what I learn next.")
        return 1
    memory.record_use(skill.NAME)
    try:
        print(skill.run(args, skills.Ctx()))
    except Exception as e:
        print(f"{skill.NAME} failed: {e}")
        return 2
    return 0


def cmd_learn(a):
    learner.learn_today(force=a.force, build=a.build)


def cmd_today(a):
    files = sorted(paths.lessons_dir().glob("*.md"))
    print(files[-1].read_text() if files else "No lessons yet. Run: jarvis learn")


def cmd_skills(a):
    errors = {}
    reg = skills.discover(errors=errors)
    m = memory.load()
    for n, s in sorted(reg.items()):
        print(f"{n:16} {s.DESCRIPTION}  (used {m['usage'].get(n, 0)}x)")
    for n, e in errors.items():
        print(f"{n:16} BROKEN: {e}")


def cmd_teach(a):
    reg = skills.discover()
    s = reg.get(a.skill)
    if not s:
        print(f"No skill '{a.skill}'. Known: {', '.join(sorted(reg))}")
        return 1
    print(s.LESSON.strip(), "\n\nTry:", *[f"\n  jarvis {e}" for e in s.EXAMPLES])


def cmd_ideas(a):
    m = memory.load()
    for i in m["ideas"] or []:
        print(f"#{i['id']:<3} [{i['effort']}] {i['status']:9} {i['title']} - {i['why']}")
    if not m["ideas"]:
        print("No ideas yet. Run: jarvis learn")


def cmd_build(a):
    m = memory.load()
    idea = next((i for i in m["ideas"] if i["id"] == a.id), None)
    if not idea:
        print("No such idea id.")
        return 1
    print(builder.build(m, idea))
    memory.save(m)


def cmd_approve(a):
    m = memory.load()
    print(builder.approve(m, a.name))
    memory.save(m)


def cmd_dashboard(a):
    f = dashboard.write(memory.load())
    print(f"Wrote {f}")
    if a.open:
        import webbrowser
        webbrowser.open(f.as_uri())


def cmd_discover(a):
    from .devices import network
    print("Network:", network.wifi_status())
    print("Scanning for smart devices (SSDP)...")
    found = network.ssdp_discover(a.timeout)
    for ip, d in sorted(found.items()):
        print(f"  {ip:15} {d['kind']:12} {d['server'][:60]}")
    if not found:
        print("  none answered. Make sure this computer is on the same Wi-Fi as the TV.")
    print("Other devices on this network:")
    for ip, mac in network.neighbors().items():
        print(f"  {ip:15} {mac}")


def cmd_gestures(a):
    from .gestures import runtime
    return runtime.run(camera=a.camera, dry_run=a.dry_run)


def cmd_schedule(a):
    py = sys.executable
    root = paths.root()
    print(f"""Run the learning loop every morning at 07:00.

cron (add with `crontab -e`):
  0 7 * * * cd {root} && {py} -m jarvis learn >> data/learn.log 2>&1

With an API key, Jarvis invents new skills and builds ideas; export ANTHROPIC_API_KEY in that crontab
or use the GitHub Action in .github/workflows/daily-learning.yml, which opens a PR you review.""")


def cmd_status(a):
    m = memory.load()
    reg = skills.discover()
    from .devices import tv
    print(f"Day {m['day']} | {len(reg)} skills | {len(m['upgrades'])} visual upgrades | {len(m['ideas'])} ideas")
    print("Brain:", "online (Claude API)" if brain.available() else "offline (built-in library only)")
    print("TV:", tv.describe_config())
    print("Unmet requests:", dict(sorted(m["gaps"].items(), key=lambda kv: -kv[1])[:5]) or "none")


def build_parser():
    p = argparse.ArgumentParser(prog="jarvis", description="Jarvis learns a new skill every day. "
                                "Anything that is not a command below is treated as a request, e.g. `jarvis note buy milk`.")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("learn", help="learn today's skill, look and ideas")
    s.add_argument("--force", action="store_true")
    s.add_argument("--build", action="store_true", help="also implement one small idea in builds/")
    s.set_defaults(fn=cmd_learn)
    sub.add_parser("today", help="show the latest lesson").set_defaults(fn=cmd_today)
    sub.add_parser("skills", help="list skills").set_defaults(fn=cmd_skills)
    s = sub.add_parser("teach", help="teach me a skill"); s.add_argument("skill"); s.set_defaults(fn=cmd_teach)
    sub.add_parser("ideas", help="list build ideas").set_defaults(fn=cmd_ideas)
    s = sub.add_parser("build", help="have Jarvis build an idea"); s.add_argument("id", type=int); s.set_defaults(fn=cmd_build)
    s = sub.add_parser("approve", help="install a finished build"); s.add_argument("name"); s.set_defaults(fn=cmd_approve)
    s = sub.add_parser("dashboard", help="regenerate the dashboard"); s.add_argument("--open", action="store_true"); s.set_defaults(fn=cmd_dashboard)
    s = sub.add_parser("discover", help="find your TV and devices on the Wi-Fi"); s.add_argument("--timeout", type=float, default=3.0); s.set_defaults(fn=cmd_discover)
    s = sub.add_parser("gestures", help="control the TV by hand gestures (webcam)")
    s.add_argument("--camera", type=int, default=0); s.add_argument("--dry-run", action="store_true", help="show what would happen, send nothing")
    s.set_defaults(fn=cmd_gestures)
    sub.add_parser("schedule", help="how to run learning daily").set_defaults(fn=cmd_schedule)
    sub.add_parser("status", help="overview").set_defaults(fn=cmd_status)
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        build_parser().print_help()
        return 0
    if argv[0] == "run":
        return _run_text(" ".join(argv[1:]))
    if argv[0] not in BUILTINS and not argv[0].startswith("-"):
        return _run_text(" ".join(argv))
    a = build_parser().parse_args(argv)
    if not getattr(a, "fn", None):
        build_parser().print_help()
        return 0
    return a.fn(a) or 0
