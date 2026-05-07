from flask import Flask, request, jsonify, render_template_string
import pickle
import re

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
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #f4f6f9;
    --surface: #ffffff;
    --border: #d0d8e4;
    --primary: #003366;
    --primary-light: #004d99;
    --primary-dim: rgba(0, 51, 102, 0.08);
    --accent: #0077cc;
    --danger: #c0392b;
    --danger-dim: rgba(192, 57, 43, 0.08);
    --safe: #1a7a3c;
    --safe-dim: rgba(26, 122, 60, 0.08);
    --text: #1a1a2e;
    --muted: #5a6a80;
    --font: 'Times New Roman', Times, serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .top-bar {
    width: 100%;
    background: var(--primary);
    color: white;
    padding: 0.6rem 2rem;
    font-size: 0.85rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .top-bar span { opacity: 0.85; }

  .header-bar {
    width: 100%;
    background: white;
    border-bottom: 3px solid var(--accent);
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }

  .logo-circle {
    width: 52px;
    height: 52px;
    background: var(--primary);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.1rem;
    font-weight: bold;
    flex-shrink: 0;
  }

  .header-bar h2 {
    font-size: 1.1rem;
    color: var(--primary);
    font-weight: bold;
    line-height: 1.3;
  }

  .header-bar p {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 2px;
  }

  .project-banner {
    width: 100%;
    background: linear-gradient(135deg, #003366 0%, #0055a5 100%);
    color: white;
    text-align: center;
    padding: 1.2rem 2rem;
    border-bottom: 3px solid #0077cc;
  }

  .project-banner h1 {
    font-size: 1.25rem;
    font-weight: bold;
    letter-spacing: 0.01em;
    line-height: 1.4;
  }

  .project-banner .project-sub {
    font-size: 0.82rem;
    opacity: 0.8;
    margin-top: 4px;
  }

  .project-tags {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-top: 10px;
    flex-wrap: wrap;
  }

  .tag {
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: white;
  }

  .main {
    width: 100%;
    max-width: 620px;
    padding: 2rem 1rem;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 2rem;
    box-shadow: 0 2px 12px rgba(0,51,102,0.07);
  }

  .card-title {
    font-size: 1.4rem;
    font-weight: bold;
    color: var(--primary);
    margin-bottom: 6px;
    border-bottom: 2px solid var(--accent);
    padding-bottom: 10px;
  }

  .card-sub {
    font-size: 0.9rem;
    color: var(--muted);
    margin-bottom: 1.5rem;
    margin-top: 8px;
  }

  textarea {
    width: 100%;
    background: #f8fafc;
    border: 1.5px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: var(--font);
    font-size: 1rem;
    line-height: 1.7;
    padding: 0.9rem;
    resize: none;
    min-height: 130px;
    transition: border-color 0.2s;
    outline: none;
    margin-bottom: 1rem;
  }

  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: #aab; }

  .btn {
    width: 100%;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 6px;
    font-family: var(--font);
    font-size: 1rem;
    font-weight: bold;
    padding: 0.8rem;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn:hover { background: var(--primary-light); }
  .btn:active { transform: scale(0.99); }

  .result {
    margin-top: 1.2rem;
    border-radius: 6px;
    padding: 1.1rem 1.3rem;
    display: none;
    animation: fadeIn 0.3s ease;
    border-right: 5px solid;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(5px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .result.phishing { background: var(--danger-dim); border-color: var(--danger); }
  .result.legit    { background: var(--safe-dim);   border-color: var(--safe); }

  .result-label { font-size: 1.15rem; font-weight: bold; margin-bottom: 4px; }
  .result.phishing .result-label { color: var(--danger); }
  .result.legit .result-label    { color: var(--safe); }
  .result-desc { font-size: 0.9rem; color: var(--muted); }

  .examples { margin-top: 1.5rem; border-top: 1px solid var(--border); padding-top: 1.2rem; }

  .examples-title {
    font-size: 0.82rem; color: var(--muted); margin-bottom: 0.7rem;
    font-weight: bold; text-transform: uppercase; letter-spacing: 0.06em;
  }

  .example-btn {
    display: block; width: 100%; text-align: right;
    background: #f4f6f9; border: 1px solid var(--border);
    border-radius: 5px; color: var(--text); font-family: var(--font);
    font-size: 0.875rem; padding: 0.55rem 0.85rem;
    cursor: pointer; margin-bottom: 6px; transition: background 0.15s, border-color 0.15s;
  }

  .example-btn:hover { background: var(--primary-dim); border-color: var(--accent); color: var(--primary); }
  .loading { opacity: 0.6; pointer-events: none; }

  .footer {
    width: 100%; background: var(--primary);
    color: rgba(255,255,255,0.7); text-align: center;
    font-size: 0.8rem; padding: 1rem; margin-top: auto;
  }
</style>
</head>
<body>

<div class="header-bar">
  <div class="logo-circle">SEU</div>
  <div>
    <h2>نظام كشف رسائل الاحتيال الإلكتروني</h2>
  </div>
</div>

<div class="project-banner">
  <h1>Arabic Phishing Email Detection Using NLP &amp; ML</h1>
  <div class="project-sub">كشف رسائل الاحتيال الإلكتروني العربية باستخدام معالجة اللغة الطبيعية والتعلم الآلي</div>
  <div class="project-tags">
    <span class="tag">NLP</span>
    <span class="tag">Machine Learning</span>
    <span class="tag">TF-IDF</span>
    <span class="tag">Logistic Regression</span>
    <span class="tag">Python</span>
  </div>
</div>

<div class="main">
  <div class="card">
    <div class="card-title">تحليل الرسالة</div>
    <div class="card-sub">أدخل نص الرسالة المراد فحصها لمعرفة إذا كانت احتيالية أم آمنة</div>

    <textarea id="emailText" placeholder="اكتب أو الصق نص الرسالة هنا..."></textarea>

    <button class="btn" onclick="analyze()">تحليل الرسالة</button>

    <div class="result" id="result">
      <div class="result-label" id="resultLabel"></div>
      <div class="result-desc" id="resultDesc"></div>
    </div>

    <div class="examples">
      <div class="examples-title">أمثلة للتجربة</div>
      <button class="example-btn" onclick="setEx('حسابك البنكي موقوف اضغط هنا لتحديث بياناتك الآن')">⚠ حسابك البنكي موقوف اضغط هنا لتحديث بياناتك</button>
      <button class="example-btn" onclick="setEx('تهانينا فزت بجائزة انقر على الرابط لاستلامها')">⚠ تهانينا فزت بجائزة انقر على الرابط</button>
      <button class="example-btn" onclick="setEx('اجتماع الفريق غداً الساعة التاسعة في قاعة الاجتماعات')">✓ اجتماع الفريق غداً الساعة التاسعة</button>
    </div>
  </div>
</div>

<div class="footer">
  جميع الحقوق محفوظة © 2025 — الجامعة السعودية الإلكترونية
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
      label.textContent = '⚠ Phishing — رسالة احتيالية';
      desc.textContent = 'هذه الرسالة تحتوي على علامات احتيال. لا تضغط على أي رابط أو تشارك بياناتك الشخصية.';
    } else {
      resultDiv.className = 'result legit';
      label.textContent = '✓ Legitimate — رسالة آمنة';
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
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=False)
