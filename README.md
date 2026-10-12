# Car Design Daily

每日一期的靜態網頁：全球汽車設計新聞＋汽車新知＋隨機情緒板（zh-TW）。

- 線上（永久）：https://feeling00480-commits.github.io/car-design-daily/ （GitHub Pages，repo `feeling00480-commits/car-design-daily`，branch `main`、root）
- 每期固定網址：`/issues/YYYY-MM-DD/`；首頁 `/` = 最新一期；`/archive/` = 往期列表
- **AI Model Daily**（同一個 repo／網站）：`/ai/` = 最新一期、`/ai/issues/YYYY-MM-DD/`、`/ai/archive/`
- **站名只用英文**：「Car Design Daily」與「AI Model Daily」。**不要**再使用任何中文站名（例如「汽車設計日報」「AI 模型日報」「AI 模型每日快報」——前者已被其他汽車媒體使用）。這適用於 masthead `<h1>`（不加中文副標）、`<title>`、og:title、meta description、往期頁、頁尾、左上角 wordmark，以及每日通知訊息裡對網站的稱呼。分頁標題格式：`Car Design Daily · YYYY.MM.DD`、`AI Model Daily · YYYY.MM.DD`。文章內容仍為繁體中文；切換器的分類標籤（CAR DESIGN 汽車設計／AI MODELS AI 模型）是分類名稱，保留不變。
- 每頁頂端都有切換器「CAR DESIGN 汽車設計｜AI MODELS AI 模型」（kicker 字體樣式，手機版在第二列、全寬）。外框（`.mind`）會滑到目標再換頁（0.38s；`prefers-reduced-motion` 時直接換頁），沒有 JS 時就是一般連結。程式在 `tools/build.py` 的 `switcher()` 和 `SWITCH_JS`。兩個區塊共用 `assets/style.css` 的設計系統與 RWD 格線（<768 一欄、768–1199 兩欄、≥1200 三欄）；AI 區塊用 `body.mode-ai` 套上科技感深色配色（預設深色，深淺色偏好與汽車區分開記憶）。

## 結構
```
index.html                  ← build.py 產生（最新一期）
archive/index.html          ← build.py 產生
assets/style.css            ← 共用樣式（深淺色、RWD、CJK 字體）
issues/YYYY-MM-DD/
  data.json                 ← 手寫的內容檔
  term.svg                  ← 今日設計名詞的線稿示意圖（每期新畫，build 會內嵌）
  img/*.webp                ← 情緒板圖像（≤1400px WebP）
  index.html                ← build.py 產生
ai/
  index.html                ← build_ai.py 產生（AI 最新一期）
  archive/index.html        ← build_ai.py 產生
  issues/YYYY-MM-DD/
    data.json               ← AI 每日內容（唯一需要手寫的檔案）
    img/*.webp              ← 來源 og:image（≤1600px WebP，<300KB）
    index.html              ← build_ai.py 產生
tools/
  build.py                  ← data.json → HTML（汽車；也提供共用的 topbar／切換器）
  build_ai.py               ← ai/issues/*/data.json → AI 頁面
  publish.sh                ← build + git commit + push main（GitHub Pages 自動重新部署）
  publish-flypod.sh         ← 已棄用的 flypod 備案
  pick_themes.py, themes.json ← 隨機主題（避開近 10 期）
  moodart.py                ← 程式生成情緒板插畫／材質（無 AI 生圖工具時的備案）
  genimg.py                 ← AI 生圖腳本（Pollinations；目前匿名呼叫回 402 需付費，已停用）
```

