#!/usr/bin/env python3
"""Drugi krug: sadrzajna unapredjenja README-a (struktura, demo, bedzevi)."""
import re, subprocess

BASE = "/tmp/opencode/repo-headers"


def run(*a):
    return subprocess.run(a, capture_output=True, text=True)


def load(repo):
    p = f"{BASE}/{repo}/README.md"
    with open(p, encoding="utf-8") as f:
        return f.read().split("\n")


def save(repo, lines, msg):
    p = f"{BASE}/{repo}/README.md"
    with open(p, encoding="utf-8") as f:
        old = f.read()
    new = "\n".join(lines).rstrip() + "\n"
    if new == old:
        print(f"{repo}: SKIP nema izmjena", flush=True)
        return
    with open(p, "w", encoding="utf-8") as f:
        f.write(new)
    d = f"{BASE}/{repo}"
    run("git", "-C", d, "add", "-A")
    run("git", "-C", d, "-c", "user.name=xnet-ba",
        "-c", "user.email=xnet-ba@users.noreply.github.com",
        "commit", "-qm", msg)
    p = run("git", "-C", d, "push", "origin", "HEAD")
    print(f"{repo}: {'PUSH OK' if p.returncode == 0 else 'PUSH FAIL ' + p.stderr.strip()[:150]}",
          flush=True)


def slug(t):
    t = t.lower()
    return "".join(c for c in t if c.isalnum() or c in "-_ ").replace(" ", "-")


BOX = re.compile(r"[┌┐└┘│─▼►├┤┬┴┼►◄]")

# ---------- 1. mujopresa: struktura + ograde ----------
L = load("mujopresa")
if "## Sadržaj" in "\n".join(L):
    print("mujopresa: SKIP struktura vec postoji", flush=True)
else:
    heads = ["🚀 Glavne karakteristike", "🧠 Kako radi", "▶️ Korištenje",
             "⚡ Cython ubrzanje", "📦 Instalacija", "📁 .mujo format",
             "🔐 Integritet", "📊 Cilj projekta", "⚠️ Status", "🧪 Planirani razvoj"]
    out, in_fence, i = [], False, 0
    plan_mode = False
    while i < len(L):
        ln = L[i]
        s = ln.strip()
        if s in heads:
            out.append("## " + s)
        elif s == "MujuPresa placeholder-never":
            out.append(ln)
        elif BOX.search(ln):
            if not in_fence:
                out.append("```")
                in_fence = True
            out.append(ln.rstrip())
        else:
            if in_fence:
                out.append("```")
                in_fence = False
            if re.match(r"^(Kompresija|Dekompresija|Metapodaci se mogu):", s):
                out.append("```bash")
                out.append(s)
                nxt = L[i + 1].strip() if i + 1 < len(L) else ""
                if nxt.startswith("Dobija se:"):
                    out.append(nxt)
                    i += 1
                out.append("```")
            elif re.match(r"^pip install", s):
                out.append("```bash")
                out.append(s)
                out.append("```")
            elif s.startswith("[KRITICNO]"):
                out.append("```text")
                out.append(s)
                out.append("```")
            elif re.match(r"^-(?!-)\S", s):
                out.append("- " + s[1:])
            elif s == "Mogući budući razvoj:":
                out.append(ln)
                plan_mode = True
            elif plan_mode and s and not s.startswith(("-", "#", "<", "`", "!")):
                out.append("- " + s)
            else:
                if s.startswith("## ") or s.startswith("---") or s.startswith("<"):
                    plan_mode = False
                out.append(ln)
        i += 1
    # TOC poslije drugog intro pasusa (linija sa 'dizajniran kao samostalni')
    for j, ln in enumerate(out):
        if "dizajniran kao samostalni kompresor" in ln:
            toc = ["", "## Sadržaj", ""]
            for h in heads + ["v1.1.0 – modularno jezgro"]:
                toc.append(f"- [{h}](#{slug(h)})")
            toc.append("")
            out[j + 1:j + 1] = toc
            break
    save("mujopresa", out, "docs: struktura README (TOC, headingi, code fenceovi)")

