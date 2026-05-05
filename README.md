# Game 67 — CS 32 Final Project

**Game 67** is an interactive card game: you pick a number between 1–200, get a hand sized from that pick, and try to build a single arithmetic expression using **each card’s value exactly once** with `+`, `-`, `*`, and `/` so that it equals the **target** defined in `constants.py` (default **24**).

## How to play

- **Pick (1–200)** sets hand size: 1–67 → 4 cards, 68–134 → 5 cards, 135–200 → 6 cards.
- **Operators:** `+`, `-`, `*` (or `x` / `×` in input), `/`.
- **Scoring:** Each valid solution that hits the target earns one point; a new hand is dealt automatically.

## Requirements

- **Python 3.7+**
- **Standard library only** for the Python server and game logic (`http.server`, `json`, `threading`, etc.).
- **Browser UI:** The page loads **Google Fonts** from the network for typography. If you are offline, the game still works; only the custom fonts may fall back to system fonts.

---

## Run the game (what you normally use)

Working directory: this folder (the one containing `deck.py`, `constants.py`, and `backend.py`).

### Browser (recommended)

```bash
python3 run_browser_game.py
```

Optional:

```bash
python3 run_browser_game.py --port 9000
python3 run_browser_game.py --no-browser
```

Same behavior as:

```bash
python3 -m backend
```

### Terminal only

```bash
python3 run_terminal_game.py
```

---

### Stop the browser server

Press **Ctrl+C** in the terminal.

### How it fits together

- **`backend.py`** — server, JSON `/api/*` routes, session state, terminal `run()`, and embedded browser HTML/JS (the “logic + protocol” layer).
- **`deck.py`, `solver.py`, `constants.py`, `validator.py`** — unchanged game rules/data/solver plumbing the backend imports.

---

## Project layout

```
├── run_terminal_game.py     # Thin launcher → imports `backend.run`
├── run_browser_game.py       # Thin launcher → imports `backend.run_browser`
├── backend.py               # Session + HTTP + terminal loop + embedded UI
├── deck.py
├── solver.py
├── constants.py
├── validator.py
└── README.md
```

---

## AI-assisted vs human-authored (summary)

- **Assisted / generated elements:** Solver mathematics, validation constraints, and similar low-level pieces; browser layout and styling helpers.
- **Human steering:** Game rules, flow, and how the terminal and browser experiences are wired together.

If you use Claude or similar tools, document your own process in your course submission as required.
