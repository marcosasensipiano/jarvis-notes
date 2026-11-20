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

### Give Jarvis its brain (API key)
Get a key at console.anthropic.com. **Never paste it into a chat or commit it.**
- *Your computer:* add `export ANTHROPIC_API_KEY=...` to `~/.zshrc`/`~/.bashrc` (and to the crontab line if you use cron).
- *GitHub daily job:* repo Settings > Secrets and variables > Actions > New repository secret, name
  `ANTHROPIC_API_KEY`, or run `gh secret set ANTHROPIC_API_KEY` (it prompts without echoing).
- Check with `jarvis status` (should say `Brain: online`). Model defaults to `claude-sonnet-5-5`; override with `JARVIS_MODEL`.

### Budget (never overspend)
```
jarvis budget 5.8        # total credit in USD, as shown in the Anthropic console
jarvis budget            # spent / left; the dashboard has a Brain budget widget
jarvis budget add 3      # after you top up
```
The API doesn't tell Jarvis your remaining credit, so Jarvis tracks its own spend (tokens x published prices).
It is an estimate: the console is the source of truth. With a budget set, Jarvis refuses any call whose worst case
could exceed what is left and falls back to its offline library.

### Make it about you
`jarvis about` asks a few questions (skills, free time, goals, money, annoyances) and stores them in
`data/profile.json` on your machine. A short summary goes into the prompts for new skills and ideas.

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
| Samsung Tizen (QLED etc., 2016+) | supported (`samsung`), see setup below |
| Roku (TV or stick) | supported (`roku`) |
| Android TV / Google TV / Fire TV / Shield | supported (`adb`, enable network debugging) |
| Any HDMI-CEC TV via a Pi | power only (`cec`) |
| LG (webOS) | **not built yet**; it's on the learning backlog, so ask Jarvis for it |

### Samsung QLED setup
1. TV and the computer running Jarvis on the same Wi-Fi/network. Run `jarvis discover` to see the TV's IP
   (or TV: Settings > General > Network > Network Status > IP Settings).
2. `cp config/devices.example.json config/devices.json`, set `"type": "samsung"` and `"host"`.
3. Run `jarvis tv volume up`. **The TV shows an "Allow Jarvis?" prompt: pick Allow** and run it again. The pairing
   token is saved in `data/samsung_token.json`, so it asks only once. If you never see the prompt, check
   Settings > General > External Device Manager > Device Connection Manager > Access Notification.
4. Optional, for `tv on` from standby: put the TV's MAC in `"mac"` (shown by `jarvis discover`) and enable
   Settings > General > Network > Expert Settings > Power On with Mobile. This uses Wake-on-LAN, which is
   model-dependent and works best when the TV is on Ethernet; on Wi-Fi it may not wake. Turning *off* always works.
5. `play/pause`: Samsung has separate Play and Pause keys, so Jarvis alternates them and can drift out of sync
   if you also use the physical remote.

Gestures (edit `config/gestures.json` to remap): hold open palm = play/pause, fist = mute, peace = home,
thumbs up/down = volume (repeats while held), swipe an open palm up/down/left/right = volume / rewind / forward.
Poses must be held still ~0.8s and have a 1.5s cooldown, and swipes only count with an open palm, so
waving at a friend doesn't change the channel. Power is deliberately **not** mapped to a gesture.

"Connect to Wi-Fi" is implemented as *awareness*: Jarvis reads your network name and finds devices on it. It
doesn't join networks or probe devices you don't own.

See `ROADMAP.md` for where this is going.

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
TV request formats (the Samsung driver is tested against a fake TV speaking real WebSocket framing), network parsing, brain pipeline (with the model mocked). **Not tested against real hardware or
the live Claude API**: the TV drivers on an actual TV (including the Samsung TLS connection, which the fake server skips), webcam/MediaPipe capture, SSDP on your network.