# ---------- 2. skills-packs: details + index + dedup ----------
L = load("agentmujo-skills-packs")
if "<details>" in "\n".join(L):
    print("packs: SKIP details vec postoje", flush=True)
else:
    pack_re = re.compile(r"^\S+ AgentMujo.*Skills$")
    idx = [i for i, ln in enumerate(L) if pack_re.match(ln.strip())]
    print(f"packs: pronadjeno {len(idx)}", flush=True)
    assert len(idx) == 23, f"ocekivano 23 head-a, nadjeno {len(idx)}"
    blocks = []
    for k, pi in enumerate(idx):
        end = idx[k + 1] if k + 1 < len(idx) else len(L)
        while end > pi and not L[end - 1].strip():
            end -= 1
        # kraj na footer '---'
        body = [ln for ln in L[pi + 1:end] if not ln.strip().startswith("---")]
        while body and not body[-1].strip():
            body.pop()
        blocks.append((L[pi].strip(), body))
    # dedup: identicni blokovi
    seen, uniq = {}, []
    for h, b in blocks:
        key = (h, tuple(x.strip() for x in b if x.strip()))
        if key in seen:
            print(f"packs: DEDUP brisem duplikat '{h}'", flush=True)
            continue
        seen[key] = True
        uniq.append((h, b))
    start = idx[0]
    head_part = L[:start]
    index_lines = ["", f"**{len(uniq)} paketa** — klikni za skillove pojedinog paketa:", ""]
    for h, b in uniq:
        n = sum(1 for x in b if " — " in x)
        index_lines.append(f"- **{h}** ({n})")
    index_lines.append("")
    new_packs = []
    for h, b in uniq:
        n = sum(1 for x in b if " — " in x)
        new_packs += ["<details>", f"<summary><b>{h} ({n})</b></summary>", ""] + b + ["", "</details>", ""]
    # sacuvaj footer (sve od prvog '---' poslije zadnjeg packa)
    tail_start = idx[-1]
    while tail_start < len(L) and L[tail_start].strip() != "---":
        tail_start += 1
    tail = L[tail_start:]
    out = head_part + index_lines + [""] + new_packs + tail
    save("agentmujo-skills-packs", out, "docs: packovi u details + index + dedup")

# ---------- 3. ascii-motion-studio: demo sekcija ----------
L = load("ascii-motion-studio")
demo = ["## 🎬 Demo", "",
        "![video-ascii](examples/video-ascii.gif)", "",
        "<sub>Video: [MP4](examples/video-ascii.mp4) · "
        "[interaktivni HTML demo](examples/animation.html) · "
        "logo: [GIF](examples/logo-color-black.gif) "
        "[PNG](examples/logo-color-black.png)</sub>", ""]
if any("examples/video-ascii.gif" in ln for ln in L):
    print("ascii-motion-studio: SKIP demo vec postoji", flush=True)
else:
    j = next(i for i, ln in enumerate(L) if ln.strip() == "## Arhitektura")
    save("ascii-motion-studio", L[:j] + demo + L[j:], "docs: demo sekcija (gif + mp4)")

# ---------- 4. training: CI badge org ----------
L = load("agentmujo-training")
txt = "\n".join(L)
if "gamai-io/agentmujo-training" in txt:
    save("agentmujo-training", txt.replace("gamai-io/agentmujo-training",
                                          "xnet-ba/agentmujo-training").split("\n"),
         "docs: CI badge na xnet-ba org")
else:
    print("agentmujo-training: SKIP badge vec tacan", flush=True)

# ---------- 5. mddr-shield: tests badge ----------
L = load("agentmujo-mddr-shield")
badge = ("[![Tests](https://github.com/xnet-ba/agentmujo-mddr-shield/actions/workflows/test.yml/badge.svg)]"
         "(https://github.com/xnet-ba/agentmujo-mddr-shield/actions/workflows/test.yml)")
if "workflows/test.yml/badge" in "\n".join(L):
    print("agentmujo-mddr-shield: SKIP badge vec postoji", flush=True)
else:
    j = next(i for i, ln in enumerate(L) if "badge/Status" in ln)
    save("agentmujo-mddr-shield", L[:j + 1] + [badge] + L[j + 1:],
         "docs: tests badge")
