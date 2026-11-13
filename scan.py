"""GitHub Actions ke liye: saare F&O stocks scan karke docs/data.json banata hai."""
import json, os, sys, time, datetime as dt
from app import fno_stocks, candles, resample, scan, TOKEN, TFS

if not TOKEN:
    sys.exit("UPSTOX_TOKEN secret set nahi hai")

out = {tf: {} for tf in TFS}
stocks = fno_stocks()
print("F&O stocks:", len(stocks))

for n, (sym, key) in enumerate(stocks.items(), 1):
    try:
        d, w, m = candles(key, "days", 2), candles(key, "weeks", 5), candles(key, "months", 15)
        fr = {"Daily": d, "Weekly": w, "Monthly": m}
        if len(m) > 10:
            fr.update({"Quarterly": resample(m, 3), "Half Yearly": resample(m, 6), "Yearly": resample(m, 12)})
        for tf, df in fr.items():
            if len(df) > 8:
                z, px = scan(df)
                out[tf][sym] = {"z": z, "px": px}
    except Exception as e:
        print(sym, "error:", e)
    if n % 20 == 0:
        print(n, "/", len(stocks))
    time.sleep(0.3)

if sum(len(v) for v in out.values()) == 0:
    sys.exit("Koi data nahi mila - token ya API check karein")  # purana data.json bacha rahega

ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
os.makedirs("docs", exist_ok=True)
with open("docs/data.json", "w") as f:
    json.dump({"updated": dt.datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST"),
               "total": len(stocks), "zones": out}, f)
print("Done")
