import json
import math
import os

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
Z = (-1.644854, -0.67449, 0.0, 0.67449, 1.644854)
HORIZON = 240
HGRID = (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 22, 27, 33,
         40, 50, 62, 76, 92, 110, 130, 155, 185, 210, 240)
PCLIP = 0.0001
RECENT = 180
WIDTH = 0.80
SCALE_MIN = 0.5
SCALE_MAX = 2.6
CASE_MIN_HISTORY = 500
MIN_SAMPLES = 40


def to_u(p):
    q = PCLIP if p < PCLIP else (1.0 - PCLIP if p > 1.0 - PCLIP else p)
    return math.log(q / (1.0 - q))


def to_p(u):
    if u >= 0.0:
        return 1.0 / (1.0 + math.exp(-u))
    e = math.exp(u)
    return e / (1.0 + e)


def pick(ordered, frac):
    n = len(ordered)
    pos = frac * (n - 1)
    lo = int(pos)
    hi = lo + 1 if lo + 1 < n else lo
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def mean_step(series, count):
    n = len(series)
    if n < 2:
        return 0.0
    start = n - count
    if start < 1:
        start = 1
    total = 0.0
    prev = series[start - 1]
    for k in range(start, n):
        cur = series[k]
        total += abs(cur - prev)
        prev = cur
    return total / (n - start)


def shape(u):
    """The market's own h-minute moves, as five quantiles per horizon."""
    n = len(u)
    table = {}
    for h in HGRID:
        if n - h < MIN_SAMPLES:
            continue
        steps = [u[i + h] - u[i] for i in range(n - h)]
        steps.sort()
        table[h] = [pick(steps, t) for t in LEVELS]
    return table


def interp(table, h):
    keys = sorted(table)
    if not keys:
        return None
    lo = keys[0]
    hi = keys[-1]
    for k in keys:
        if k <= h:
            lo = k
        if k >= h:
            hi = k
            break
    if lo == hi:
        return table[lo]
    w = (h - lo) / float(hi - lo)
    return [table[lo][i] * (1.0 - w) + table[hi][i] * w for i in range(5)]


def flat_row(ux, h):
    """Not enough history for any horizon: the house's own random walk."""
    x = to_p(ux)
    r = 0.0025 * math.sqrt(h)
    row = []
    for z in Z:
        v = x + z * r
        row.append(round(0.0 if v < 0.0 else (1.0 if v > 1.0 else v), 6))
    return row


def market_rows(u, ratio):
    table = shape(u)
    ux = u[-1]
    rows = []
    for h in range(1, HORIZON + 1):
        base = interp(table, h)
        if base is None:
            rows.append(flat_row(ux, h))
            continue
        mid = base[2]
        row = []
        prev = 0.0
        for i in range(5):
            v = to_p(ux + (base[i] - mid) * ratio * WIDTH)
            if v < prev:
                v = prev
            row.append(round(v, 6))
            prev = v
        rows.append(row)
    return rows


def clamp(v):
    return SCALE_MIN if v < SCALE_MIN else (SCALE_MAX if v > SCALE_MAX else v)


def main():
    src = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    dst = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    for name in sorted(f for f in os.listdir(src) if f.endswith(".in")):
        with open(os.path.join(src, name), encoding="utf-8") as f:
            case = json.load(f)
        markets = []
        for market in case["markets"]:
            u = [to_u(p) for p in market["prices"]]
            base = mean_step(u, len(u))
            own = mean_step(u, RECENT) / base if base > 1e-9 else 1.0
            markets.append({"id": market["id"], "u": u, "own": own})
        long = sorted(o["own"] for o in markets if len(o["u"]) >= CASE_MIN_HISTORY)
        common = pick(long, 0.5) if long else 1.0
        out = {"forecasts": []}
        for o in markets:
            ratio = clamp(math.sqrt(o["own"] * common))
            out["forecasts"].append({"id": o["id"], "q": market_rows(o["u"], ratio)})
        with open(os.path.join(dst, name[:-3] + ".out"), "w", encoding="utf-8") as f:
            json.dump(out, f, separators=(",", ":"))


main()