## 產生下一期（每日流程）
1. **蒐集設計新聞（5–8 則，近 24–72 小時）**：用 WebSearch/WebFetch 實際讀過原文才收錄；不得杜撰日期、引言。
   - **固定 7 則（自 2026-10-13 起；10-12 已補到 7 則）**：第 1 則是全寬 feature 卡，其後 6 則在 ≥1200px 三欄格線排成 3＋3，剛好填滿；build.py／CSS 不需改動（卡片數不寫死）。
     **排序純粹依新聞重磅程度**：最大條的（通常是全新車型全球首發）當第 1 則（首則圖也會成為 og:image 與往期列表標題）。**Mitsubishi 追蹤**：每天專門搜尋 Mitsubishi（合作夥伴）消息；有新鮮且重要的消息就保底佔 7 則中的一則，位置依它的重要程度排，不硬放第一或最後。未經官方證實的報導要在標題／摘要寫明「報導」並附雙方回應。沒有重要消息就不硬塞、也不必提沒有消息，改用下一則最好的備選（日系車廠是不錯的後備）補滿 7 則。
   每則：品牌、標籤、日期、中文標題、原文標題、2–3 句摘要、3–5 點設計解析（比例／燈號／面處理／CMF／室內 UX／品牌方向）、來源連結。
   - **每則設計新聞都必須有 1 張代表圖（必要步驟）**：
     1. 優先用車廠官方新聞室／press kit 圖片（BMW PressClub、JLR Media、VW Newsroom、Renault/Alpine Media、Hyundai Newsroom、Porsche Newsroom…）；找不到才用來源報導的 `og:image`。
        取得方式：`curl -sL -A "<瀏覽器 UA>" <URL> | grep -o -i -E '<meta[^>]*og:image[^>]*>'`，必要時在頁面 HTML 中找較大尺寸的圖。
     2. 必須確認圖片就是該車款（開圖檢查）；**不可用不相符的圖，也不可用 AI 生成圖代表真實車款**。若找不到合適圖片，該則不放圖，並在回報中註明。
     3. 裁成 16:9、縮成 1600×900 WebP（q≈82，<300KB），存成 `issues/<date>/img/news-<id>.webp`。
     4. 在 data.json 該則加入 `"image": {"file": "news-<id>.webp", "alt": "<中文描述>", "credit": "<來源名稱，如 BMW Group PressClub>", "credit_url": "<來源頁面>"}`。
        build.py 會把圖片放在卡片最上方（object-fit: cover、lazy loading、alt），並顯示「圖片來源：…」連結；首則卡片的圖也會用作 og:image。
2. **汽車新知（3–5 則）**：EV、電池、自駕、法規、製造、市場；摘要＋連結。
   **今日設計名詞（必要步驟，每期都要畫新圖）**：寫一則和當期新聞呼應的名詞（`term.name / zh / body / source`），並**為這個名詞手繪一張新的線稿示意圖**：
   - **選詞**：只用汽車設計圈公認、查得到用法的術語（例：lighting signature、DRG／down-the-road graphic、dash-to-axle、greenhouse、DLO、shoulder line、C-pillar、heritage cue）。來源以 Car Design News、Interior Motives、車廠設計新聞稿或設計師訪談為準；**不可自創名詞**，也不要用某位設計師的一次性口語（例如 Jaguar 的「strike-through graphic」）當主詞條，必要時改用它所屬的通用術語。
   - **內文寫法（約 100–150 字，白話繁體中文）**：① 第一句直接定義「它是什麼」；② 接著舉一台**本期新聞裡的真實車款**，具體說是哪個部位、長什麼樣子；③ 最多再一句說設計師為什麼這樣做。不用比喻（如「劃破」「同一筆簽名」）、不堆砌術語（如「面處理」「母題」「顯影」）；寫完自己讀一遍，一般讀者一次看得懂才算數。
   - **出處**：`"source": [["來源名稱：簡述", "URL"], ...]`（1–2 個，實際讀過的頁面），頁面會在內文下方顯示一行「出處：…」。
   - **示意圖**：存成 `issues/<date>/term.svg`，在 data.json 加 `"diagram": "term.svg"`。
     - 必須畫出**一眼看得出是車**的線稿：正面／背面／側面擇一或並排，要有車身輪廓、輪胎、擋風玻璃（或車窗），以及水箱護罩或車燈；不可只畫抽象方框或線條。
     - 名詞指的部位用強調色 `#f08a5d` 標出，並加 **2–3 個簡短中文標註**（如「① 四條細長頭燈」）用虛線指到該部位；最下方可加一行白話說明。
     - 格式：單一 `<svg class="diagram" viewBox="0 0 520 …" width="100%" role="img" aria-label="…">`；線條用 `stroke="currentColor"`（自動適應深淺色），文字要在頁面上縮小後仍看得清楚（viewBox 520 寬時，標註 font-size 15–16、次要文字 ≥12）。風格參考 `issues/2026-10-11/term.svg`（lighting signature：Type 01 正面＋背面）與 `issues/2026-10-09/term.svg`（Heritage cue）。
     - 圖的內容必須對應當天名詞與內文舉的例子；**不可沿用前一期的圖**。build.py 會內嵌這個 SVG，缺檔、缺 `diagram` 欄位，或與其他期（不同名詞）內容相同時，**build 會直接失敗**。
3. **情緒板（1–2 組）**：`python3 tools/pick_themes.py 2` 抽主題 → 每組 4–6 張原創虛構圖（不可出現真實車款或 logo）＋6 色 hex 色票、關鍵字、材質筆記。
   - 有 GenerateImage 等生圖工具時優先使用，輸出後轉 WebP（≤1400px、q≈80）放 `issues/<date>/img/`，命名 `mb1-1…`、`mb2-1…`，每組第一張為 hero（16:9），其餘 4:3。
   - 沒有時用 `tools/moodart.py` 的做法（SVG 插畫＋numpy 材質）為新主題寫對應函式。
