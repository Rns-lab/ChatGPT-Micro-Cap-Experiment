import os, json, sys, requests
import pandas as pd
from pathlib import Path

def send(text):
    tok=os.getenv("TELEGRAM_BOT_TOKEN"); chat=os.getenv("TELEGRAM_CHAT_ID")
    if not tok or not chat: return
    url=f"https://api.telegram.org/bot{tok}/sendMessage"
    requests.post(url, json={"chat_id":chat,"text":text[:4000],"parse_mode":"HTML"}, timeout=15)

def summarize():
    csvs = sorted(Path(".").rglob("*.csv"), key=lambda p: p.stat().st_mtime)
    if not csvs:
        return "❌ Nessun CSV trovato, impossibile creare il report."
    latest = csvs[-1]
    try:
        df = pd.read_csv(latest)
    except Exception as e:
        return f"❌ Lettura CSV fallita ({latest.name}): {e}"

    # Adatta ai nomi colonne più comuni
    col_profit = None
    for c in ["Profit","PnL","P&L","profit","pnl"]:
        if c in df.columns:
            col_profit = c; break
    if col_profit is None:
        return f"❌ Colonna PnL/Profit non trovata in {latest.name}."

    s = df[col_profit].fillna(0)
    pnl = float(s.sum())
    trades = int(s.shape[0])
    eq_curve = s.cumsum()
    eq = float(eq_curve.iloc[-1]) if trades else 0.0
    dd_series = (eq_curve.cummax() - eq_curve)
    dd = float(dd_series.max()) if trades else 0.0
    win_rate = float((s > 0).mean() * 100) if trades else 0.0
    sharpe = float((s.mean() / (s.std() + 1e-9)) * (252 ** 0.5)) if trades>1 else 0.0

    msg = (
        "📊 <b>Report giornaliero - Paper Mode</b>\n"
        f"Ultimo file: <code>{latest.name}</code>\n\n"
        f"💰 Profitto totale: <b>{pnl:.2f}</b>\n"
        f"📈 Sharpe ratio: <b>{sharpe:.2f}</b>\n"
        f"📉 Max Drawdown: <b>{dd:.2f}</b>\n"
        f"⚔️ Win rate: <b>{win_rate:.1f}%</b>\n"
        f"🧾 Numero trade: <b>{trades}</b>\n"
        f"🏦 Equity finale (cum PnL): <b>{eq:.2f}</b>"
    )
    return msg

if __name__ == "__main__":
    try:
        send(summarize())
    except Exception as e:
        send(f"❌ Errore report Telegram: {e}")
