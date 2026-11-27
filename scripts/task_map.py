#!/usr/bin/env python3
"""Generate the task map: Mermaid dependency diagrams built from the GitHub issues.

The map is written into the body of the issue labelled `task-map`. It is rebuilt
by .github/workflows/task-map.yml whenever an issue or a branch changes.

Usage:
    python3 scripts/task_map.py            print the map to stdout
    python3 scripts/task_map.py --update   write it to the task-map issue

Needs the `gh` CLI, authenticated (in CI through GH_TOKEN) and, outside a
checkout of the repository, GH_REPO=owner/name.

Where the data comes from:
    task        an issue whose title starts with an ID, e.g. "W2-04: ..."
    dependency  a "- #12 ..." line in the issue's "## Depends on" section;
                a "- Milestone M3" line means every task of that milestone
    done        the issue is closed
    in progress the issue is open and a branch starts with the task ID
                (w2-04-chunk-search), as CONTRIBUTING.md prescribes
    ready       the issue is open and every dependency is closed
    blocked     the issue is open and a dependency is still open
"""
import json
import re
import subprocess
import sys
import tempfile

MAP_LABEL = "task-map"
MAP_TITLE = "Task map"
CRITICAL_LABEL = "critical-path"
ID_RE = re.compile(r"^(P-\d\d|W\d-\d\d): (.+)$")

# symbol, legend text, fill, border, text colour
STATES = {
    "done": ("✓", "done", "#d5ecd4", "#2e7d32", "#1b3a1d"),
    "progress": ("▶", "in progress", "#fff0c2", "#b26a00", "#4a3000"),
    "ready": ("○", "ready to start", "#d6e6fb", "#1565c0", "#0d2f5c"),
    "blocked": ("✕", "blocked by an open task", "#eceff1", "#78909c", "#37474f"),
}


def gh(args):
    return subprocess.check_output(["gh"] + args).decode("utf-8")


def load():
    fields = "number,title,state,body,labels,milestone"
    issues = json.loads(gh(["issue", "list", "--state", "all", "--limit", "1000", "--json", fields]))
    branches = gh(["api", "repos/{owner}/{repo}/branches", "--paginate", "--jq", ".[].name"]).split()
    return issues, [b.lower() for b in branches]


def build(issues, branches):
    tasks, by_number, map_issue = {}, {}, None
    for it in issues:
        labels = [l["name"] for l in it["labels"]]
        if MAP_LABEL in labels:
            map_issue = it
            continue
        m = ID_RE.match(it["title"])
        if not m:
            continue
        tid = m.group(1)
        section = re.search(r"^## Depends on\s*$(.*?)(?=^## |^---\s*$|\Z)", it["body"] or "", re.S | re.M)
        tasks[tid] = {
            "id": tid,
            "name": m.group(2),
            "number": it["number"],
            "closed": it["state"] == "CLOSED",
            "milestone": (it["milestone"] or {}).get("title") or "No milestone",
            "critical": CRITICAL_LABEL in labels,
            "dep_numbers": [int(n) for n in re.findall(r"^\s*[-*] #(\d+)", section.group(1), re.M)] if section else [],
            "dep_milestones": re.findall(r"^\s*[-*] Milestone (M\d+)", section.group(1), re.M) if section else [],
        }
        by_number[it["number"]] = tid
    for t in tasks.values():
        t["deps"] = sorted({by_number[n] for n in t["dep_numbers"] if n in by_number and by_number[n] != t["id"]})
        # Milestone dependencies count for the state but are not drawn as arrows.
        t["open_milestones"] = [
            m for m in t["dep_milestones"]
            if any(o["milestone"].split(" ")[0] == m and not o["closed"] for o in tasks.values())]
        prefix = t["id"].lower()
        if t["closed"]:
            t["state"] = "done"
        elif any(b == prefix or b.startswith(prefix + "-") for b in branches):
            t["state"] = "progress"
        elif all(tasks[d]["closed"] for d in t["deps"]) and not t["open_milestones"]:
            t["state"] = "ready"
        else:
            t["state"] = "blocked"
    return tasks, map_issue


def node(t):
    name = t["name"].replace('"', "'")
    if len(name) > 44:
        name = name[:43].rstrip() + "…"
    return '    %s["%s %s<br/>%s"]:::%s' % (
        t["id"].replace("-", "_"), STATES[t["state"]][0], t["id"], name, t["state"])


def diagram(tasks, ids, edges, direction="LR"):
    out = ["```mermaid", "flowchart " + direction]
    out += [node(tasks[i]) for i in sorted(ids)]
    out += ["    %s --> %s" % (a.replace("-", "_"), b.replace("-", "_")) for a, b in sorted(edges)]
    for key, (_, _, fill, stroke, color) in STATES.items():
        out.append("    classDef %s fill:%s,stroke:%s,color:%s" % (key, fill, stroke, color))
    out.append("```")
    return out


