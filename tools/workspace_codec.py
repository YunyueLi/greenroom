#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""greenroom workspace codec — markdown 工作台文件夹 ⇄ JSON 数据块 互转。

为什么存在：docs/workspace-spec.md 规定的工作台是一个 md 文件夹。客户端要把它装进
数据库、浏览器存储或者自己的应用，需要一个稳定的块结构；导出时又要能一字不差地还原
成文件夹。这个 codec 就是两边的桥，任何按契约实现的客户端都可以拿去做导入导出。

数据块模型（与 docs/workspace-spec.md 对齐）:
  blocks = {
    "profile": {profile, resume, storyBank},   # 核心身份块：简历+经历+档案，每个岗都取料
    "library": [ {group, name, path, content} ],# 工作台里出现的资料文件，与 profile 分开
    "jobs":    [ {slug, meta, job, intel, script, rounds[], extra[]} ],  # 一岗一块
    "extra":   [ {path, content} ],             # 未归类的顶层 md，绝不丢
    "assets":  [ path ]                          # 二进制引用（pdf 等），只记路径不入块
  }

无损原则：每个槽位存**原始 md 全文**（frontmatter+正文原样），blocks→folder 字节级还原；
meta 是从 job.md frontmatter 解析出来的便捷副本（给客户端快速展示），不作为回写真源。

用法:
  python3 tools/workspace_codec.py <workspace-dir>           # 跑 round-trip 自测并报告
  python3 tools/workspace_codec.py <workspace-dir> --emit    # 打印 blocks JSON（资料/正文截断预览）
