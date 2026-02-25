"""
RSA Encryption Visualizer
A step-by-step educational tool showing how RSA asymmetric encryption works.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import math
import random


# ─── RSA Math ─────────────────────────────────────────────────────────────────

def is_prime(n: int) -> bool:
    """Return True if n is a prime number."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.isqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def extended_gcd(a: int, b: int):
    """
    Extended Euclidean Algorithm.
    Returns (gcd, x, y) such that a*x + b*y = gcd(a, b).
    Also returns a list of steps for visualisation.
    """
    steps = []
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1

    steps.append(
        f"  Start: r={old_r}, s={old_s}, t={old_t}"
        f"   |   r={r}, s={s}, t={t}"
    )

    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
        steps.append(
            f"  q={quotient}: r={old_r}, s={old_s}, t={old_t}"
            f"   |   r={r}, s={s}, t={t}"
        )

    return old_r, old_s, old_t, steps


def mod_inverse(e: int, phi: int):
    """
    Compute d such that e*d ≡ 1 (mod phi) using the extended GCD.
    Returns (d, steps_list).
    """
    gcd, x, _, steps = extended_gcd(e, phi)
    if gcd != 1:
        return None, steps
    return x % phi, steps


def find_valid_e(phi: int) -> int:
    """Find a common public exponent e valid for the given phi."""
    for candidate in [65537, 17, 5, 3]:
        if candidate < phi and math.gcd(candidate, phi) == 1:
            return candidate
    # Fallback: brute-force small odd e
    for e in range(3, phi, 2):
        if math.gcd(e, phi) == 1:
            return e
    return 2


def fast_pow_steps(base: int, exp: int, mod: int):
    """
    Modular exponentiation (square-and-multiply) returning the result
    and a list of human-readable steps.
    """
    steps = []
    steps.append(f"  Compute {base}^{exp} mod {mod}")
    steps.append(f"  Exponent in binary: {bin(exp)}")
    result = 1
    b = base % mod
    e = exp
    step_num = 1
    while e > 0:
        if e % 2 == 1:
            result = (result * b) % mod
            steps.append(
                f"  Step {step_num}: bit=1 → result = (result × {b}) mod {mod} = {result}"
            )
        else:
            steps.append(
                f"  Step {step_num}: bit=0 → result unchanged = {result}"
            )
        b = (b * b) % mod
        e //= 2
        step_num += 1
    steps.append(f"  ✓ Final result = {result}")
    return result, steps


# ─── Colour palette ───────────────────────────────────────────────────────────

BG        = "#1e1e2e"
PANEL     = "#2a2a3e"
ACCENT    = "#cba6f7"       # lavender
GREEN     = "#a6e3a1"
YELLOW    = "#f9e2af"
BLUE      = "#89b4fa"
RED       = "#f38ba8"
TEXT      = "#cdd6f4"
SUBTEXT   = "#a6adc8"
BORDER    = "#45475a"
MONO      = ("Courier New", 10)
MONO_BIG  = ("Courier New", 12, "bold")
SANS      = ("Helvetica", 10)
SANS_BIG  = ("Helvetica", 13, "bold")
SANS_TITLE= ("Helvetica", 16, "bold")


# ─── Reusable widgets ─────────────────────────────────────────────────────────

def styled_label(parent, text, fg=TEXT, font=SANS, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=BG, font=font, **kw)


def styled_entry(parent, width=10, **kw):
    e = tk.Entry(parent, width=width, bg=PANEL, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=4, font=MONO, **kw)
    return e


def styled_button(parent, text, command, color=ACCENT, **kw):
    return tk.Button(
        parent, text=text, command=command,
        bg=color, fg=BG, activebackground=TEXT,
        font=SANS, relief="flat", padx=12, pady=6, cursor="hand2", **kw
    )


def log_box(parent, height=14):
    """A read-only, monospaced, dark scrolled text widget."""
    st = scrolledtext.ScrolledText(
        parent, height=height, bg=PANEL, fg=TEXT,
        font=MONO, relief="flat", bd=0,
        state="disabled", wrap="word",
        insertbackground=TEXT,
    )
    st.configure(highlightbackground=BORDER, highlightthickness=1)
    return st


