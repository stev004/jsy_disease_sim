"""Compare base vs head structure builds per seed.

IDENTICAL = same artifact directory names at every layer, byte-identical non-JSON/MD
files (Parquet etc.), and identical diagnostics.json / benchmark.json after removing
ONLY run-time measurements (runtime_seconds, peak_memory_bytes). Manifests are
provenance records (created_at, code revision, dirty flag, sizes/digests of the
measurement files); they are compared after dropping those fields and any residual
difference is printed for the director to judge.
"""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

MEASURE = {"runtime_seconds", "peak_memory_bytes"}
PROVENANCE = {
    "created_at", "dirty_worktree_flag", "git_commit", "git_sha", "code_revision",
    "source_revision", "m2_manifest_hash", "runtime_seconds", "peak_memory_bytes",
}
MEASURE_FILES = {"diagnostics.json", "diagnostics.md", "benchmark.json", "manifest.json"}


def strip(obj, keys):
    if isinstance(obj, dict):
        return {k: strip(v, keys) for k, v in obj.items() if k not in keys}
    if isinstance(obj, list):
        return [strip(v, keys) for v in obj]
    return obj


def strip_manifest(obj):
    obj = strip(obj, PROVENANCE)
    for key in ("output_artifacts", "artifacts", "files"):
        rows = obj.get(key) if isinstance(obj, dict) else None
        if isinstance(rows, list):
            obj[key] = [
                {k: v for k, v in r.items() if not (
                    any(str(r.get(n, "")).endswith(m) for n in ("path", "name", "file") for m in MEASURE_FILES)
                    and k in {"sha256", "size_bytes"})}
                if isinstance(r, dict) else r
                for r in rows
            ]
    return obj


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def status(side):
    return dict(line.split() for line in Path(f"/tmp/ids-{side}.status").read_text().split("\n") if line.strip())


def main(seeds):
    b, h = status("base"), status("head")
    tally = Counter()
    notes = []
    for s in seeds:
        if b.get(s) != "ok" and h.get(s) == "ok":
            diag = next(Path(f"/tmp/ids-head/{s}").rglob("diagnostics.json"), None)
            disc = []
            for d in Path(f"/tmp/ids-head/{s}").rglob("diagnostics.json"):
                j = json.loads(d.read_text())
                if "private_assignment_residual_fallback" in json.dumps(j):
                    disc.append(d.parent.name)
            tally["FALLBACK"] += 1
            notes.append(f"{s} FALLBACK disclosure_in={disc} status_head_ok")
            continue
        if b.get(s) != "ok":
            tally["BOTH-FAIL" if h.get(s) != "ok" else "?"] += 1
            notes.append(f"{s} BOTH-FAIL")
            continue
        if h.get(s) != "ok":
            tally["REGRESSION"] += 1
            notes.append(f"{s} REGRESSION head failed")
            continue
        bd, hd = Path(f"/tmp/ids-base/{s}"), Path(f"/tmp/ids-head/{s}")
        bf = sorted(p.relative_to(bd) for p in bd.rglob("*") if p.is_file())
        hf = sorted(p.relative_to(hd) for p in hd.rglob("*") if p.is_file())
        diffs = []
        if bf != hf:
            diffs.append(f"file set differs: {set(map(str, bf)) ^ set(map(str, hf))}")
        manifest_residual = []
        for rel in bf:
            if rel not in hf:
                continue
            pb, ph = bd / rel, hd / rel
            if rel.name == "manifest.json":
                a, c = strip_manifest(json.loads(pb.read_text())), strip_manifest(json.loads(ph.read_text()))
                if a != c:
                    manifest_residual.append(str(rel))
            elif rel.name in {"diagnostics.json", "benchmark.json"}:
                if strip(json.loads(pb.read_text()), MEASURE) != strip(json.loads(ph.read_text()), MEASURE):
                    diffs.append(f"{rel} differs beyond measurements")
            elif rel.name == "diagnostics.md":
                la = [l for l in pb.read_text().splitlines() if "untime" not in l and "memory" not in l]
                lc = [l for l in ph.read_text().splitlines() if "untime" not in l and "memory" not in l]
                if la != lc:
                    diffs.append(f"{rel} differs beyond measurement lines")
            elif sha(pb) != sha(ph):
                diffs.append(f"{rel} bytes differ")
        if diffs:
            tally["DIFFERENT"] += 1
            notes.append(f"{s} DIFFERENT {diffs}")
        else:
            tally["IDENTICAL"] += 1
            if manifest_residual:
                tally["manifest_residual"] += 1
                if tally["manifest_residual"] <= 2:
                    bm = strip_manifest(json.loads((bd / manifest_residual[0]).read_text()))
                    hm = strip_manifest(json.loads((hd / manifest_residual[0]).read_text()))
                    keys = [k for k in set(bm) | set(hm) if bm.get(k) != hm.get(k)]
                    notes.append(f"{s} manifest residual keys {keys}: base={[bm.get(k) for k in keys]} head={[hm.get(k) for k in keys]}")
    print("TALLY", dict(tally))
    for n in notes:
        print(n)


if __name__ == "__main__":
    main(sys.argv[1:])