"""
import os
import re
import sys
import json
import tempfile

JOB_META_KEYS = ("company", "role", "status", "source", "domain", "logo", "updated")


def split_frontmatter(raw):
    """返回 (fm: dict, body: str)。最小 YAML：顶部 --- 包裹的 key: value 平铺标量。
    只认平铺标量，value 按第一个冒号切（兼容 URL）。"""
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            block = raw[3:end]
            rest = raw[end + 4:]
            if rest.startswith("\n"):
                rest = rest[1:]
            fm = {}
            for line in block.split("\n"):
                s = line.strip()
                if not s or s.startswith("#") or ":" not in s:
                    continue
                k, v = s.split(":", 1)
                fm[k.strip()] = v.strip()
            return fm, rest
    return {}, raw


def _first_h1(body):
    m = re.search(r"^#\s+(.*)$", body, re.M)
    return m.group(1).strip() if m else None


def _round_no(fm, name):
    """轮次号：先 fm.round 取数字，再文件名里第一个数字，最后 0。"""
    if fm.get("round"):
        digits = re.sub(r"\D", "", str(fm["round"]))
        if digits:
            return int(digits)
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 0


def _job_file_type(fm, rest):
    """镜像 buildWorkspace：frontmatter type 优先，否则按文件名推断。"""
    if fm.get("type"):
        return fm["type"]
    base = rest.rsplit("/", 1)[-1]
    if base == "job.md":
        return "job"
    if base == "intel.md":
        return "intel"
    if base == "script.md":
        return "script"
    if "debrief" in rest:
        return "debrief"
    if "mock" in rest:
        return "mock"
    if "prep" in rest:
        return "round-prep"
    return "doc"


def _iter_md(root):
    """yield (相对 posix 路径, 原始文本)。跳过任何以点开头的路径段（.git/.DS_Store 等）。"""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            if fn.startswith("."):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            yield rel, full


def _resolve_root(root):
    """rebase：若 root 本身不含 profile.md/jobs/，但唯一子目录含，则下探一层。"""
    def looks_like_ws(p):
        return os.path.isdir(os.path.join(p, "jobs")) or os.path.isfile(os.path.join(p, "profile.md"))
    if looks_like_ws(root):
        return root
    subs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith(".")]
    if len(subs) == 1 and looks_like_ws(os.path.join(root, subs[0])):
        return os.path.join(root, subs[0])
    return root


def folder_to_blocks(root):
    root = _resolve_root(root)
    blocks = {"profile": {"profile": None, "resume": None, "storyBank": None},
              "library": [], "jobs": [], "extra": [], "assets": []}
    jobs_map = {}
    profile_updates, job_updates = [], {}

    for rel, full in _iter_md(root):
        if not rel.endswith(".md"):
            blocks["assets"].append(rel)
            continue
        with open(full, encoding="utf-8") as f:
            raw = f.read()
        fm, body = split_frontmatter(raw)
        slot = {"path": rel, "content": raw}

        lm = re.match(r"^library/(.+)\.md$", rel)
        if lm:
            sub = lm.group(1)
            group = sub.split("/")[0] if "/" in sub else "通用"
            name = fm.get("title") or _first_h1(body) or sub.rsplit("/", 1)[-1]
            blocks["library"].append({"group": group, "name": name, "path": rel,
                                      "content": raw, "updated": fm.get("updated")})
            continue

        jm = re.match(r"^jobs/([^/]+)/(.*)$", rel)
        if jm:
            slug, rest = jm.group(1), jm.group(2)
            job = jobs_map.get(slug)
            if job is None:
                job = jobs_map[slug] = {"slug": slug, "meta": {}, "job": None,
                                        "intel": None, "script": None, "rounds": [], "extra": []}
                job_updates[slug] = []
            t = _job_file_type(fm, rest)
            if t == "job":
                job["job"] = slot
                job["meta"] = {k: fm[k] for k in JOB_META_KEYS if k in fm}
            elif t == "intel":
                job["intel"] = slot
            elif t == "script":
                job["script"] = slot
            else:
                job["rounds"].append({"type": t, "round": _round_no(fm, rest),
                                      "path": rel, "content": raw})
            if fm.get("updated"):
                job_updates[slug].append(fm["updated"])
            continue

        # 顶层文件
        t = fm.get("type") or {"profile.md": "profile", "resume.md": "resume",
                               "story-bank.md": "story-bank"}.get(rel, "md")
        if t == "profile":
            blocks["profile"]["profile"] = slot
        elif t == "resume":
            blocks["profile"]["resume"] = slot
        elif t == "story-bank":
            blocks["profile"]["storyBank"] = slot
        else:
            blocks["extra"].append(slot)
        if fm.get("updated"):
            profile_updates.append(fm["updated"])

    for slug, job in jobs_map.items():
        job["rounds"].sort(key=lambda r: (r["round"],
                           {"round-prep": 0, "mock": 1, "debrief": 2, "doc": 3}.get(r["type"], 9)))
        ups = job_updates.get(slug) or []
        if ups:
            job["updatedAt"] = max(ups)
        blocks["jobs"].append(job)
    blocks["jobs"].sort(key=lambda j: j.get("meta", {}).get("updated", ""), reverse=True)
    if profile_updates:
        blocks["profile"]["updatedAt"] = max(profile_updates)
    blocks["assets"].sort()
    return blocks


def blocks_to_folder(blocks, out_dir):
    """把块里所有文本槽位按原路径写回（字节还原）。二进制 assets 只是引用，不在此还原。"""
    written = []

    def write(slot):
        if not slot:
            return
        path = os.path.join(out_dir, slot["path"].replace("/", os.sep))
        os.makedirs(os.path.dirname(path) or out_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(slot["content"])
        written.append(slot["path"])

    p = blocks.get("profile", {})
    for key in ("profile", "resume", "storyBank"):
        write(p.get(key))
    for item in blocks.get("library", []):
        write(item)
    for job in blocks.get("jobs", []):
        for key in ("job", "intel", "script"):
            write(job.get(key))
        for r in job.get("rounds", []):
            write(r)
        for e in job.get("extra", []):
            write(e)
    for e in blocks.get("extra", []):
        write(e)
    return written


def _collect_md(root):
    out = {}
    for rel, full in _iter_md(root):
        if rel.endswith(".md"):
            with open(full, encoding="utf-8") as f:
                out[rel] = f.read()
    return out


def round_trip_test(root):
    root = _resolve_root(root)
    src = _collect_md(root)
    blocks = folder_to_blocks(root)
    tmp = tempfile.mkdtemp(prefix="gr-codec-")
    try:
        blocks_to_folder(blocks, tmp)
        out = _collect_md(tmp)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    src_paths, out_paths = set(src), set(out)
    missing = sorted(src_paths - out_paths)   # 源里有、回写丢了
    extra = sorted(out_paths - src_paths)     # 回写多出来的
    changed = sorted(p for p in (src_paths & out_paths) if src[p] != out[p])
    ok = not (missing or extra or changed)

    print("=" * 60)
    print(f"工作台: {root}")
    print(f"profile: " + ", ".join(k for k in ("profile", "resume", "storyBank")
          if blocks["profile"].get(k)) or "（空）")
    print(f"library: {len(blocks['library'])} 篇  |  jobs: {len(blocks['jobs'])} 个  |  "
          f"顶层 extra: {len(blocks['extra'])}  |  二进制 assets: {len(blocks['assets'])}")
    for j in blocks["jobs"]:
        bits = [k for k in ("intel", "script") if j.get(k)]
        print(f"  · {j['slug']}: job{'+' + '+'.join(bits) if bits else ''}"
              f"  rounds={len(j['rounds'])}"
              + (f"  ({', '.join(r['type'] + str(r['round']) for r in j['rounds'])})" if j["rounds"] else ""))
    print("-" * 60)
    print(f"round-trip 共 {len(src)} 个 .md：", "✓ 全部字节级一致" if ok else "✗ 有差异")
    for p in missing:
        print(f"   缺失: {p}")
    for p in extra:
        print(f"   多出: {p}")
    for p in changed:
        print(f"   内容变了: {p}")
    print("=" * 60)
    return ok


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    root = argv[1]
    if not os.path.isdir(root):
        print(f"目录不存在: {root}")
        return 2
    if "--emit" in argv:
        blocks = folder_to_blocks(root)

        def trunc(o, n=200):
            if isinstance(o, dict):
                return {k: trunc(v, n) for k, v in o.items()}
            if isinstance(o, list):
                return [trunc(x, n) for x in o]
            if isinstance(o, str) and len(o) > n:
                return o[:n] + f"…（{len(o)} 字）"
            return o
        print(json.dumps(trunc(blocks), ensure_ascii=False, indent=2))
        return 0
    return 0 if round_trip_test(root) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
