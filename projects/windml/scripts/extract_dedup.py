"""Extract a Greenbyte SCADA zip, collapsing the duplicated rows found in the 2023/2024 Cubico exports.
In those Turbine_Data files each 10-minute timestamp appears up to ~80x: one full row (~300 values), one sparse
row repeating 9 availability/EFLH columns, and many all-'NaN' rows. Rule: per timestamp keep the line with the
most non-NaN values; every other line's non-NaN values are checked against it (conflicts counted in the log and
the conflicting line is kept too). Comment/header lines and Status files are untouched.
Writes <dest>/<member> and <dest>/_dedup_log.json. Usage: extract_dedup.py ZIP DEST"""
import io, json, os, sys, zipfile
zp, dest = sys.argv[1], sys.argv[2]
os.makedirs(dest, exist_ok=True)
logp = os.path.join(dest, "_dedup_log.json")
log = json.load(open(logp)) if os.path.exists(logp) else {}
def vals(line):
    return line.rstrip("\r\n").split(",")
with zipfile.ZipFile(zp) as z:
    for m in z.namelist():
        name = os.path.basename(m)
        if not name: continue
        out = os.path.join(dest, name)
        if not name.startswith("Turbine_Data_"):
            with z.open(m) as src, open(out, "wb") as dst:
                dst.write(src.read())
            continue
        header, best, others, order = [], {}, {}, []
        n_in = 0
        with z.open(m) as fh:
            for line in io.TextIOWrapper(fh, encoding="utf-8"):
                if line.startswith("#") or not line.strip():
                    header.append(line); continue
                n_in += 1
                v = vals(line); ts = v[0]; cnt = sum(x not in ("NaN", "") for x in v[1:])
                if ts not in best:
                    best[ts] = (cnt, line); order.append(ts); continue
                if line == best[ts][1]: continue
                if cnt > best[ts][0]:
                    others.setdefault(ts, []).append(best[ts][1]); best[ts] = (cnt, line)
                elif cnt > 0:
                    others.setdefault(ts, []).append(line)
        conflicts, extra = 0, []
        for ts, lines in others.items():
            b = vals(best[ts][1])
            for l in set(lines):
                o = vals(l)
                if len(o) != len(b) or any(x not in ("NaN", "") and x != y for x, y in zip(o[1:], b[1:])):
                    conflicts += 1; extra.append(l)
        with open(out, "w", encoding="utf-8") as dst:
            dst.writelines(header)
            for ts in order: dst.write(best[ts][1])
            dst.writelines(extra)
        n_out = len(order) + len(extra)
        log[name] = {"data_lines_in": n_in, "data_lines_out": n_out, "dropped": n_in - n_out,
                     "timestamps": len(order), "conflicting_lines_kept": conflicts}
        print(name, log[name], flush=True)
        del best, others
json.dump(log, open(logp, "w"), indent=1)
