import time
import sqlite3
import requests
from bs4 import BeautifulSoup

# 1. SQLiteデータベースの準備
conn = sqlite3.connect("google_repos.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS repositories")
cur.execute("""
    CREATE TABLE repositories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        language TEXT,
        stars TEXT
    )
""")

# 2. スクレイピング処理（全ページ取得）
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

page = 1
while True:
    url = f"https://github.com/orgs/google/repositories?page={page}"
    print(f"Fetching page {page}...")
    
    response = requests.get(url, headers=headers)
    time.sleep(1)  # 課題必須: 1秒待機
    
    if response.status_code != 200:
        print(f"Status code {response.status_code}. Stopping.")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    
    # リポジトリ名へのリンク（/google/リポジトリ名）を持つ見出し(h3またはh4)を探す
    repo_links = soup.select("h3 a[href^='/google/'], h4 a[href^='/google/']")
    
    if not repo_links:
        print("No more repositories found.")
        break

    for link in repo_links:
        name = link.get_text(strip=True)
        
        # リンクを含む親のリスト要素(li)まで遡る
        container = link.find_parent("li")
        if not container:
            continue
            
        # スター数（/stargazers へのリンク）を取得
        star_tag = container.select_one("a[href$='/stargazers']")
        stars = star_tag.get_text(strip=True) if star_tag else "0"
        
        # 主要な言語を取得（色付きの丸アイコンの隣にあるテキスト、またはlang属性など）
        language = "None"
        # GitHubの言語表示は aria-label や色付き丸(background-color)の隣のspanに入っていることが多い
        color_dot = container.select_one("span[style*='background-color']")
        if color_dot and color_dot.parent:
            lang_text = color_dot.parent.get_text(strip=True)
            if lang_text:
                language = lang_text

        # DBに挿入
        cur.execute(
            "INSERT INTO repositories (name, language, stars) VALUES (?, ?, ?)",
            (name, language, stars)
        )

    conn.commit()
    page += 1

# 3. 保存したデータをSELECT文で表示
print("\n--- 保存されたデータ (SELECT文の結果) ---")
cur.execute("SELECT * FROM repositories")
rows = cur.fetchall()

for row in rows:
    print(row)

print(f"\n合計取得件数: {len(rows)} 件")
conn.close()