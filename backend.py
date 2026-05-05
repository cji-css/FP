"""
Backend only: shared game/session state, `/api/*` HTTP handlers, embedded browser UI markup,
and the terminal play loop helpers.

Pair with `run_browser_game.py` or `run_terminal_game.py` at the repo root (`deck`, `solver`,
`constants`, `validator` stay as sibling modules).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _load_validator():
    candidate = _PROJECT_ROOT / "validator.py"
    if candidate.is_file():
        spec = importlib.util.spec_from_file_location("_g67_validator", candidate)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    raise ImportError("No validator.py found in project root.")


_v = _load_validator()
validate_expression = _v.validate_expression

from deck import build_deck, hand_size_from_pick
from solver import solve_all_expressions

from constants import SUIT_SYMBOLS, TARGET


_state_lock = threading.Lock()
_state = {
    "hand": [],
    "pick": None,
    "score": 0,
    "hints": [],
}


def _hand_values():
    return [c["value"] for c in _state["hand"]]


def _deal(pick):
    deck = build_deck()
    n = hand_size_from_pick(pick)
    _state["pick"] = pick
    _state["hand"] = [deck.pop() for _ in range(n)]
    _state["hints"] = []


def api_new_pick(pick: int):
    if not isinstance(pick, int) or pick < 1 or pick > 200:
        raise ValueError("Pick must be an integer between 1 and 200.")
    with _state_lock:
        _deal(pick)
        vals = _hand_values()
        hand_copy = list(_state["hand"])
        score = _state["score"]
    return {
        "ok": True,
        "pick": pick,
        "hand": hand_copy,
        "target": TARGET,
        "score": score,
        "hand_values": vals,
        "hints_count": len(solve_all_expressions(vals, target=TARGET, limit=300)),
    }


def api_guess(expression: str):
    with _state_lock:
        if not _state["hand"]:
            raise RuntimeError("Start a round first.")
        vals = list(_hand_values())
        pick = _state["pick"]
        ok, msg, val = validate_expression(expression, vals)
        solved = bool(ok and val is not None and float(val) == float(TARGET))
        if solved:
            _state["score"] += 1
            _deal(pick)
            new_hand = list(_state["hand"])
            score = _state["score"]
        else:
            new_hand = list(_state["hand"])
            score = _state["score"]

    new_vals = [c["value"] for c in new_hand]
    hints_ct = len(solve_all_expressions(new_vals, target=TARGET, limit=300))
    return {
        "expr_ok": ok,
        "details": None if ok else msg,
        "result": float(val) if ok and val is not None else None,
        "hit_target": bool(ok and val is not None and float(val) == float(TARGET)),
        "solved": solved,
        "scored": 1 if solved else 0,
        "score": score,
        "hand": new_hand,
        "hints_count": hints_ct,
    }


def api_hints():
    with _state_lock:
        if not _state["hand"]:
            raise RuntimeError("Start a round first.")
        vals = _hand_values()
    exprs = solve_all_expressions(vals, target=TARGET, limit=12)
    with _state_lock:
        _state["hints"] = exprs
    return exprs


def _html_page() -> str:
    """Build HTML with server-side constants."""
    sym_json = json.dumps({k: SUIT_SYMBOLS[k] for k in SUIT_SYMBOLS}, ensure_ascii=False)
    target_js = str(int(TARGET)) if float(TARGET).is_integer() else str(float(TARGET))
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Game 67</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=DM+Sans:ital,wght@0,400;0,600;1,400&display=swap');
    :root {
      --bg0: #0a0614;
      --bg1: #1a1030;
      --glass: rgba(255,255,255,.06);
      --stroke: rgba(255,255,255,.14);
      --accent: #2ee6d6;
      --accent2: #ff3d9a;
      --gold: #f4d03f;
      --text: #eef6ff;
      --muted: #9aa8c8;
      --danger: #ff5c5c;
      --radius: 18px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      font-family: 'DM Sans', system-ui, sans-serif;
      color: var(--text);
      overflow-x: hidden;
      background: radial-gradient(ellipse 120% 80% at 50% -20%, #3d1f6e 0%, transparent 55%),
                  radial-gradient(ellipse 70% 50% at 100% 100%, rgba(255,61,154,.28), transparent),
                  radial-gradient(ellipse 60% 40% at 0% 80%, rgba(46,230,214,.22), transparent),
                  linear-gradient(165deg, var(--bg0), var(--bg1));
    }
    .grid-bg {
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: radial-gradient(ellipse 90% 70% at 50% 45%, black, transparent);
      pointer-events: none;
      z-index: 0;
    }
    .orb {
      position: fixed;
      border-radius: 50%;
      filter: blur(80px);
      opacity: .45;
      pointer-events: none;
      z-index: 0;
      animation: float 18s ease-in-out infinite alternate;
    }
    .orb.o1 { width: 340px; height: 340px; background: var(--accent2); left: -8%; top: 10%; animation-delay: -3s;}
    .orb.o2 { width: 380px; height: 380px; background: #6c5ce7; right: -10%; top: 38%; animation-delay: -8s;}
    .orb.o3 { width: 280px; height: 280px; background: var(--accent); left: 35%; bottom: -5%; animation-delay: -12s;}
    @keyframes float { from { transform: translate(0,0) scale(1);} to { transform: translate(28px,-22px) scale(1.05);}}

    header {
      position: relative;
      z-index: 2;
      text-align: center;
      padding: 28px 16px 8px;
    }
    header h1 {
      font-family: 'Orbitron', sans-serif;
      font-weight: 900;
      font-size: clamp(2rem, 6vw, 3rem);
      letter-spacing: .12em;
      text-transform: uppercase;
      background: linear-gradient(135deg, var(--accent), var(--gold));
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      text-shadow: 0 0 40px rgba(46,230,214,.35);
      animation: titlePulse 4s ease-in-out infinite alternate;
    }
    @keyframes titlePulse { from { filter: brightness(1);} to { filter: brightness(1.25); }}

    main {
      position: relative;
      z-index: 2;
      max-width: 920px;
      margin: 0 auto;
      padding: 12px 18px 48px;
    }

    .panel {
      background: var(--glass);
      border: 1px solid var(--stroke);
      border-radius: var(--radius);
      backdrop-filter: blur(14px);
      box-shadow: 0 20px 50px rgba(0,0,0,.45),
                  inset 0 1px 0 rgba(255,255,255,.08);
    }

    .hud {
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 12px;
      padding: 18px 22px;
      margin-bottom: 18px;
    }
    .target-wrap {
      text-align: center;
    }
    .target-wrap .lbl { font-size: .78rem; color: var(--muted); letter-spacing: .2em; text-transform: uppercase;}
    .target-num {
      font-family: 'Orbitron', monospace;
      font-size: clamp(3rem, 12vw, 4.2rem);
      font-weight: 900;
      line-height: 1;
      background: linear-gradient(#fff 10%, var(--accent) 100%);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      animation: targetGlow 2.2s ease-in-out infinite alternate;
    }
    @keyframes targetGlow {
      from { filter: drop-shadow(0 0 8px rgba(46,230,214,.4));}
      to { filter: drop-shadow(0 0 26px rgba(244,208,63,.65));}
    }
    .score-chip {
      justify-self: end;
      padding: 8px 16px;
      border-radius: 999px;
      border: 1px solid rgba(244,208,63,.35);
      background: rgba(244,208,63,.09);
      font-family: 'Orbitron', sans-serif;
      font-size: .9rem;
      color: var(--gold);
    }
    .pick-badge {
      justify-self: start;
      font-size: .85rem;
      color: var(--muted);
    }
    .pick-badge strong { color: var(--accent); }

    .lobby {
      padding: 28px 26px;
      text-align: center;
    }
    .lobby p { color: var(--muted); margin-bottom: 20px; line-height: 1.55; font-size: 1rem; }
    .pick-row {
      display: flex; flex-wrap: wrap; gap: 12px; justify-content: center;
      align-items: center;
    }
    input[type="number"] {
      width: 120px;
      padding: 12px 14px;
      font-size: 1.05rem;
      border-radius: 12px;
      border: 1px solid var(--stroke);
      background: rgba(0,0,0,.35);
      color: var(--text);
      outline: none;
      font-family: 'Orbitron', monospace;
    }
    input[type="number"]:focus {
      border-color: var(--accent);
      box-shadow: 0 0 16px rgba(46,230,214,.35);
    }
    button {
      cursor: pointer;
      font-family: 'Orbitron', sans-serif;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
      border: none;
      border-radius: 12px;
      padding: 12px 22px;
      font-size: .82rem;
      transition: transform .15s, box-shadow .15s;
    }
    button:active { transform: scale(.96);}
    .btn-primary {
      background: linear-gradient(135deg, var(--accent), #1aa89a);
      color: #031210;
      box-shadow: 0 8px 28px rgba(46,230,214,.38);
    }
    .btn-primary:hover {
      box-shadow: 0 12px 36px rgba(46,230,214,.52);
    }
    .btn-ghost {
      background: transparent;
      color: var(--muted);
      border: 1px solid var(--stroke);
    }
    .btn-ghost:hover { color: var(--text); border-color: rgba(255,255,255,.28); }

    .play-area { padding: 22px 20px 28px; }
    .cards {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      justify-content: center;
      min-height: 140px;
      margin-bottom: 22px;
      perspective: 900px;
    }
    .card {
      width: 88px;
      height: 124px;
      border-radius: 12px;
      position: relative;
      transform-style: preserve-3d;
      animation: dealIn .55s cubic-bezier(.2,.9,.2,1) backwards;
      box-shadow:
        0 12px 28px rgba(0,0,0,.55),
        0 0 0 1px rgba(255,255,255,.1) inset,
        0 -3px 20px rgba(255,255,255,.06) inset;
    }
    @keyframes dealIn {
      from { opacity: 0; transform: translateY(40px) rotateX(-18deg) scale(.85);}
      to { opacity: 1; transform: translateY(0) rotateX(0) scale(1);}
    }
    .card-inner {
      border-radius: 12px;
      width: 100%; height: 100%;
      background: linear-gradient(145deg, #fefefe 8%, #e8eaf0 92%);
      color: #1a1423;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-family: 'Orbitron', sans-serif;
      transition: transform .25s ease, box-shadow .25s ease;
    }
    .card:hover .card-inner {
      transform: translateY(-6px) rotateY(6deg) scale(1.03);
      box-shadow: 0 20px 40px rgba(46,230,214,.25);
    }
    .card.red .card-inner { color: #c81e3c; }
    .card .corner {
      font-size: .82rem;
      font-weight: 800;
      line-height: 1;
      text-align: center;
    }
    .card .val { font-size: 1.6rem; font-weight: 900; margin: 6px 0; }
    .card .su { font-size: 1.45rem;}

    .expr-row {
      display: flex; flex-wrap: wrap; gap: 10px; align-items: stretch;
      margin-bottom: 14px;
    }
    #expr {
      flex: 1;
      min-width: 180px;
      padding: 14px 16px;
      border-radius: 12px;
      border: 1px solid var(--stroke);
      background: rgba(0,0,0,.42);
      color: var(--text);
      font-size: 1.05rem;
      font-family: ui-monospace, monospace;
      outline: none;
    }
    #expr:focus {
      border-color: var(--accent2);
      box-shadow: 0 0 20px rgba(255,61,154,.28);
    }
    .toast {
      min-height: 28px;
      font-size: .95rem;
      margin-bottom: 12px;
      padding: 8px 12px;
      border-radius: 10px;
      transition: opacity .2s;
    }
    .toast.err { background: rgba(255,92,92,.14); border: 1px solid rgba(255,92,92,.35); color: #ffb4b4; }
    .toast.ok { background: rgba(46,230,214,.14); border: 1px solid rgba(46,230,214,.35); color: #bffaf3; }

    #hintBox {
      font-size: .85rem;
      color: var(--muted);
      max-height: 120px;
      overflow-y: auto;
      padding: 10px;
      border-radius: 10px;
      border: 1px dashed rgba(255,255,255,.14);
      background: rgba(0,0,0,.22);
      font-family: ui-monospace, monospace;
      margin-top: 10px;
    }

    canvas#fx {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 99;
    }

    .shake { animation: shake .42s ease; }
    @keyframes shake {
      0%,100% { transform: translateX(0);}
      20% { transform: translateX(-8px);}
      40% { transform: translateX(8px);}
      60% { transform: translateX(-5px);}
      80% { transform: translateX(5px);}
    }

    footer {
      position: relative;
      z-index: 2;
      text-align: center;
      padding: 16px;
      font-size: .78rem;
      color: rgba(154,168,200,.65);
    }
  </style>
</head>
<body>
  <div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
  <div class="grid-bg"></div>
  <canvas id="fx"></canvas>

  <header>
    <h1>Game 67</h1>
  </header>

  <main>
    <div class="panel hud">
      <div class="pick-badge">Your pick <strong id="pickShow">—</strong></div>
      <div class="target-wrap">
        <div class="lbl">Target</div>
        <div class="target-num" id="targetShow">__TARGET_HTML__</div>
      </div>
      <div class="score-chip">Score <span id="scoreShow">0</span></div>
    </div>

    <section class="panel lobby" id="lobby">
      <p>Pick a number from <strong style="color:var(--gold)">1–200</strong>. It sizes your hand: 4, 5, or 6 cards. Build one expression using <strong style="color:var(--accent)">each value once</strong> with + − × ÷ to hit the target.</p>
      <div class="pick-row">
        <input id="pickInput" type="number" min="1" max="200" placeholder="Pick" />
        <button class="btn-primary" id="dealBtn">Deal hand</button>
      </div>
    </section>

    <section class="panel play-area" id="play" style="display:none;">
      <div class="cards" id="cards"></div>
      <div class="toast" id="toast" style="display:none;"></div>
      <div class="expr-row">
        <input id="expr" type="text" autocomplete="off" placeholder="Example: (1+2)*(3+4)+5 …" spellcheck="false"/>
        <button class="btn-primary" id="submitBtn">Submit</button>
        <button class="btn-ghost" id="hintBtn">Peek hints</button>
      </div>
      <div id="hintBox" style="display:none;"></div>
    </section>
  </main>

  <footer>Use each card exactly once • Local Python server — not hosted online</footer>

<script>
(() => {
  const $ = (s) => document.querySelector(s);
  const TARGET_GOAL = __TARGET_JS__;
  const SYM = __SYM_JSON__;
  const lobby = $('#lobby');
  const play = $('#play');
  const toast = $('#toast');
  let celebrating = false;

  function flash(msg, ok) {
    toast.textContent = msg;
    toast.className = 'toast ' + (ok ? 'ok' : 'err');
    toast.style.display = 'block';
  }

  function suitClass(suit) {
    return (suit === 'Hearts' || suit === 'Diamonds') ? 'red' : '';
  }

  async function api(path, body) {
    const r = await fetch(path, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body || {})
    });
    const txt = await r.text();
    let data;
    try { data = JSON.parse(txt); }
    catch (_) { throw new Error('Bad server response'); }
    if (!r.ok) throw new Error(data.error || 'Request failed');
    return data;
  }

  function renderCards(hand) {
    const wrap = $('#cards');
    wrap.innerHTML = '';
    hand.forEach((c, i) => {
      const sym = SYM[c.suit] || '\\u2660';
      const el = document.createElement('div');
      el.className = 'card ' + suitClass(c.suit);
      el.style.animationDelay = (i * .08).toFixed(2) + 's';
      el.innerHTML =
        '<div class="card-inner"><div class="corner">' + c.rank + '<br/>' + sym + '</div>' +
        '<div class="val">' + c.value + '</div><div class="su">' + sym + '</div></div>';
      wrap.appendChild(el);
    });
  }

  const canvas = $('#fx');
  const ctx = canvas.getContext('2d');
  function resizeFx() {
    canvas.width = innerWidth;
    canvas.height = innerHeight;
  }
  addEventListener('resize', resizeFx);
  resizeFx();

  let particles = [];
  function burst() {
    const cx = innerWidth / 2, cy = innerHeight * 0.34;
    for (let i = 0; i < 90; i++) {
      particles.push({
        x: cx, y: cy,
        vx: (Math.random() - .5) * 13,
        vy: (Math.random() - .95) * 14,
        life: .9 + Math.random() * .6,
        hue: Math.random() * 80 + 150,
        sz: Math.random() * 5 + 2
      });
    }
    if (!celebrating) {
      celebrating = true;
      requestAnimationFrame(loopFx);
    }
  }
  function loopFx() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles = particles.filter(p => {
      p.vy += 0.35;
      p.x += p.vx; p.y += p.vy;
      p.life -= .016;
      if (p.life <= 0) return false;
      ctx.fillStyle = 'hsla(' + p.hue + ',90%,62%,' + p.life + ')';
      ctx.beginPath(); ctx.arc(p.x, p.y, p.sz, 0, 6.283); ctx.fill();
      return true;
    });
    if (particles.length) requestAnimationFrame(loopFx);
    else celebrating = false;
  }

  $('#dealBtn').onclick = async () => {
    const v = parseInt($('#pickInput').value, 10);
    if (!(v >= 1 && v <= 200)) {
      flash('Enter a whole number between 1 and 200.', false);
      toast.style.display = 'block';
      return;
    }
    try {
      const data = await api('/api/new', { pick: v });
      $('#pickShow').textContent = v;
      $('#scoreShow').textContent = data.score;
      $('#hintBox').style.display = 'none';
      lobby.style.display = 'none';
      play.style.display = 'block';
      renderCards(data.hand);
      flash('Dealt ' + data.hand.length + ' cards • ' + data.hints_count + ' solution(s) (search cap 300).', true);
    } catch (e) {
      flash(e.message, false);
    }
  };

  $('#submitBtn').onclick = async () => {
    const expr = $('#expr').value.trim();
    if (!expr) { flash('Type an expression first.', false); return; }
    try {
      const data = await api('/api/guess', { expression: expr });
      $('#scoreShow').textContent = data.score;
      if (data.solved) {
        flash('\u2713 Perfect! +' + data.scored + ' • New hand dealt.', true);
        renderCards(data.hand);
        $('#expr').value = '';
        burst();
      } else if (!data.expr_ok && data.details) {
        flash(data.details, false);
        play.classList.remove('shake');
        void play.offsetWidth;
        play.classList.add('shake');
      } else if (data.expr_ok && !data.hit_target) {
        flash('Evaluates to ' + data.result + ', not ' + TARGET_GOAL + '.', false);
        play.classList.remove('shake');
        void play.offsetWidth;
        play.classList.add('shake');
      } else flash('Try again.', false);
    } catch (e) { flash(e.message, false); }
  };

  $('#hintBtn').onclick = async () => {
    try {
      const list = await api('/api/hints', {});
      const box = $('#hintBox');
      box.style.display = 'block';
      if (!list || !list.length) box.textContent = 'No hints to show.';
      else box.innerHTML = list.map(e => '<div>' + escapeHtml(e) + '</div>').join('');
    } catch (e) { flash(e.message, false); }
  };

  function escapeHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }
})();
</script>
</body>
</html>
""".replace("__TARGET_HTML__", str(TARGET)).replace("__TARGET_JS__", target_js).replace(
        "__SYM_JSON__", sym_json
    )