def log_write(widget, text, tag=None):
    widget.configure(state="normal")
    if tag:
        widget.insert("end", text + "\n", tag)
    else:
        widget.insert("end", text + "\n")
    widget.see("end")
    widget.configure(state="disabled")


def log_clear(widget):
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.configure(state="disabled")


# ─── Main Application ─────────────────────────────────────────────────────────

class RSAApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RSA Encryption Visualizer")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(900, 640)

        # Shared RSA state
        self.p = tk.IntVar(value=61)
        self.q = tk.IntVar(value=53)
        self.e_var = tk.IntVar(value=17)
        self.n = None
        self.phi = None
        self.e = None
        self.d = None
        self.keys_ready = False

        self._build_header()
        self._build_notebook()
        self._build_status_bar()

    # ── Header ──────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=ACCENT, pady=10)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="🔐  RSA Encryption Visualizer",
            bg=ACCENT, fg=BG, font=SANS_TITLE
        ).pack()
        tk.Label(
            hdr,
            text="Learn how RSA asymmetric encryption works — step by step",
            bg=ACCENT, fg=BG, font=SANS
        ).pack()

    # ── Notebook ─────────────────────────────────────────────────────────────

    def _build_notebook(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Dark.TNotebook",        background=BG, borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
                        background=PANEL, foreground=SUBTEXT,
                        padding=[14, 6], font=SANS)
        style.map("Dark.TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", BG)])

        self.nb = ttk.Notebook(self, style="Dark.TNotebook")
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)

        self._tab_keygen()
        self._tab_encrypt()
        self._tab_decrypt()
        self._tab_theory()

    # ── Status bar ───────────────────────────────────────────────────────────

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="👋  Enter two primes and generate keys to get started.")
        bar = tk.Label(
            self, textvariable=self.status_var,
            bg=BORDER, fg=TEXT, font=SANS, anchor="w", padx=10, pady=4
        )
        bar.pack(fill="x", side="bottom")

    def _set_status(self, msg):
        self.status_var.set(msg)

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 1 — Key Generation
    # ════════════════════════════════════════════════════════════════════════

    def _tab_keygen(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="  🔑  Key Generation  ")

        # ── Controls ──────────────────────────────────────────────────────
        ctrl = tk.Frame(frame, bg=BG)
        ctrl.pack(fill="x", padx=20, pady=(14, 6))

        styled_label(ctrl, "Prime  p:", fg=YELLOW, font=SANS_BIG).grid(row=0, column=0, padx=6, pady=4, sticky="w")
        self.entry_p = styled_entry(ctrl, width=8)
        self.entry_p.insert(0, str(self.p.get()))
        self.entry_p.grid(row=0, column=1, padx=6)

        styled_label(ctrl, "Prime  q:", fg=YELLOW, font=SANS_BIG).grid(row=0, column=2, padx=6, pady=4, sticky="w")
        self.entry_q = styled_entry(ctrl, width=8)
        self.entry_q.insert(0, str(self.q.get()))
        self.entry_q.grid(row=0, column=3, padx=6)

        styled_label(ctrl, "Public exp  e:", fg=BLUE, font=SANS_BIG).grid(row=0, column=4, padx=6, pady=4, sticky="w")
        self.entry_e = styled_entry(ctrl, width=8)
        self.entry_e.insert(0, str(self.e_var.get()))
        self.entry_e.grid(row=0, column=5, padx=6)

        btn_row = tk.Frame(frame, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=4)
        styled_button(btn_row, "⚙  Generate Keys", self._generate_keys, color=ACCENT).pack(side="left", padx=6)
        styled_button(btn_row, "🎲  Random Primes", self._random_primes, color=YELLOW).pack(side="left", padx=6)
        styled_button(btn_row, "🗑  Clear Log", lambda: log_clear(self.kg_log), color=BORDER).pack(side="left", padx=6)

        # ── Key display boxes ─────────────────────────────────────────────
        keys_frame = tk.Frame(frame, bg=BG)
        keys_frame.pack(fill="x", padx=20, pady=6)

        pub_box = tk.LabelFrame(keys_frame, text=" 🔓  Public Key ", bg=BG, fg=BLUE,
                                font=SANS_BIG, bd=2, relief="groove")
        pub_box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.pub_label = tk.Label(pub_box, text="(n, e) = (?, ?)", bg=BG,
                                  fg=BLUE, font=MONO_BIG, pady=10)
        self.pub_label.pack()

        priv_box = tk.LabelFrame(keys_frame, text=" 🔒  Private Key ", bg=BG, fg=RED,
                                 font=SANS_BIG, bd=2, relief="groove")
        priv_box.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.priv_label = tk.Label(priv_box, text="(n, d) = (?, ?)", bg=BG,
                                   fg=RED, font=MONO_BIG, pady=10)
        self.priv_label.pack()

        # ── Log ───────────────────────────────────────────────────────────
        tk.Label(frame, text="  Step-by-step log:", bg=BG, fg=SUBTEXT, font=SANS,
                 anchor="w").pack(fill="x", padx=20)
        self.kg_log = log_box(frame, height=16)
        self.kg_log.pack(fill="both", expand=True, padx=20, pady=(2, 14))

        # Configure tags
        for tag, col in [("head", ACCENT), ("ok", GREEN), ("warn", YELLOW),
                         ("err", RED), ("info", BLUE), ("eq", TEXT)]:
            self.kg_log.tag_configure(tag, foreground=col)

    def _random_primes(self):
        """Fill p, q with random small primes."""
        small_primes = [p for p in range(11, 200) if is_prime(p)]
        p = random.choice(small_primes)
        q_candidates = [x for x in small_primes if x != p]
        q = random.choice(q_candidates)
        self.entry_p.delete(0, "end"); self.entry_p.insert(0, str(p))
        self.entry_q.delete(0, "end"); self.entry_q.insert(0, str(q))
        self._set_status(f"🎲  Random primes: p={p}, q={q}.  Now click Generate Keys.")

    def _generate_keys(self):
        log_clear(self.kg_log)
        log_write(self.kg_log, "═" * 60, "head")
        log_write(self.kg_log, "  RSA KEY GENERATION  ", "head")
        log_write(self.kg_log, "═" * 60, "head")

        # Parse inputs
        try:
            p = int(self.entry_p.get())
            q = int(self.entry_q.get())
            e = int(self.entry_e.get())
        except ValueError:
            messagebox.showerror("Input Error", "p, q and e must be integers.")
            return

        # Validate primes
        if not is_prime(p):
            log_write(self.kg_log, f"  ✗  p={p} is NOT prime.", "err")
            self._set_status(f"❌  p={p} is not prime.  Please choose a prime.")
            return
        log_write(self.kg_log, f"  ✓  p = {p}  (prime)", "ok")

        if not is_prime(q):
            log_write(self.kg_log, f"  ✗  q={q} is NOT prime.", "err")
            self._set_status(f"❌  q={q} is not prime.  Please choose a prime.")
            return
        log_write(self.kg_log, f"  ✓  q = {q}  (prime)", "ok")

        if p == q:
            log_write(self.kg_log, "  ✗  p and q must be different.", "err")
            return

        # Step 1: n
        n = p * q
        log_write(self.kg_log, "")
        log_write(self.kg_log, "  ── STEP 1: Compute the modulus ──────────────────────", "head")
        log_write(self.kg_log, f"  n = p × q = {p} × {q} = {n}", "eq")

        # Step 2: phi
        phi = (p - 1) * (q - 1)
        log_write(self.kg_log, "")
        log_write(self.kg_log, "  ── STEP 2: Euler's totient function φ(n) ────────────", "head")
        log_write(self.kg_log, f"  φ(n) = (p−1)(q−1) = ({p}−1)({q}−1)", "eq")
        log_write(self.kg_log, f"       = {p-1} × {q-1} = {phi}", "eq")

        # Step 3: e
        log_write(self.kg_log, "")
        log_write(self.kg_log, "  ── STEP 3: Choose public exponent e ─────────────────", "head")
        log_write(self.kg_log, f"  Conditions: 1 < e < {phi}  AND  gcd(e, φ(n)) = 1", "info")

        gcd_e_phi = math.gcd(e, phi)
        if not (1 < e < phi) or gcd_e_phi != 1:
            suggested = find_valid_e(phi)
            log_write(self.kg_log, f"  ✗  e={e} is invalid  (gcd={gcd_e_phi}).  Suggest e={suggested}", "warn")
            e = suggested
            self.entry_e.delete(0, "end")
            self.entry_e.insert(0, str(e))
            log_write(self.kg_log, f"  → Auto-corrected to e = {e}", "ok")
        else:
            log_write(self.kg_log, f"  gcd({e}, {phi}) = {gcd_e_phi}  ✓", "ok")
            log_write(self.kg_log, f"  e = {e}  is valid", "ok")

        # Step 4: d  (extended GCD)
        log_write(self.kg_log, "")
        log_write(self.kg_log, "  ── STEP 4: Compute private exponent d ───────────────", "head")
        log_write(self.kg_log, f"  Find d such that:  e·d ≡ 1 (mod φ(n))", "info")
        log_write(self.kg_log, f"  i.e.  {e}·d ≡ 1 (mod {phi})", "info")
        log_write(self.kg_log, "")
        log_write(self.kg_log, "  Extended Euclidean Algorithm on (e, φ(n)):", "head")
        log_write(self.kg_log, f"  Columns: (remainder r, Bézout coeff s for e, Bézout coeff t for φ)", "info")

        d, ext_steps = mod_inverse(e, phi)
        for step in ext_steps:
            log_write(self.kg_log, step, "eq")

        if d is None:
            log_write(self.kg_log, "  ✗  No modular inverse — gcd ≠ 1!", "err")
            return

        log_write(self.kg_log, "")
        log_write(self.kg_log, f"  gcd(e, φ(n)) = 1  ✓  →  d = {e}⁻¹ mod {phi} = {d}", "ok")
        log_write(self.kg_log, f"  Verify: {e} × {d} mod {phi} = {(e * d) % phi}  (should be 1)", "ok")

        # Step 5: Summary
        log_write(self.kg_log, "")
        log_write(self.kg_log, "  ── STEP 5: Key Summary ──────────────────────────────", "head")
        log_write(self.kg_log, f"  🔓  Public  Key : (n={n},  e={e})", "info")
        log_write(self.kg_log, f"  🔒  Private Key : (n={n},  d={d})", "warn")
        log_write(self.kg_log, "")
        log_write(self.kg_log, "  ⚠  Keep d secret!  Anyone with d can decrypt your messages.", "err")
        log_write(self.kg_log, "═" * 60, "head")

        # Store state
        self.n, self.phi, self.e, self.d = n, phi, e, d
        self.keys_ready = True

        self.pub_label.config(text=f"(n={n},  e={e})")
        self.priv_label.config(text=f"(n={n},  d={d})")
        self._set_status(f"✅  Keys ready — Public(n={n}, e={e})   Private(n={n}, d={d})")

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 2 — Encryption
    # ════════════════════════════════════════════════════════════════════════

    def _tab_encrypt(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="  🔏  Encryption  ")

        # ── Controls ──────────────────────────────────────────────────────
        ctrl = tk.Frame(frame, bg=BG)
        ctrl.pack(fill="x", padx=20, pady=(14, 6))

        styled_label(ctrl, "Plaintext message  m  (integer, 0 < m < n):",
                     fg=GREEN, font=SANS_BIG).grid(row=0, column=0, padx=6, sticky="w")
        self.entry_msg = styled_entry(ctrl, width=12)
        self.entry_msg.insert(0, "42")
        self.entry_msg.grid(row=0, column=1, padx=6)

        btn_row = tk.Frame(frame, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=4)
        styled_button(btn_row, "🔏  Encrypt", self._encrypt, color=GREEN).pack(side="left", padx=6)
        styled_button(btn_row, "🗑  Clear", lambda: log_clear(self.enc_log), color=BORDER).pack(side="left", padx=6)

        # ── Result banner ─────────────────────────────────────────────────
        self.enc_result = tk.Label(
            frame, text="Ciphertext  c  =  ?",
            bg=PANEL, fg=GREEN, font=MONO_BIG, pady=10
        )
        self.enc_result.pack(fill="x", padx=20, pady=6)

        # ── Log ───────────────────────────────────────────────────────────
        tk.Label(frame, text="  Step-by-step log:", bg=BG, fg=SUBTEXT, font=SANS,
                 anchor="w").pack(fill="x", padx=20)
        self.enc_log = log_box(frame, height=16)
        self.enc_log.pack(fill="both", expand=True, padx=20, pady=(2, 14))
        for tag, col in [("head", ACCENT), ("ok", GREEN), ("warn", YELLOW),
                         ("err", RED), ("info", BLUE), ("eq", TEXT)]:
            self.enc_log.tag_configure(tag, foreground=col)

    def _encrypt(self):
        if not self.keys_ready:
            messagebox.showwarning("No Keys", "Please generate keys first (Key Generation tab).")
            return
        log_clear(self.enc_log)
        log_write(self.enc_log, "═" * 60, "head")
        log_write(self.enc_log, "  RSA ENCRYPTION  ", "head")
        log_write(self.enc_log, "═" * 60, "head")

        try:
            m = int(self.entry_msg.get())
        except ValueError:
            messagebox.showerror("Input Error", "Message must be an integer.")
            return

        n, e = self.n, self.e

        log_write(self.enc_log, f"  Public Key : (n={n},  e={e})", "info")
        log_write(self.enc_log, f"  Plaintext  :  m = {m}", "ok")

        if not (0 < m < n):
            log_write(self.enc_log, f"  ✗  m must satisfy  0 < m < n={n}", "err")
            self._set_status(f"❌  Message must be 0 < m < {n}")
            return

        log_write(self.enc_log, "")
        log_write(self.enc_log, "  ── Formula ──────────────────────────────────────────", "head")
        log_write(self.enc_log, f"  c = m^e mod n", "eq")
        log_write(self.enc_log, f"  c = {m}^{e} mod {n}", "eq")
        log_write(self.enc_log, "")
        log_write(self.enc_log, "  ── Square-and-Multiply (fast modular exponentiation) ─", "head")

        c, steps = fast_pow_steps(m, e, n)
        for s in steps:
            log_write(self.enc_log, s, "eq")

        log_write(self.enc_log, "")
        log_write(self.enc_log, f"  ✓  Ciphertext  c = {c}", "ok")
        log_write(self.enc_log, "═" * 60, "head")

        self.enc_result.config(text=f"Ciphertext  c  =  {c}")
        self.last_cipher = c
        self._set_status(f"✅  Encrypted: m={m}  →  c={c}")

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 3 — Decryption
    # ════════════════════════════════════════════════════════════════════════

    def _tab_decrypt(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="  🔓  Decryption  ")

        # ── Controls ──────────────────────────────────────────────────────
        ctrl = tk.Frame(frame, bg=BG)
        ctrl.pack(fill="x", padx=20, pady=(14, 6))

        styled_label(ctrl, "Ciphertext  c  (integer):",
                     fg=RED, font=SANS_BIG).grid(row=0, column=0, padx=6, sticky="w")
        self.entry_cipher = styled_entry(ctrl, width=16)
        self.entry_cipher.insert(0, "?")
        self.entry_cipher.grid(row=0, column=1, padx=6)

        btn_row = tk.Frame(frame, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=4)
        styled_button(btn_row, "🔓  Decrypt", self._decrypt, color=RED).pack(side="left", padx=6)
        styled_button(btn_row, "📋  Use Last Ciphertext", self._use_last_cipher, color=YELLOW).pack(side="left", padx=6)
        styled_button(btn_row, "🗑  Clear", lambda: log_clear(self.dec_log), color=BORDER).pack(side="left", padx=6)

        # ── Result banner ─────────────────────────────────────────────────
        self.dec_result = tk.Label(
            frame, text="Decrypted message  m  =  ?",
            bg=PANEL, fg=GREEN, font=MONO_BIG, pady=10
        )
        self.dec_result.pack(fill="x", padx=20, pady=6)

        # ── Log ───────────────────────────────────────────────────────────
        tk.Label(frame, text="  Step-by-step log:", bg=BG, fg=SUBTEXT, font=SANS,
                 anchor="w").pack(fill="x", padx=20)
        self.dec_log = log_box(frame, height=16)
        self.dec_log.pack(fill="both", expand=True, padx=20, pady=(2, 14))
        for tag, col in [("head", ACCENT), ("ok", GREEN), ("warn", YELLOW),
                         ("err", RED), ("info", BLUE), ("eq", TEXT)]:
            self.dec_log.tag_configure(tag, foreground=col)

        self.last_cipher = None

    def _use_last_cipher(self):
        if self.last_cipher is None:
            messagebox.showinfo("No cipher", "Encrypt a message first to get a ciphertext.")
            return
        self.entry_cipher.delete(0, "end")
        self.entry_cipher.insert(0, str(self.last_cipher))

    def _decrypt(self):
        if not self.keys_ready:
            messagebox.showwarning("No Keys", "Please generate keys first (Key Generation tab).")
            return
        log_clear(self.dec_log)
        log_write(self.dec_log, "═" * 60, "head")
        log_write(self.dec_log, "  RSA DECRYPTION  ", "head")
        log_write(self.dec_log, "═" * 60, "head")

        try:
            c = int(self.entry_cipher.get())
        except ValueError:
            messagebox.showerror("Input Error", "Ciphertext must be an integer.")
            return

        n, d, e = self.n, self.d, self.e

        log_write(self.dec_log, f"  Private Key : (n={n},  d={d})", "warn")
        log_write(self.dec_log, f"  Ciphertext  :  c = {c}", "err")
        log_write(self.dec_log, "")
        log_write(self.dec_log, "  ── How d was obtained (recap) ───────────────────────", "head")
        log_write(self.dec_log, f"  We solved:  {e}·d ≡ 1 (mod {self.phi})", "info")
        log_write(self.dec_log, f"  Using the Extended Euclidean Algorithm → d = {d}", "info")
        log_write(self.dec_log, "")
        log_write(self.dec_log, "  ── Formula ──────────────────────────────────────────", "head")
        log_write(self.dec_log, f"  m = c^d mod n", "eq")
        log_write(self.dec_log, f"  m = {c}^{d} mod {n}", "eq")
        log_write(self.dec_log, "")
        log_write(self.dec_log, "  ── Square-and-Multiply ───────────────────────────────", "head")

        m_recovered, steps = fast_pow_steps(c, d, n)
        for s in steps:
            log_write(self.dec_log, s, "eq")

        log_write(self.dec_log, "")
        log_write(self.dec_log, f"  ✓  Decrypted message  m = {m_recovered}", "ok")
        log_write(self.dec_log, "═" * 60, "head")

        self.dec_result.config(text=f"Decrypted message  m  =  {m_recovered}")
        self._set_status(f"✅  Decrypted: c={c}  →  m={m_recovered}")

    # ════════════════════════════════════════════════════════════════════════
    #  TAB 4 — Theory Cheatsheet
    # ════════════════════════════════════════════════════════════════════════

    def _tab_theory(self):
        frame = tk.Frame(self.nb, bg=BG)
        self.nb.add(frame, text="  📖  Theory  ")

        st = scrolledtext.ScrolledText(
            frame, bg=PANEL, fg=TEXT,
            font=("Courier New", 11), relief="flat", bd=0,
            state="normal", wrap="word", padx=20, pady=14
        )
        st.pack(fill="both", expand=True, padx=10, pady=10)

        for tag, col, fnt in [
            ("h1",    ACCENT,   ("Courier New", 14, "bold")),
            ("h2",    BLUE,     ("Courier New", 12, "bold")),
            ("ok",    GREEN,    ("Courier New", 11)),
            ("warn",  YELLOW,   ("Courier New", 11)),
            ("red",   RED,      ("Courier New", 11)),
            ("plain", TEXT,     ("Courier New", 11)),
        ]:
            st.tag_configure(tag, foreground=col, font=fnt)

        def w(t, tag="plain"):
            st.insert("end", t + "\n", tag)

        w("RSA — A Visual Cheatsheet", "h1")
        w("─" * 62, "h2")
        w("")
        w("1. KEY GENERATION", "h2")
        w("   a) Choose two distinct primes  p  and  q.", "ok")
        w("   b) Compute  n = p × q   (the public modulus).", "ok")
        w("   c) Compute Euler's totient  φ(n) = (p−1)(q−1).", "ok")
        w("   d) Choose  e  with  1 < e < φ(n)  and  gcd(e, φ(n)) = 1.", "ok")
        w("   e) Compute  d = e⁻¹ mod φ(n)  via Extended GCD.", "ok")
        w("   → Public Key:  (n, e)", "warn")
        w("   → Private Key: (n, d)  ← keep secret!", "red")
        w("")
        w("2. ENCRYPTION  (anyone with the public key can do this)", "h2")
        w("   c = m^e mod n", "ok")
        w("   where m is the plaintext  (integer, 0 < m < n)", "plain")
        w("")
        w("3. DECRYPTION  (only the private key holder can do this)", "h2")
        w("   m = c^d mod n", "ok")
        w("   This works because of Euler's theorem:", "plain")
        w("   m^(e·d) ≡ m^(k·φ(n)+1) ≡ m (mod n)", "plain")
        w("")
        w("─" * 62, "h2")
        w("")
        w("4. EXTENDED EUCLIDEAN ALGORITHM", "h2")
        w("   Used to find d = e⁻¹ mod φ(n).", "plain")
        w("")
        w("   Goal: find (gcd, x, y) such that  a·x + b·y = gcd(a, b)", "ok")
        w("")
        w("   Algorithm (iterative):", "warn")
        w("   (r₀, s₀, t₀) = (a, 1, 0)", "plain")
        w("   (r₁, s₁, t₁) = (b, 0, 1)", "plain")
        w("   Loop while r₁ ≠ 0:", "plain")
        w("       q  = r₀ // r₁", "plain")
        w("       (r₀, r₁) = (r₁, r₀ − q·r₁)", "plain")
        w("       (s₀, s₁) = (s₁, s₀ − q·s₁)", "plain")
        w("       (t₀, t₁) = (t₁, t₀ − q·t₁)", "plain")
        w("   Result: gcd = r₀,  x = s₀,  y = t₀", "plain")
        w("")
        w("   If gcd = 1, then  d = x mod φ(n).", "ok")
        w("")
        w("─" * 62, "h2")
        w("")
        w("5. SECURITY NOTE", "h2")
        w("   • Real RSA uses primes with 1024–4096 bits.", "red")
        w("   • This tool uses small numbers for educational purposes.", "warn")
        w("   • Never use small primes in production!", "red")
        w("")
        w("─" * 62, "h2")
        w("")
        w("6. MODULAR EXPONENTIATION (square-and-multiply)", "h2")
        w("   Efficiently computes b^e mod n in O(log e) steps.", "plain")
        w("   Decompose exponent into binary; for each bit:", "plain")
        w("     bit=1 → result = result × base (mod n)", "ok")
        w("     bit=0 → result unchanged", "plain")
        w("     always → base = base² (mod n)", "plain")

        st.configure(state="disabled")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = RSAApp()
    app.mainloop()