4. 複製前一期 `data.json` 為模板，填入新內容（`issue_no` +1、`date`、`weekday`、`lede`）。
5. 發佈：在 `/workspace/car-design-daily` 執行 `./tools/publish.sh "Issue 00N · YYYY-MM-DD"`
   （= `build.py` + `build_ai.py`（--site-url "$(cat .site-url)"） → `git add -A` → `git commit` → `git push origin main`）。
   GitHub Pages 約 1–2 分鐘重新部署（可用 `gh api repos/feeling00480-commits/car-design-daily/pages/builds/latest` 查狀態）。
   之後用 WebFetch／curl 驗證 `https://feeling00480-commits.github.io/car-design-daily/`、`/issues/<date>/`、`/archive/` 以及所有新聞圖與情緒板圖片都回 200。
   - 所有站內連結必須是相對路徑（站點位於子路徑 `/car-design-daily/`）；og:image／canonical 用 `.site-url` 產生絕對網址。
6. 預覽圖：`google-chrome --headless=new --no-sandbox --window-size=1280,2400 --screenshot=preview.png <URL>`

## AI Model Daily：每日流程
**版面順序（2026-10-12 起，v3）**：01 閉源模型 → ≡ 本週榜單（緊接閉源之後、不編號）→ 02 開源模型 → 03 追蹤清單 → 04 其他新聞 → 05 推薦影片 → 06 注意事項 → 往期。區塊編號由 `build_ai.py` 依實際出現的區塊自動計算；舊期（沒有 `closed`／`open`／`leaderboards`）照舊顯示 01 追蹤清單起。

1. **來源資料**：`/workspace/ai-digest/reported.json`，取 `run_date` = 當天的項目；**先比對所有舊 `run_date` 的標題／網址，已報過的不再當主新聞**（例：GPT-6、Claude Haiku 5.5 已於 10/08 報導）。
   - `closed` → 「閉源模型」：各大 AI 公司的閉源新模型與重大功能更新，**文字／LLM**（OpenAI、Anthropic、Google Gemini、xAI Grok、Meta 等）與**圖像／影片**（Midjourney、Runway、Kling、Seedance、Vidu、Veo／Omni、BFL Pro…），以及能力測試、跑分、榜單變化、重要評測報導。**4–6 則，依重要性排序，沒有就少放，絕不湊數**；只收最近幾天的消息。
   - `open` → 「開源模型」：重要的新開放權重發布，文字／LLM（Qwen、DeepSeek、Llama、Mistral、GLM、Kimi…）與圖像、影片、音訊模型。**4–6 則**，依重要性排序，必須是新的。
   - `watch:<model>` → 「追蹤清單」（MiniMax H3、Qwen Image 2.1、Krea 2；每個模型一張卡）。
   - `other` → 「其他新聞」：約 6 則，範圍同原本：工具、ComfyUI 更新、社群工作流、研究、API／服務。**已屬閉源／開源模型區的不放這裡，也不重複**。
     - **forge-classic**（https://github.com/Haoming02/sd-webui-forge-classic，預設分支 `neo`）：每天用 `gh api repos/Haoming02/sd-webui-forge-classic/commits?sha=neo` 與 `/releases` 檢查，和 reported.json 的 `forge_classic.last_seen_commit` 比較；**只有真的有新 commit／release 才放一則**（寫改了什麼、台灣時間），沒有就完全不提。放了之後更新 `forge_classic`。
   - `youtube` → 「推薦影片」。`seen-not-reported` 不當主新聞，只在注意事項簡短帶過。
2. **核對原文**：每則都讀過主連結，讀不到再讀 `alt_urls`，摘要只寫原文有的內容；官方頁擋抓取時要在 caveats 註明依哪個轉載來源整理。抓取一律 15 秒逾時。
3. **代表圖（有就放，沒有就不放）**：抓主連結或 alt 的 `og:image`（curl 加瀏覽器 UA），轉成 ≤1600px WebP、<300KB，存到 `ai/issues/DATE/img/`，在 data.json 的 `image` 填 `file / alt / credit / credit_url`。
   - 只用官方或來源頁自己的圖（官方宣傳圖、HF／GitHub 分享卡、專案示例、官方貼文影片縮圖）。
   - **絕不用 AI 生成圖代表真實產品**；第三方部落格的 AI 插畫封面也不用。
   - 沒有專屬圖（只有網站通用圖）就設 `"image": null`，頁面會註明「來源頁沒有可用的官方圖片」。
   - YouTube 縮圖：`https://i.ytimg.com/vi/<id>/maxresdefault.jpg`。頁面先顯示縮圖，點擊才載入 youtube-nocookie 內嵌播放。
