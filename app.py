from flask import Flask, render_template, jsonify
import random
import math
from datetime import datetime, timedelta

app = Flask(__name__)

def generate_stock_data():
    dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    rsis, macds, ma20s, ma50s = [], [], [], []
    start = datetime(2019, 1, 2)
    price = 142.0
    for i in range(1500):
        d = start + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        change = random.gauss(0.03, 1.2)
        open_p = round(price + random.gauss(0, 0.3), 2)
        close_p = round(open_p + change, 2)
        high_p = round(max(open_p, close_p) + abs(random.gauss(0, 0.5)), 2)
        low_p = round(min(open_p, close_p) - abs(random.gauss(0, 0.5)), 2)
        vol = int(random.gauss(2000000, 800000))
        rsi = round(random.uniform(30, 70), 2)
        macd = round(random.gauss(0, 1), 2)
        ma20 = round(close_p + random.gauss(0, 2), 2)
        ma50 = round(close_p + random.gauss(0, 3), 2)
        dates.append(d.strftime("%Y-%m-%d"))
        opens.append(open_p); highs.append(high_p); lows.append(low_p)
        closes.append(close_p); volumes.append(max(vol, 500000))
        rsis.append(rsi); macds.append(macd); ma20s.append(ma20); ma50s.append(ma50)
        price = close_p
        if len(dates) >= 1508:
            break
    return dates, opens, highs, lows, closes, volumes, rsis, macds, ma20s, ma50s

def generate_sentiment_data(dates):
    headlines_pos = [
        "Company reports strong quarterly earnings, stock jumps 8%",
        "New product launch receives positive reviews",
        "Partnership announcement boosts investor confidence",
        "Analysts upgrade stock rating to buy",
        "Revenue growth exceeds market expectations",
        "Record breaking sales quarter announced",
        "CEO unveils ambitious expansion strategy",
    ]
    headlines_neg = [
        "Market uncertainty due to inflation concerns",
        "Regulatory challenges impact market sentiment",
        "Supply chain issues affect production",
        "Competitor launches similar product",
        "Analysts downgrade stock on growth concerns",
        "Rising costs pressure profit margins",
        "Global slowdown fears weigh on markets",
    ]
    headlines_neu = [
        "Company announces routine board meeting",
        "Stock trades sideways amid mixed signals",
        "Market watchers await Fed decision",
        "Quarterly report in line with estimates",
    ]
    news_rows = []
    for d in dates[-30:]:
        r = random.random()
        if r > 0.55:
            h = random.choice(headlines_pos)
            s = "Positive"
            sc = round(random.uniform(0.4, 0.85), 2)
        elif r > 0.14:
            h = random.choice(headlines_neu)
            s = "Neutral"
            sc = round(random.uniform(-0.05, 0.15), 2)
        else:
            h = random.choice(headlines_neg)
            s = "Negative"
            sc = round(random.uniform(-0.75, -0.25), 2)
        news_rows.append({"date": d, "headline": h, "sentiment": s, "score": sc})

    compound_scores = [round(random.gauss(0.186, 0.3), 3) for _ in dates]
    total = len(dates)
    pos_count = int(total * 0.447)
    neu_count = int(total * 0.411)

    return {
        "compound_scores": compound_scores,
        "news_rows": news_rows[:10],
        "total": total,
        "pos_count": pos_count,
        "neu_count": neu_count,
        "avg_compound": 0.186,
    }

def generate_predictions(closes, dates):
    predicted = []
    for c in closes:
        noise = random.gauss(0, 2.5)
        predicted.append(round(c + noise, 2))
    test_start = int(len(closes) * 0.85)
    actual_test = closes[test_start:]
    pred_test = predicted[test_start:]
    dates_test = dates[test_start:]
    errors = [round(p - a, 2) for a, p in zip(actual_test, pred_test)]
    mae = round(sum(abs(e) for e in errors) / len(errors), 2)
    rmse = round(math.sqrt(sum(e**2 for e in errors) / len(errors)), 2)
    mape = round(sum(abs(e/a) for e, a in zip(errors, actual_test)) / len(errors) * 100, 2)
    ss_res = sum((a - p)**2 for a, p in zip(actual_test, pred_test))
    ss_tot = sum((a - sum(actual_test)/len(actual_test))**2 for a in actual_test)
    r2 = round(1 - ss_res/ss_tot, 3)
    last_price = closes[-1]
    future_dates, future_prices = [], []
    fp = last_price
    for i in range(30):
        fd = datetime(2024, 12, 31) + timedelta(days=i+1)
        if fd.weekday() < 5:
            fp = round(fp + random.gauss(0.8, 1.5), 2)
            future_dates.append(fd.strftime("%Y-%m-%d"))
            future_prices.append(fp)
    return {
        "all_dates": dates, "all_actual": closes, "all_predicted": predicted,
        "test_dates": dates_test, "actual_test": actual_test, "pred_test": pred_test,
        "mae": mae, "rmse": rmse, "mape": mape, "r2": r2, "errors": errors,
        "future_dates": future_dates, "future_prices": future_prices,
        "last_price": last_price, "pred_price": future_prices[-1] if future_prices else last_price,
    }

dates, opens, highs, lows, closes, volumes, rsis, macds, ma20s, ma50s = generate_stock_data()
sentiment_data = generate_sentiment_data(dates)
prediction_data = generate_predictions(closes, dates)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dashboard")
def api_dashboard():
    sample = [{"date": dates[i], "open": opens[i], "high": highs[i],
               "low": lows[i], "close": closes[i], "volume": volumes[i],
               "rsi": rsis[i], "macd": macds[i], "ma20": ma20s[i], "ma50": ma50s[i]}
              for i in range(5)]
    return jsonify({"records": len(dates), "features": 7,
                    "start_date": dates[0], "end_date": dates[-1],
                    "dates": dates, "closes": closes, "volumes": volumes, "sample": sample})

@app.route("/api/sentiment")
def api_sentiment():
    return jsonify({**sentiment_data, "dates": dates})

@app.route("/api/predictions")
def api_predictions():
    return jsonify(prediction_data)

@app.route("/api/evaluation")
def api_evaluation():
    actual = prediction_data["actual_test"]
    pred = prediction_data["pred_test"]
    scatter = [{"actual": round(a, 2), "predicted": round(p, 2)}
               for a, p in zip(actual[::2], pred[::2])]
    hist_data = {}
    for e in prediction_data["errors"]:
        bucket = round(e)
        hist_data[bucket] = hist_data.get(bucket, 0) + 1
    hist = [{"error": k, "count": v} for k, v in sorted(hist_data.items())]
    return jsonify({"mae": prediction_data["mae"], "rmse": prediction_data["rmse"],
                    "mape": prediction_data["mape"], "r2": prediction_data["r2"],
                    "scatter": scatter, "histogram": hist})

@app.route("/api/future")
def api_future():
    last_price = prediction_data["last_price"]
    pred_price = prediction_data["pred_price"]
    change_pct = round((pred_price - last_price) / last_price * 100, 2)
    return jsonify({"hist_dates": dates[-20:], "hist_prices": closes[-20:],
                    "future_dates": prediction_data["future_dates"],
                    "future_prices": prediction_data["future_prices"],
                    "last_price": last_price, "pred_price": pred_price,
                    "change_pct": change_pct,
                    "ci_low": round(pred_price * 0.955, 2),
                    "ci_high": round(pred_price * 1.045, 2),
                    "avg_sentiment": 0.186, "sentiment_impact": 2.35})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
