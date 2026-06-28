import hashlib, os, smtplib, requests, re
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import subprocess

URL = "https://select-type.com/rsv/?id=jA_3bzej9I8&c_id=404251"
NOTIFY_EMAIL = "shinoyan1@gmail.com"
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_PASS"]
LAST_HASH = os.environ.get("LAST_HASH", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "")

def get_page_text():
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    res = requests.get(URL, headers=headers, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    for tag in soup(["script", "style", "meta", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', '', text)
    return text

def send_email(body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "【予約開始】巨大とうもろこし迷路の予約が変化しました！"
    msg["From"] = GMAIL_USER
    msg["To"] = NOTIFY_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)

def update_secret(new_hash):
    subprocess.run(
        ["gh", "secret", "set", "LAST_HASH", "--body", new_hash, "--repo", REPO],
        check=True,
        env={**os.environ, "GH_TOKEN": GITHUB_TOKEN}
    )

text = get_page_text()
new_hash = hashlib.sha256(text.encode()).hexdigest()

print(f"前回ハッシュ: {LAST_HASH[:16] or '(初回)'}...")
print(f"今回ハッシュ: {new_hash[:16]}...")

if "準備中" in text:
    print("📋 ステータス: まだ準備中")
else:
    print("🎉 予約開始の可能性！")

if LAST_HASH and LAST_HASH != new_hash:
    body = f"""巨大とうもろこし迷路の予約ページに変化がありました！

URL: {URL}

{'⚠️ 「準備中」表示が消えました！今すぐ予約を！' if '準備中' not in text else 'ページに変化がありました。確認してください。'}
"""
    send_email(body)
    print("✅ メール送信完了")
elif not LAST_HASH:
    print("📝 初回実行：ハッシュを保存します")

if new_hash != LAST_HASH:
    update_secret(new_hash)
    print("✅ ハッシュ更新完了")
else:
    print("変化なし。")