class _GameHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[67] %s\n" % (self.address_string() + " - " + (fmt % args),))

    def _send_json(self, obj: object, status: int = 200):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self):
        html = _html_page().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(html)

    def _read_json_body(self):
        length = self.headers.get("Content-Length")
        if not length:
            return {}
        raw = self.rfile.read(min(int(length), 65536))
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send_html()
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        body = self._read_json_body()
        if body is None:
            self._send_json({"error": "Invalid JSON body."}, status=400)
            return

        try:
            if path == "/api/new":
                pick = body.get("pick")
                pick = int(pick) if pick is not None else None
                self._send_json(api_new_pick(pick))
                return
            if path == "/api/guess":
                expr = str(body.get("expression", "")).strip()
                self._send_json(api_guess(expr))
                return
            if path == "/api/hints":
                hints = api_hints()
                self._send_json(hints if isinstance(hints, list) else list(hints))
                return
        except (TypeError, ValueError) as e:
            self._send_json({"error": str(e)}, status=400)
            return
        except RuntimeError as e:
            self._send_json({"error": str(e)}, status=400)
            return

        self._send_json({"error": "Not found."}, status=404)


def serve_browser(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True):
    bind = ("", port)
    srv = ThreadingHTTPServer(bind, _GameHandler)
    url = f"http://{host}:{port}/"
    print(f"Game 67 is running at {url}")
    print("Press Ctrl+C to stop the server.")

    def _open():
        if not open_browser:
            return
        try:
            webbrowser.open(url)
        except Exception:
            print("(Could not launch browser automatically; open the URL manually.)")

    threading.Timer(0.35, _open).start()

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down…")
    finally:
        srv.server_close()