4. **本週榜單（leaderboard 模組）**：
   - 兩張圖：(a) **文字 LLM 總榜**：LMArena Text Arena Overall 前 10（`curl -A "Mozilla/5.0" https://lmarena.ai/leaderboard/text`，HTML 內含名次／分數／±／票數／更新日）；(b) **生圖或生影片榜**：Artificial Analysis 前 10（`https://artificialanalysis.ai/image/leaderboard/text-to-image` 或 `/video/leaderboard/text-to-video`，HTML 內含 Elo）。**只用實際抓到的數字，絕不編造**；記下來源與資料更新日（as_of）、抓取日。AA 頁面沒有廠商欄位，org 依模型名對應。
   - 每天存快照 `/workspace/ai-digest/leaderboards/YYYY-MM-DD.json`（格式同 2026-10-12.json：`boards[]` 每個有 `id,title,en,source,source_url,as_of,fetched,metric,rows[{rank,model,org,score,ci,note?}]`），供隔天比對。
   - **顯示規則**：週一、或沒有前一份快照 → `"mode": "full"` 顯示完整兩張圖。其他日子和最近一份快照比較：有新模型進入前 5、或第 1 名換人 → `"mode": "changes"`，照樣放兩張圖，在變動的 row 加 `"new": true` 或 `"up": true`（顏色會改成 accent2），並在 `changes[]` 用一句話寫出變化；都沒有 → `"mode": "note"`，`note` 寫「榜單無重大變化，最新更新日 YYYY-MM-DD」。
   - 某個榜抓不到（JS 渲染等）時先試公開 API／資料檔或其他可信彙整站（如 BenchLeader），仍失敗就只放另一張並在 caveats 註明。
   - data.json：`"leaderboards": {"mode", "snapshot", "boards"[同快照], "changes"?, "note"?}`。
5. **寫 `ai/issues/YYYY-MM-DD/data.json`**（可複製上一期再改），欄位如下：
   - `date`、`weekday`、`issue_no`、`lede`（先閉源、再榜單重點、再開源與追蹤清單）
   - `closed[]`、`open[]`、`news[]`：都是 `{id, org, tag, date, title, orig, summary, links[[名稱, url]], image|null}`；tag 以「閉源 · …」「開源 · …」開頭
   - `leaderboards`：見上
   - `watch[]`：`{id, model, kind, status, updates[]}`；每則 update 是 `{title, date, summary, links, image|null}`
   - `video`：`{title, orig, channel, youtube_id, url, date, thumb{file, alt, credit}}`
   - `caveats[]`：廠商自評數字、權重尚未釋出、授權、榜單 Preliminary／信賴區間、讀不到的原文等
   - masthead 會自動顯示：追蹤模型／更新數、閉源 N 則、開源 N 則、其他新聞 N 則、推薦影片。
6. **更新** `reported.json`（每則加 `category`：`closed`／`open`／`watch:*`／`other`／`youtube`／`seen-not-reported`）與 `/workspace/ai-digest/today_summary.md`（3–5 行：閉源、榜單、開源、追蹤清單重點）。
7. **發布**：`./tools/publish.sh "AI 00N · YYYY-MM-DD"`（內含 `--site-url`，會同時重建汽車與 AI 兩區；注意它用 `git add -A`，根目錄不要留預覽截圖），約 1 分鐘後檢查 `/ai/`、`/ai/issues/DATE/`、`/ai/archive/`。手動重建時一定要加 `--site-url "$(cat .site-url)"`，否則 og:image／canonical 會消失。

## 新聞來源清單
- 設計專業：Car Design News、Interior Motives、Auto&Design（義）、Dezeen、Designboom、Design Week、Wallpaper*、Yanko Design
- 綜合車媒：Autocar、Top Gear、Motor1、Carscoops、Car and Driver、Road & Track、CAR Magazine、Octane、autoevolution
- 科技／EV：The Verge、Electrek、InsideEVs、electrive、WIRED
- 亞洲：Chosun Biz、Digital Today（韓）、Car Watch／Response（日）、汽车之家／懂车帝（中）、Yahoo 汽車／U-CAR／8891（台）
- 原廠新聞室：JLR、BMW PressClub、Renault、Stellantis、Alpine、Porsche Newsroom、Hyundai Newsroom 等
- 產業：Reuters、Automotive News、just-auto、Insurance Journal

## 主題池
見 `tools/themes.json`（Brutalist off-roader、Japanese retro-futurism 1980s、Scandinavian calm interior、Desert rally pastel、Art Deco streamliner、Kyoto craft & washi interior…），可自由增補。

## 託管
- **正式**：GitHub Pages（`main` / root，含 `.nojekyll`），push 即更新，網址永久。gh CLI 已在本機以 `feeling00480-commits` 登入。
- **已棄用備案**：flypod 匿名部署 https://2b80368e7d1741c6.flypod.page（2026-10-22 到期；`tools/publish-flypod.sh`）。更新權杖在本機 `~/.config/flypod/`，絕不可 commit。
