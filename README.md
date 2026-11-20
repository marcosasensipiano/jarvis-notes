# Jarvis

A personal assistant that **learns one new skill every day**, upgrades its own look, teaches you how to use
what it learned, proposes things to build, and builds some of them itself. It controls your TV, sees what
is on your Wi-Fi, and responds to hand gestures.

Pure Python 3.10+, no dependencies (the webcam feature needs two optional ones).

```
python -m jarvis note buy oat milk
python -m jarvis timer 25m tea
python -m jarvis learn            # today's lesson
python -m jarvis today            # read it
```
(`pip install -e .` gives you a plain `jarvis` command.)

## How it learns

Each `jarvis learn` run:

1. **Picks a skill.** Priority: the thing you keep asking for that it couldn't do (every unmatched request is
   remembered as a *gap*), otherwise its own idea of what would help you most.
   - **With `ANTHROPIC_API_KEY`:** Claude writes a brand-new skill *and its tests*. Jarvis only installs it if it
     passes a static safety guard and its own tests in an isolated interpreter. Failures are retried once with the
     error, then logged; it never installs something that doesn't pass.
   - **Without a key:** it unlocks the next skill from `library/` (4 ship today). When that runs out it tells you,
     rather than pretending.
2. **Upgrades its graphics.** One visual upgrade per day on the dashboard (`dashboard/index.html`): glow, scanlines,
   rotating arc reactor, holographic grid, skill constellation, pulsing status light. After those, Claude designs
   new CSS-only ones itself.
3. **Teaches you.** `lessons/day-NNN-date.md` explains the new skill, gives commands to try, and explains the
   visual change. `jarvis teach <skill>` replays any lesson.
4. **Thinks of builds.** `jarvis ideas` lists ideas, personalised by what you use and what you were refused.
5. **Builds on its own.** `jarvis learn --build` implements one small idea in `builds/<name>/` with tests.
   Nothing goes live until you run `jarvis approve <name>`.

### Run it daily
- **On your computer:** `jarvis schedule` prints a cron line.
- **On GitHub:** `.github/workflows/daily-learning.yml` runs every morning and opens a pull request with the day's
  learning. Add the repo secret `ANTHROPIC_API_KEY` to let it invent skills. You review, merge, pull.

## TV, Wi-Fi, gestures

```
jarvis discover                        # who is on your Wi-Fi, and which look like TVs
cp config/devices.example.json config/devices.json   # then edit type + host
jarvis tv volume up                    # or: tv pause, tv home, tv off ...
jarvis gestures --dry-run              # try gestures without sending anything
jarvis gestures                        # live (pip install opencv-python mediapipe)
```

| TV | Status |
|---|---|
| Roku (TV or stick) | supported (`roku`) |
| Android TV / Google TV / Fire TV / Shield | supported (`adb`, enable network debugging) |
| Any HDMI-CEC TV via a Pi | power only (`cec`) |
| Samsung (Tizen), LG (webOS) | **not built yet.** They need websocket pairing; it's on the learning backlog, so ask Jarvis for it |

Gestures (edit `config/gestures.json` to remap): hold open palm = play/pause, fist = mute, peace = home,
thumbs up/down = volume (repeats while held), swipe an open palm up/down/left/right = volume / rewind / forward.
Poses must be held still ~0.8s and have a 1.5s cooldown, and swipes only count with an open palm, so
waving at a friend doesn't change the channel. Power is deliberately **not** mapped to a gesture.

"Connect to Wi-Fi" is implemented as *awareness*: Jarvis reads your network name and finds devices on it. It
doesn't join networks or probe devices you don't own.

## Writing / reviewing skills
A skill is a folder `skills/<name>/` with `skill.py` (NAME, DESCRIPTION, TRIGGERS, EXAMPLES, LESSON, `run(args, ctx)`)
and `test_skill.py`. `python -m unittest discover -s tests -t .` runs everything, including every shipped skill's tests.

## Safety
- `jarvis/guard.py` rejects generated code that imports `os`, `subprocess`, `socket`, `urllib`... or calls
  `eval`/`exec`. It is a guardrail, **not a sandbox**; the real gate is that learned skills arrive as a PR you review.
- Memory (`data/memory.json`) stores counters and short unmet-request phrases, not transcripts. It is committed
  so the daily job can learn from your usage, so keep this repo private. Your notes/habits/expenses (`data/*` other
  than `memory.json`) are git-ignored.

## Status
Tested: skills, routing, learning loop, safety guard, gesture classification/engine (on synthetic landmarks),
TV request formats, network parsing, brain pipeline (with the model mocked). **Not tested against real hardware or
the live Claude API**: the TV drivers on an actual TV, webcam/MediaPipe capture, SSDP on your network.
