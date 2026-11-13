"""GitHub Actions ke liye: saare F&O stocks scan karke docs/data.json banata hai."""
import json, os, sys, time, datetime as dt
import requests
from app import fno_stocks, candles, resample, scan, TOKEN, TFS, P

if not TOKEN:
    sys.exit("UPSTOX_TOKEN secret set nahi hai")

# ---- config.json (yahan se base candles / body % / alert settings badlein) ----
cfg = json.load(open("config.json"))
P.update(bases=cfg["bases"], base_max=cfg["base_max_body_pct"],
         leg_min=cfg["leg_min_body_pct"], lookback=cfg["lookback"])
ALERT_TFS, ALERT_PCT = cfg["alert_timeframes"], cfg["alert_distance_pct"]


def trend(df):
    """U = Uptrend (close > EMA20 > EMA50), D = Downtrend (close < EMA20 < EMA50), S = Sideways."""
    c = df["c"].astype(float)
    e20, e50 = c.ewm(span=20, adjust=False).mean().iloc[-1], c.ewm(span=50, adjust=False).mean().iloc[-1]
    return "U" if c.iloc[-1] > e20 > e50 else "D" if c.iloc[-1] < e20 < e50 else "S"


out = {tf: {} for tf in TFS}
trends = {}
cand = {tf: {} for tf in TFS}  # website ko raw candles (zones website khud nikalegi)
stocks = fno_stocks()
print("F&O stocks:", len(stocks), "| bases:", P["bases"])

for n, (sym, key) in enumerate(stocks.items(), 1):
    try:
        d, w, m = candles(key, "days", 2), candles(key, "weeks", 5), candles(key, "months", 15)
        fr = {"Daily": d, "Weekly": w, "Monthly": m}
        if len(m) > 10:
            fr.update({"Quarterly": resample(m, 3), "Half Yearly": resample(m, 6), "Yearly": resample(m, 12)})
        trends[sym] = {tf: trend(fr[tf]) for tf in ("Daily", "Weekly", "Monthly") if len(fr[tf]) > 50}
        for tf, df in fr.items():
            if len(df) > 8:
                z, px = scan(df)
                out[tf][sym] = {"z": z, "px": px}
                cand[tf][sym] = {k: [round(float(x), 2) for x in df[k].values[-125:]] for k in "ohlc"}
    except Exception as e:
        print(sym, "error:", e)
    if n % 20 == 0:
        print(n, "/", len(stocks))
    time.sleep(0.3)

if sum(len(v) for v in out.values()) == 0:
    sys.exit("Koi data nahi mila - token ya API check karein")  # purana data.json bacha rahega

# ---- Alerts: zone ke paas aaya lekin abhi touch nahi hua ----
cur = {}
for tf in ALERT_TFS:
    for sym, v in out.get(tf, {}).items():
        c, h, l = v["px"]
        for zt, z in v["z"].items():
            top, bot, _ = z
            if h >= bot and l <= top:
                continue
            side = c > top if zt == "demand" else c < bot
            dist = (c - top) / c * 100 if c > top else (bot - c) / c * 100
            if side and dist <= ALERT_PCT:
                cur[f"{sym}|{tf}|{zt}|{round(top)}"] = f"{sym} {tf} {zt} zone - {dist:.2f}% away (LTP {c:.2f})"

os.makedirs("docs", exist_ok=True)
try:
    old = set(json.load(open("docs/alerts.json")))
except Exception:
    old = set()
new = [msg for k, msg in cur.items() if k not in old]
topic = os.environ.get("NTFY_TOPIC", "")
if new and topic:
    try:
        requests.post(f"https://ntfy.sh/{topic}", data="\n".join(new).encode("utf-8"),
                      headers={"Title": "Zone Alert", "Priority": "high"}, timeout=20)
        print("Alert sent:", len(new))
    except Exception as e:
        print("ntfy error:", e)
json.dump(sorted(cur), open("docs/alerts.json", "w"))

with open("docs/candles.json", "w") as f:
    json.dump(cand, f, separators=(",", ":"))

ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
with open("docs/data.json", "w") as f:
    json.dump({"updated": dt.datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST"), "total": len(stocks),
               "trend": trends, "alert_tfs": ALERT_TFS, "alert_pct": ALERT_PCT}, f)
print("Done")
