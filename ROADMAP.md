# Jarvis roadmap

Goal: a Jarvis that is useful every day, learns skills **bound to you**, proposes ideas (including ways to earn
money), builds some of them itself, and gets better each day, while you stay in control of anything that costs
money, reaches other people, or changes your live setup.

## Where we are (built, tested)
- Daily learning loop: new skill, new dashboard look, lesson, ideas, optional self-build (`jarvis learn --build`)
- Safety: static guard + each new skill must pass its own tests; builds wait for `jarvis approve`
- TV (Samsung, Roku, Android/Fire TV, CEC), Wi-Fi discovery, gesture engine
- Spend tracking + hard budget + dashboard widget (`jarvis budget`)
- Profile of you (`jarvis about`) feeding what it learns and proposes

## Known gaps (honest list)
- Never run against your real TV, webcam, or the live API yet (first runs will find bugs)
- `jarvis learn "<thing>"` (learn on demand) does not exist yet; requests wait for the next daily run
- Offline it only has 4 skills to unlock
- Skills can't call each other, so there are no multi-step routines ("morning scene") yet
- No notifications: Jarvis only speaks when you run it
- No voice

## Next, in order
1. **Make it real on your hardware.** Run on your computer, fix what breaks (Samsung TLS, discovery, gestures).
   Review your existing local Jarvis (see below) and merge what is good.
2. **Learn on demand + the "gap" loop.** `jarvis learn "control my lights"`; Jarvis proposes skills from your
   unmet requests and your profile, not only from a generic list.
3. **Routines.** Skills that chain (morning: briefing, TV news, habits). Triggered by a phrase, a gesture, or time.
4. **Business assistant** (proposes and helps run, you decide):
   - Ideas ranked against your profile: skills, hours, money, goal. Cheap validation steps first.
   - Research & drafting: market notes, offers, landing page copy, outreach drafts, price math.
   - Operations you approve each step of: invoices, expenses (already started: `expense_log`), income tracking,
     weekly review of what is working.
   - Hard rules: Jarvis never spends money, sends messages to other people, publishes, or signs up for things
     without an explicit yes each time. No legal/tax advice presented as certain.
5. **Multiple agents.** Only where reasoning is needed (planner, researcher, builder, reviewer). Plain code does
   the doing. One shared budget, cheap model for routing, stronger one for writing code.
6. **Visual and ambient.** Dashboard on the TV, notifications, better gesture feedback.

## How "bound to you" works
`jarvis about` stores your profile locally. It is included (briefly) in the prompts for new skills and ideas, so
Jarvis builds for your life instead of a generic user. Anything you don't want sent to the API, leave out.

## Rules we keep
- Spending is capped by `jarvis budget`; Jarvis refuses calls that could exceed it.
- New code from Jarvis arrives with tests and as a reviewable change; big builds need `jarvis approve`.
- Nothing outward-facing (money, messages, publishing) without your explicit approval.