def run_browser(port: int = 8765, open_browser: bool = True):
    """Start the HTTP server (`python -m backend` mirrors `run_browser_game.py`)."""
    serve_browser(port=port, open_browser=open_browser)


def run():
    """Play in the terminal."""
    print("Game 67 — hit the target with every card.")
    print(f"Target: {TARGET}")

    raw = input("Pick a number 1–200 (hand size): ").strip()
    try:
        pick = int(raw)
    except ValueError:
        print("Need an integer.")
        return

    try:
        session = api_new_pick(pick)
    except ValueError as e:
        print(e)
        return

    while True:
        vals = session["hand_values"]
        cards = session["hand"]
        print(f"\nScore: {session['score']}")
        for c in cards:
            sym = SUIT_SYMBOLS[c["suit"]]
            print(f"  {c['rank']}{sym} ({c['value']})")

        expr = input("Expression [q quit, ?h hints]: ").strip()
        if expr.lower() == "q":
            print(f"Final score {session['score']}. Thanks for playing.")
            return

        if expr == "?h":
            hs = solve_all_expressions(vals, target=TARGET, limit=300)
            show = hs[: min(15, len(hs))]
            if not hs:
                print("No solutions found within search cap.")
            else:
                print(f"Showing {len(show)}/{len(hs)}:")
                for h in show:
                    print(f"  {h}")
            continue

        res = api_guess(expr)

        session["score"] = res["score"]
        session["hand"] = res["hand"]
        session["hand_values"] = [c["value"] for c in res["hand"]]

        if not res["expr_ok"]:
            print(res["details"])
            continue

        if res["solved"]:
            print("\u2713 Correct! +" + str(res["scored"]) + " — dealing new cards.")
            continue

        print(f"Equals {res['result']}, not {TARGET}.")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Game 67 — browser server")
    ap.add_argument("--port", type=int, default=8765, help="Local port (default: 8765)")
    ap.add_argument("--no-browser", action="store_true", help="Do not open a browser tab")
    cli = ap.parse_args()
    run_browser(port=cli.port, open_browser=not cli.no_browser)

