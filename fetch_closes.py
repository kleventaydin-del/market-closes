"""Writes daily closes for the Daily Markets Brief to closes.csv and latest.json."""
import json, sys, time, datetime as dt
import yfinance as yf

# label -> Yahoo symbol
SYMBOLS = {
    "QQQ": "QQQ", "NASDAQ100": "^NDX", "NASDAQ_COMP": "^IXIC", "SP500": "^GSPC",
    "VIX": "^VIX", "US10Y": "^TNX", "BRENT": "BZ=F", "USDTRY": "USDTRY=X",
    "BIST100": "XU100.IS", "XBANK": "XBANK.IS",
    "KCHOL": "KCHOL.IS", "THYAO": "THYAO.IS", "MGROS": "MGROS.IS",
}

def fetch(symbol, tries=4):
    for i in range(tries):
        try:
            h = yf.Ticker(symbol).history(period="1mo", interval="1d", auto_adjust=False)
            h = h.dropna(subset=["Close"])
            if len(h):
                return h
        except Exception as e:
            print(f"{symbol}: attempt {i+1} failed: {e}", file=sys.stderr)
        time.sleep(3 * (i + 1))
    return None

rows, latest, failed = [], {}, []
for label, sym in SYMBOLS.items():
    h = fetch(sym)
    if h is None:
        failed.append(label)
        continue
    h = h.tail(12)
    for d, r in h.iterrows():
        rows.append((label, sym, d.strftime("%Y-%m-%d"), round(float(r["Close"]), 4)))
    last, prev = h.iloc[-1], (h.iloc[-2] if len(h) > 1 else None)
    latest[label] = {
        "symbol": sym,
        "date": h.index[-1].strftime("%Y-%m-%d"),
        "close": round(float(last["Close"]), 4),
        "prev_close": round(float(prev["Close"]), 4) if prev is not None else None,
        "change_pct": round((float(last["Close"]) / float(prev["Close"]) - 1) * 100, 2) if prev is not None else None,
    }
    time.sleep(1)

with open("closes.csv", "w", encoding="utf-8") as f:
    f.write("label,symbol,date,close\n")
    for r in rows:
        f.write(",".join(map(str, r)) + "\n")
with open("latest.json", "w", encoding="utf-8") as f:
    json.dump({"generated_utc": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
               "note": "End-of-day closes from Yahoo Finance; check each date before use.",
               "failed": failed, "latest": latest}, f, indent=1, ensure_ascii=False)
print("failed:", failed)
sys.exit(1 if len(failed) == len(SYMBOLS) else 0)
