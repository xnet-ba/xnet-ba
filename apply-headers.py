#!/usr/bin/env python3
"""Rollout matrix header/footer na sve public repove (osim xnet-ba/xnet-ba).
Idempotentno: preskace repove koji vec imaju marker xnet-ba-matrix-header-v1.
Ne dira sadrzaj README-a — samo prepend header + append footer."""
import subprocess, os, unicodedata, urllib.parse, shutil

WORK = "/tmp/opencode/repo-headers"
os.makedirs(WORK, exist_ok=True)

TYPING = ("https://readme-typing-svg.demolab.com?font=Fira+Code&size=16"
          "&duration=2800&pause=800&color=00FF41&center=true&vCenter=true&width=700"
          "&lines=xnet-ba+%3A%3A+open-source+AI+iz+BiH;citaj+README+pa+pokreni;PR+dobrodosli")


def run(*a):
    return subprocess.run(a, capture_output=True, text=True)


def ascii(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return " ".join(s.split())


repos = run("gh", "repo", "list", "xnet-ba", "--json", "name,isPrivate",
            "--limit", "50", "--jq",
            ".[] | select(.isPrivate==false) | .name").stdout.split()

for R in repos:
    if R == "xnet-ba":
        continue
    desc = run("gh", "repo", "view", f"xnet-ba/{R}",
               "--json", "description", "--jq", ".description // \"\"").stdout.strip()
    d = ascii(desc)
    if not d or d.lower() == R.lower():
        d = "open-source AI iz BiH"
    d = d[:60]
    fs = 42 if len(R) <= 16 else (32 if len(R) <= 24 else 24)
    q = urllib.parse.quote
    header = f"""<!-- xnet-ba-matrix-header-v1 -->
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=00FF41&height=140&section=header&text={q(R)}&fontColor=000000&fontSize={fs}&fontAlignY=32&desc={q(d)}&descAlignY=55" width="100%" alt="{R}"/>

[![Typing SVG]({TYPING})](https://github.com/xnet-ba/{R})

[![Stars](https://img.shields.io/github/stars/xnet-ba/{R}?style=flat-square&color=00FF41&labelColor=000000)](https://github.com/xnet-ba/{R}/stargazers)
[![License](https://img.shields.io/github/license/xnet-ba/{R}?style=flat-square&color=00FF41&labelColor=000000)](LICENSE)
[![Top lang](https://img.shields.io/github/languages/top/xnet-ba/{R}?style=flat-square&color=00FF41&labelColor=000000)](https://github.com/xnet-ba/{R})
[![Last commit](https://img.shields.io/github/last-commit/xnet-ba/{R}?style=flat-square&color=00FF41&labelColor=000000)](https://github.com/xnet-ba/{R}/commits)
[![matrix](https://img.shields.io/badge/MATRIX-xnet--ba-00FF41?style=flat-square&labelColor=000000)](https://github.com/xnet-ba)

</div>

---
"""
    footer = """
---

<div align="center">
<img src="https://raw.githubusercontent.com/xnet-ba/xnet-ba/main/assets/divider.svg" width="100%" alt=""/>
<sup>part of <a href="https://github.com/xnet-ba">xnet-ba matrix</a> — open-source AI iz BiH</sup>
</div>
"""
    dest = os.path.join(WORK, R)
    shutil.rmtree(dest, ignore_errors=True)
    r = run("gh", "repo", "clone", f"xnet-ba/{R}", dest)
    if r.returncode != 0:
        print(f"{R}: CLONE FAIL {r.stderr.strip()[:120]}", flush=True)
        continue
    readme = None
    candidates = [f for f in sorted(os.listdir(dest))
                  if f.lower().startswith("readme")
                  and os.path.isfile(os.path.join(dest, f))]
    exact = [f for f in candidates if f.lower() == "readme.md"]
    if exact:
        readme = os.path.join(dest, exact[0])
    elif candidates:
        readme = os.path.join(dest, candidates[0])
    if readme:
        txt = open(readme, encoding="utf-8", errors="replace").read()
        if "xnet-ba-matrix-header-v1" in txt:
            print(f"{R}: SKIP vec ima header", flush=True)
            continue
        open(readme, "w", encoding="utf-8").write(header + txt.rstrip() + "\n" + footer)
    else:
        readme = os.path.join(dest, "README.md")
        open(readme, "w", encoding="utf-8").write(header + f"# {R}\n\n{d}\n" + footer)
    if not run("git", "-C", dest, "status", "--porcelain").stdout.strip():
        print(f"{R}: SKIP nema izmjena", flush=True)
        continue
    run("git", "-C", dest, "add", "-A")
    run("git", "-C", dest, "-c", "user.name=xnet-ba",
        "-c", "user.email=xnet-ba@users.noreply.github.com",
        "commit", "-qm", "docs: matrix header v1 (badges + footer)")
    p = run("git", "-C", dest, "push", "origin", "HEAD")
    print(f"{R}: {'PUSH OK' if p.returncode == 0 else 'PUSH FAIL ' + p.stderr.strip()[:150]}",
          flush=True)
