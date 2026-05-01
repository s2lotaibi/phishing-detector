from flask import Flask, request, jsonify, render_template_string
import pickle
import re
import os

app = Flask(__name__)

model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

def clean_text(text):
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^\u0600-\u06FF\s]", "", text)
    text = text.strip()
    return text

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>كاشف رسائل الاحتيال</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --border: #1e1e2e;
    --accent: #e63946;
    --accent-dim: rgba(230,57,70,0.12);
    --safe: #2dc653;
    --safe-dim: rgba(45,198,83,0.12);
    --text: #f0eff4;
    --muted: #6b6b80;
    --font: 'IBM Plex Sans Arabic', sans-serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }

  body::before {
    content: '';
    position: fixed;
    top: -50%;
    right: -20%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(230,57,70,0.06) 0%, transparent 70%);
    pointer-events: none;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2.5rem;
    width: 100%;
    max-width: 560px;
  }

  .header { margin-bottom: 2rem; }

  .header h1 {
    font-size: 1.6rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.2;
  }

  .header h1 span { color: var(--accent); }

  .header p {
    color: var(--muted);
    font-size: 0.9rem;
    margin-top: 6px;
    font-weight: 300;
  }

  .input-wrap { position: relative; margin-bottom: 1rem; }

  textarea {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text);
    font-family: var(--font);
    font-size: 1rem;
    line-height: 1.7;
    padding: 1rem;
    resize: none;
    min-height: 140px;
    transition: border-color 0.2s;
    outline: none;
  }

  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--muted); }

  .btn {
    width: 100%;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 10px;
    font-family: var(--font);
    font-size: 1rem;
    font-weight: 500;
    padding: 0.85rem;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.1s;
  }

  .btn:hover { opacity: 0.88; }
  .btn:active { transform: scale(0.99); }

  .result {
    margin-top: 1.5rem;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    display: none;
    animation: fadeIn 0.3s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .result.phishing {
    background: var(--accent-dim);
    border: 1px solid rgba(230,57,70,0.3);
  }

  .result.legit {
    background: var(--safe-dim);
    border: 1px solid rgba(45,198,83,0.3);
  }

  .result-label {
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 4px;
  }

  .result.phishing .result-label { color: var(--accent); }
  .result.legit .result-label { color: var(--safe); }

  .result-desc {
    font-size: 0.875rem;
    color: var(--muted);
    font-weight: 300;
  }

  .examples {
    margin-top: 2rem;
    border-top: 1px solid var(--border);
    padding-top: 1.5rem;
  }

  .examples p {
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .example-btn {
    display: block;
    width: 100%;
    text-align: right;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--muted);
    font-family: var(--font);
    font-size: 0.875rem;
    padding: 0.6rem 0.9rem;
    cursor: pointer;
    margin-bottom: 6px;
    transition: background 0.15s, color 0.15s;
  }

  .example-btn:hover {
    background: var(--border);
    color: var(--text);
  }

  .loading { opacity: 0.6; pointer-events: none; }
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>كاشف رسائل <span>الاحتيال</span></h1>
    <p>أدخل نص الرسالة لمعرفة إذا كانت احتيالية أو آمنة</p>
  </div>

  <div class="input-wrap">
    <textarea id="emailText" placeholder="اكتب نص الرسالة هنا..."></textarea>
  </div>

  <button class="btn" onclick="analyze()">تحليل الرسالة</button>

  <div class="result" id="result">
    <div class="result-label" id="resultLabel"></div>
    <div class="result-desc" id="resultDesc"></div>
  </div>

  <div class="examples">
    <p>أمثلة للتجربة</p>
    <button class="example-btn" onclick="setEx('حسابك البنكي موقوف اضغط هنا لتحديث بياناتك الآن')">⚠ حسابك البنكي موقوف اضغط هنا لتحديث بياناتك</button>
    <button class="example-btn" onclick="setEx('تهانينا فزت بجائزة انقر على الرابط لاستلامها')">⚠ تهانينا فزت بجائزة انقر على الرابط</button>
    <button class="example-btn" onclick="setEx('اجتماع الفريق غداً الساعة التاسعة في قاعة الاجتماعات')">✓ اجتماع الفريق غداً الساعة التاسعة</button>
  </div>
</div>

<script>
function setEx(t) {
  document.getElementById('emailText').value = t;
  document.getElementById('result').style.display = 'none';
}

async function analyze() {
  const text = document.getElementById('emailText').value.trim();
  if (!text) return;

  const btn = document.querySelector('.btn');
  btn.classList.add('loading');
  btn.textContent = 'جاري التحليل...';

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();

    const resultDiv = document.getElementById('result');
    const label = document.getElementById('resultLabel');
    const desc = document.getElementById('resultDesc');

    if (data.prediction === 'phishing') {
      resultDiv.className = 'result phishing';
      label.textContent = 'Phishing — رسالة احتيالية';
      desc.textContent = 'هذه الرسالة تحتوي على علامات احتيال. لا تضغط على أي رابط أو تشارك بياناتك.';
    } else {
      resultDiv.className = 'result legit';
      label.textContent = 'Legitimate — رسالة آمنة';
      desc.textContent = 'هذه الرسالة تبدو طبيعية وآمنة.';
    }
    resultDiv.style.display = 'block';
  } catch(e) {
    alert('حدث خطأ، تأكد أن الخادم شغال');
  } finally {
    btn.classList.remove('loading');
    btn.textContent = 'تحليل الرسالة';
  }
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data.get("text", "")
    cleaned = clean_text(text)
    vector = vectorizer.transform([cleaned])
    prediction = model.predict(vector)[0]
    return jsonify({"prediction": prediction})

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://localhost:5000")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