def critical_edges(tasks):
    """Link each critical task to the nearest critical tasks it depends on,
    following dependencies through tasks that are not on the critical path."""
    edges = set()
    for t in tasks.values():
        if not t["critical"]:
            continue
        seen, stack = set(), list(t["deps"])
        while stack:
            d = stack.pop()
            if d in seen:
                continue
            seen.add(d)
            if tasks[d]["critical"]:
                edges.add((d, t["id"]))
            else:
                stack.extend(tasks[d]["deps"])
    return edges


def task_line(t, tasks):
    line = "- #%d **%s** %s" % (t["number"], t["id"], t["name"])
    if t["state"] == "blocked":
        waiting = ["%s (#%d)" % (d, tasks[d]["number"]) for d in t["deps"] if not tasks[d]["closed"]]
        waiting += ["milestone %s" % m for m in t["open_milestones"]]
        line += " — waits for " + ", ".join(waiting)
    return line


def render(tasks):
    order = sorted(tasks.values(), key=lambda t: t["id"])
    milestones = sorted({t["milestone"] for t in order})
    done = sum(t["closed"] for t in order)
    out = [
        "This issue is generated by `scripts/task_map.py`. **Do not edit it by hand**; "
        "the next update overwrites it. It is rebuilt when an issue is opened, edited, "
        "closed or reopened and when a branch is created or deleted.",
        "",
        "**%d of %d tasks done.**" % (done, len(order)),
        "",
        "| Symbol | Meaning |",
        "| :---: | :--- |",
    ]
    for key in ("done", "progress", "ready", "blocked"):
        out.append("| %s | %s |" % (STATES[key][0], STATES[key][1]))
    out += ["",
            "A task counts as *in progress* when a branch starts with its ID, "
            "for example `w2-04-chunk-search`. Arrows point from a task to the tasks that need it.",
            "",
            "| Milestone | Done | In progress | Ready | Blocked |",
            "| :--- | ---: | ---: | ---: | ---: |"]
    for ms in milestones:
        group = [t for t in order if t["milestone"] == ms]
        count = lambda s: sum(t["state"] == s for t in group)  # noqa: E731
        out.append("| %s | %d of %d | %d | %d | %d |" % (
            ms, count("done"), len(group), count("progress"), count("ready"), count("blocked")))

    for title, state in (("In progress", "progress"), ("Ready to start", "ready")):
        group = [t for t in order if t["state"] == state]
        out += ["", "## %s" % title, ""]
        out += [task_line(t, tasks) for t in group] or ["Nothing."]

    critical = {t["id"] for t in order if t["critical"]}
    if critical:
        out += ["", "## Critical path", "",
                "A delay in one of these tasks delays the final results.", ""]
        out += diagram(tasks, critical, critical_edges(tasks))

    for ms in milestones:
        inside = {t["id"] for t in order if t["milestone"] == ms}
        edges = {(d, i) for i in inside for d in tasks[i]["deps"]}
        linked = {i for e in edges for i in e}
        # Tasks without any dependency link in this milestone are listed, not drawn.
        out += ["", "## %s" % ms, ""]
        if linked:
            outside = sorted(linked - inside)
            if outside:
                out += ["Also shown, from other milestones: %s." % ", ".join(outside), ""]
            out += diagram(tasks, linked, edges)
            out.append("")
        out += ["<details><summary>All %d tasks</summary>" % len(inside), ""]
        for i in sorted(inside):
            t = tasks[i]
            out.append("%s %s" % (STATES[t["state"]][0], task_line(t, tasks)[2:]))
            out.append("")
        out[-1] = ""
        out += ["</details>"]
    return "\n".join(out) + "\n"


def main():
    issues, branches = load()
    tasks, map_issue = build(issues, branches)
    if not tasks:
        sys.exit("no task issues found")
    text = render(tasks)
    if "--update" not in sys.argv:
        sys.stdout.write(text)
        return
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(text)
    if map_issue is None:
        gh(["label", "create", MAP_LABEL, "--color", "5319e7", "--force",
            "--description", "The generated task map issue"])
        print(gh(["issue", "create", "--title", MAP_TITLE, "--label", MAP_LABEL, "--body-file", f.name]).strip())
    elif (map_issue["body"] or "").strip() != text.strip():
        gh(["issue", "edit", str(map_issue["number"]), "--body-file", f.name])
        print("updated #%d" % map_issue["number"])
    else:
        print("no change")


if __name__ == "__main__":
    main()
