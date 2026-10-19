# Car Design Daily

每日一期的靜態網頁：全球汽車設計新聞＋色彩與材質（含年度色／內裝配色示例）＋汽車新知（zh-TW）。

- 線上（永久）：https://cmcdesignai.github.io/car-design-daily/ （GitHub Pages，repo `CMCDesignAI/car-design-daily`，branch `main`、root）
- 每期固定網址：`/issues/YYYY-MM-DD/`；首頁 `/` = 最新一期；`/archive/` = 往期列表
- **AI Model Daily**（同一個 repo／網站）：`/ai/` = 最新一期、`/ai/issues/YYYY-MM-DD/`、`/ai/archive/`
- **站名只用英文**：「Car Design Daily」與「AI Model Daily」。**不要**再使用任何中文站名（例如「汽車設計日報」「AI 模型日報」「AI 模型每日快報」——前者已被其他汽車媒體使用）。這適用於 masthead `<h1>`（不加中文副標）、`<title>`、og:title、meta description、往期頁、頁尾、左上角 wordmark，以及每日通知訊息裡對網站的稱呼。分頁標題格式：`Car Design Daily · YYYY.MM.DD`、`AI Model Daily · YYYY.MM.DD`。文章內容仍為繁體中文；切換器的分類標籤（CAR DESIGN 汽車設計／AI MODELS AI 模型）是分類名稱，保留不變。
- 每頁頂端都有切換器「CAR DESIGN 汽車設計｜AI MODELS AI 模型」（kicker 字體樣式，手機版在第二列、全寬）。外框（`.mind`）會滑到目標再換頁（0.38s；`prefers-reduced-motion` 時直接換頁），沒有 JS 時就是一般連結。程式在 `tools/build.py` 的 `switcher()` 和 `SWITCH_JS`。每頁都有 Screen Wake Lock（開啟時螢幕不會休眠）。兩個區塊共用 `assets/style.css` 的設計系統與 RWD 格線（<768 一欄、768–1199 兩欄、≥1200 三欄）；AI 區塊用 `body.mode-ai` 套上科技感深色配色（預設深色，深淺色偏好與汽車區分開記憶）。

## ⚠️ 不可移除：Screen Wake Lock
- 程式在 `assets/wakelock.js`。**所有頁面一律用 `tools/build.py` 的 `write_page()` 寫出**，它會自動在 `</head>` 前插入 `<script src="…assets/wakelock.js" defer>`（依頁面深度算相對路徑），所以改版 header／footer 也不會掉。
- 兩個 build 結尾都會跑 `check_wakelock()`：本次寫出的任何頁面缺 wake lock、或 `assets/wakelock.js` 不存在，就以 exit 2 失敗並列出頁面。**不要繞過 `write_page()`、不要刪這個檢查**；發布後也要抽查線上頁面含 `wakelock.js`。

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
1b. **色彩與材質 CMF（排程自 2026-10-17 起：每日 4–7 張卡，數量彈性）**：放在設計新聞之後。中間的「色彩・材質・介面動態」模組，**每個類別一列**：A 列車型內裝（`cmf[]` kind=car）、B 列色彩／塗料／材質（`cmf[]` kind=trend|paint|material）、C 列介面與 HMI（`hmi[]`）。每列 1 張＝全寬（桌機圖左文右）、2 張＝各半、3 張＝三等分；手機一欄。
   - **每日數量依素材量、重要性與適合度決定，不硬湊**：car 1–2、trend+paint+material 合計 2–3、hmi 0–2，`cmf`＋`hmi` 合計 4–7。欄位：`cmf[]`：`{id, kind(car|trend|paint|material), car（品牌／車型或機構名）, tag, title（≤24 字）, points[3–4 句，每句 ≤30 字], image{file, alt, credit, credit_url}（車型必填；其他有圖就放）, swatch?{label, hex}（無圖的色彩卡）, sources[[名稱, url]], note?（備援說明，顯示 ⚠）}`。`kind` 決定所在列與標籤（車型／趨勢／塗料／材質）。發布前跑 `python3 tools/check_cmf.py <日期>`（會檢查上述數量，舊期無 kind 不檢查）。
   - **規則 1：不與當日設計新聞重疊**：**同車＋同一篇來源文章禁止**；也避免同車重複講設計新聞已寫過的內裝重點（例：Mission S 已在設計新聞講五圓儀表，就不要再用同一角度當 CMF 車型則）。優先選設計新聞以外的車；素材夠好且有**另一篇**專門內裝／CMF 來源時才用同車。
   - **規則 2：車型則照片必須是內裝或材質特寫**（座艙、座椅、儀表板、飾板、縫線、布料／皮革、漆面近拍）。**禁止外觀 3/4 或全車照**。找不到合格照片就換車。
   - **材質卡範圍：以「已用於汽車」的表面材質／表面處理為優先**：量產或概念車上看得到、摸得到的內外飾材質，或車用供應商為汽車內外飾提供的材料（皮革與替代皮革、車用面料如 Kvadrat／Dinamica／Alcantara、木飾、裝飾膜、烤漆／塗層效果、電鍍／鍍鉻、紋理／皮紋、發光飾件與燈光材質、指名車款的永續飾材）。**家具相關材質可以收**，前提是能對應到車內（座椅包覆、皮革、紡織、軟質飾面、可轉用到車上的木飾），並在 points 寫出與車內的關聯。**展覽作品要嚴選**：只收有明確車用潛力的材料，純藝術作品不收（例：設計週天然染色作品）。**不收**：結構件、底盤件、引擎／變速箱、隱藏零件或純工程材料新聞（例：回收 PA6 穩定桿連桿）。
   - **來源**：國際車廠原廠新聞稿／內裝圖集、zley 提供的 CMF 部門網站（色彩趨勢 WGSN／Coloro／Pantone／NCS；車用塗料 PPG／Axalta／BASF；材質 MaterialDistrict、Automotive Interiors World /news/materials 等；空間／生活設計 Dezeen／designboom 僅備援）、網路搜尋（Auto&Design、Interior Motives、Car Design News 等），以及相關時的中國車廠（NIO、Li Auto、Xpeng、BYD 等原廠發布）。每一句 point 都要能在來源找到；色名／材質名保留原廠英文；不可從照片推測。
   - **去重（30 天）**：寫入 `cmf-log.json`（`{date, kind?, car_key, angle, url, image?}`）。30 天內同 `car_key` 或同 `url` 不再放。車型湊不到 2 則就少放，不硬湊；0 則車型時仍盡量保留趨勢／塗料／材質。
1c. **介面與 HMI 卡（`hmi[]`，0–2 張；有好案例時 1 張，強案例日 2 張）**：在上面卡片模組的 C 列，和其他卡片同樣式，標籤「介面與 HMI」（kind=case）或「靈感參考」（kind=inspiration）。給 GUI 設計師看的「以圖為主」設計案例。
   - 欄位：`hmi[]`：`{id, kind(case|inspiration), brand, tag, title（≤26 字）, date（YYYY-MM-DD，來源真實發布日）, points[3–5 句 zh-TW，寫這個介面設計做得好的地方], image{file（本機 .jpg，存 issues/<日期>/img/）, alt, credit, credit_url}, sources[[名稱, url]]}`。`hmi` 空或缺 → C 列不顯示。
   - 圖片：必須是真實介面截圖或設計圖（中控／儀表 UI、HMI 概念、Android Auto／CarPlay／Tesla 畫面、OEM HMI 案例），下載後轉 JPG（長邊 ≤1600）。credit 格式只能是「Brand (via site)」（例：`GM (via Automotive Interiors World)`）或「site 示意圖」（例：`Not a Tesla App 示意圖`）。沒有可用圖片的消息不放。
   - 來源：Automotive Interiors World /news/hmi（curl 403，用 WebFetch 讀；圖片檔可 curl）、Not a Tesla App（/rss；軟體更新頁附介面圖）、9to5Google Android Auto、9to5Mac CarPlay、Elektrobit newsroom。沒有新案例時改放 `kind: inspiration`，標「靈感參考」：MOMOHMI、Muzli、Apple HIG／design videos、Google Design。
   - 日期照抄來源，不可推測；舊於 30 天的案例只有在當天沒有新案例時才用，並照實標日期。
   - 去重（30 天）：寫入 `hmi-log.json`（`{date, key(=id), url, image}`），30 天內同 key 或同 url 不再放。發布前跑 `python3 tools/check_hmi.py <日期>`。
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
3. **年度色與每日內裝配色（`color_data`，自 2026-10-16 起取代獨立情緒板）**：有 `color_data` 的期數不再做獨立「情緒板」區塊。
   - `color_data.hues/pop/dirs/mat`：年度色／市佔／方向／材質數據（只寫實際讀過的報告）。
   - `color_data.interior`：每日一組儀表板＋門板配色示例；以當期引用的年度色／趨勢色**新組**組合（不要直接複製年度色盤），含 `parts`（色票＋來源小字／連結）、`mood`／`mood_text`、`vars`（上色用 CSS 變數）。插圖用固定模板 `assets/door-template.svg`＋`assets/ip-template.svg`，只換顏色。
   - 舊期（無 `color_data`）仍可保留 `moodboards`；新期不要再加虛構主題情緒板。
4. 複製前一期（有 `color_data` 的）`data.json` 為模板，填入新內容（`issue_no` +1、`date`、`weekday`、`lede`）；清掉過期 CMF／新聞，保留結構。
5. 發佈：在 `/workspace/car-design-daily` 執行 `./tools/publish.sh "Issue 00N · YYYY-MM-DD"`
   （= `build.py` + `build_ai.py`（--site-url "$(cat .site-url)"） → `git add -A` → `git commit` → `git push origin main`）。
   GitHub Pages 約 1–2 分鐘重新部署（可用 `gh api repos/CMCDesignAI/car-design-daily/pages/builds/latest` 查狀態）。
   之後用 WebFetch／curl 驗證 `https://cmcdesignai.github.io/car-design-daily/`、`/issues/<date>/`、`/archive/` 以及新聞圖與 CMF／內裝插圖都回 200。
   - 所有站內連結必須是相對路徑（站點位於子路徑 `/car-design-daily/`）；og:image／canonical 用 `.site-url` 產生絕對網址。
6. 預覽圖：`google-chrome --headless=new --no-sandbox --window-size=1280,2400 --screenshot=preview.png <URL>`

## AI Model Daily：每日流程
**版面順序（2026-10-13 起，v4：新手友善）**：≡ 本週榜單（每天都顯示、永遠在最上方，不編號；無變化標「榜單無重大變化」）→ 01 AI 新聞 → 02 追蹤清單 → 03 教學區 → 04 推薦影片 → 05 注意事項 → 往期。`data.json` 有 `ainews` 就是 v4（不再輸出閉源／開源／其他新聞）；舊期（v3 的 `closed`／`open`／`news`）照原樣顯示。

**v4 共通短格式（每一則都要）**：`short_title`（短標題）＋ `one`（一句白話：這是什麼、對讀者有什麼用）＋ `gloss`（`[[名詞, 一句白話解釋]]`，**該名詞在當期第一次出現時才加**）；細節（`orig`、`summary`、來源）自動收進「看更多」。`lede` 1–2 句、`caveats` 最多 2 行、榜單 `analysis_short` 1–2 句（只有 changed 時）。

1. **來源資料**：`/workspace/ai-digest/reported.json`，取 `run_date` = 當天的項目；**先比對所有舊 `run_date` 的標題／網址，已報過的不再當主新聞**。
   - `ainews` → 「AI 新聞」：**約 5–6 則**，依重要性排序，沒有就少放、不湊數。範圍：
     - 大廠的模型與產品新聞：Google（Gemini、Gemini App、Nano Banana 各版本、Flow 影片平台的服務異動）、OpenAI（GPT、ChatGPT）、Anthropic（Claude）、xAI（Grok、Grok App、Grok Bot，以及 Musk 在 X 上的產品宣布）、Meta，及同級公司（Mistral、DeepSeek、Qwen 等）。
     - **平台／服務異動也算新聞**（Flow、Gemini App、ChatGPT、Grok App 的功能、方案、價格、下架）。
     - 圖像／影片生成模型的**世代升級**；大型文字／圖像／影片模型的**重磅開源**。
     - **不收**一般人用不到的小眾、領域專用或純論文模型。
     - **X 帳號**（用 x 工具 `get_users_posts`，exclude replies,retweets，只取近 36 小時）：@elonmusk、@xai、@grok、@OpenAI、@AnthropicAI、@GoogleDeepMind、@GeminiApp、@NanoBanana。**只收產品宣布**，政治、迷因、轉推閒聊一律不收；引用時附 x.com 貼文連結。
     - **版本升級（例：Nano Banana 2.0 → 2.1）**：看更多裡必寫【比上一版進步在哪】（官方說法）、新限制或價格變化、在哪裡能用；再附 **2–4 則真實使用者／評測者的實測比較（含連結）**，註明樣本小、屬初步實測。
     - **延伸規則**：已在 reported.json 的主題，只有出現新實質內容（新實測、新平台／地區上線、價格變動、下架日）才可再放，`tag` 前加「延伸 · 」；否則不放。
   - `watch:<model>` → 「追蹤清單」（MiniMax H3、Qwen Image 2.1、Krea 2；每個模型一張卡，同樣短格式，每則更新一句 `one`）。**沒有消息的模型**：`updates: []`、`status` 寫「今天沒有新消息。」（卡片顯示「今日無更新」）。
   - `tutorial` → 「教學區」：每天 **2–3 篇**新手部署／操作教學（圖像或影片生成：安裝 ComfyUI、本地跑 Qwen Image／影片模型、LoRA、放大、img2img／inpaint、量化省顯存…）。欄位 `{id, title, learn（一句：學到什麼）, level（入門／中階／進階）, vram, kind（常青教學／本週新教學／追蹤模型教學）, gloss, steps[], links}`。
     - 來源只用官方文件、GitHub README、Hugging Face 模型卡或知名教學；**每個連結發布前 curl 確認 200**（被擋 403 的改用其他可信來源）。VRAM 寫官方數字，沒有就標「約／依原頁為準」，**不得編造**。
     - 組合：至少 1 篇和本週新聞或追蹤模型相關（有好的才放），其餘從常青主題輪替。
     - **去重**：每篇寫進 reported.json（`category: "tutorial"`、`url`、`topic` 例如 `install-comfyui`、`qwen-image-2.1-run`、`lora-basics`）；**30 天內同 URL 或同 topic 不重複**；常青主題 30 天後只有換來源或新版本（如 ComfyUI Desktop 新版）才可再上；同一模型每週最多 1 篇；沒有合格的就只放 2 篇，不重複湊數。
   - **forge-classic**（https://github.com/Haoming02/sd-webui-forge-classic，分支 `neo`）：每天用 `gh api repos/Haoming02/sd-webui-forge-classic/commits?sha=neo` 與 `/releases` 對照 reported.json 的 `forge_classic.last_seen_commit`；**只有正式 release 或重大功能**才放（放 AI 新聞，或做成教學區一篇），零星 commit 不放、不提；都要更新 `forge_classic`。
   - `youtube` → 「推薦影片」1 支（和當期新聞相關才放）。`seen-not-reported` 不當主新聞。
2. **核對原文**：每則都讀過主連結，讀不到再讀 `alt_urls`，摘要只寫原文有的內容；官方頁擋抓取時要在 caveats 註明依哪個轉載來源整理。抓取一律 15 秒逾時。
3. **代表圖（有就放，沒有就不放）**：抓主連結或 alt 的 `og:image`（curl 加瀏覽器 UA），轉成 ≤1600px WebP、<300KB，存到 `ai/issues/DATE/img/`，在 data.json 的 `image` 填 `file / alt / credit / credit_url`。
   - 只用官方或來源頁自己的圖（官方宣傳圖、HF／GitHub 分享卡、專案示例、官方貼文影片縮圖）。
   - **絕不用 AI 生成圖代表真實產品**；第三方部落格的 AI 插畫封面也不用。
   - 沒有專屬圖（只有網站通用圖）就設 `"image": null`，頁面會註明「來源頁沒有可用的官方圖片」。
   - YouTube 縮圖：`https://i.ytimg.com/vi/<id>/maxresdefault.jpg`。頁面先顯示縮圖，點擊才載入 youtube-nocookie 內嵌播放。
4. **本週榜單（leaderboard 模組）——每天都顯示，固定在頁面最上方**（masthead／導言之後、01 閉源模型之前）：
   - **兩張圖**：(a) 文字 LLM 總榜：LMArena Text Arena Overall 前 10（`curl -sL -m 15 -A "Mozilla/5.0" https://lmarena.ai/leaderboard/text`，HTML 內有名次／模型／廠商／分數／±／Preliminary／資料更新日）；(b) 文生圖：Artificial Analysis AA-Image-T2I 前 10（`https://artificialanalysis.ai/image/leaderboard/text-to-image`，HTML 內有 Elo／±；沒有廠商欄位，org 依模型名對應）。**只用當天實際抓到的數字，絕不編造或估算**。
   - **每天的步驟**：
     1. 抓兩個榜，寫成 `/tmp/lb_fresh_YYYY-MM-DD.json`：`{"boards":[{id,title,en,source,source_url,as_of,fetched,metric,rows:[{rank,model,org,score,ci?,note?}]}]}`。`id` 固定 `text`／`image`，`title`／`en`／`source` 沿用前一天的寫法；`as_of` = 榜單頁標示的資料更新日，`fetched` = 今天；`note` 只填 `"Preliminary"`；模型名稱每天用同一種寫法（diff 是用名稱比對）。
     2. 執行 `python3 tools/lb_diff.py --date YYYY-MM-DD --fresh /tmp/lb_fresh_YYYY-MM-DD.json`。它會找 `/workspace/ai-digest/leaderboards/` 裡**日期早於今天的最新一份快照**來比對，每個榜給一個 `status`：
        - `baseline`：沒有前一份快照 → 顯示今天的圖，標「首份快照（Baseline）」。
        - `unchanged`：沒有重大變化 → **沿用前一份快照的圖與 as_of**，標「榜單無重大變化 · 資料更新 <as_of>」，來源列註明沿用哪天的資料與最新檢查日。
        - `changed`：有重大變化 → 顯示今天的圖，變動的列標 ↑n／↓n、NEW、分數差，並列出跌出前 10 的模型。
        - **重大變化的定義**：第 1 名換人，或前 10 名單有進出，或任一模型名次變動 ≥ 2，或任一分數變動 ≥ 5。小於這些的微幅波動視為無變化（沿用舊圖，誤差累積到門檻才會觸發）。
     3. 它會寫入今天的快照 `/workspace/ai-digest/leaderboards/YYYY-MM-DD.json`（存的是**實際顯示的資料**，含 `status`、`diff.summary`、`carried_from`），並把 `leaderboards` 寫進當天 `data.json`，再把 diff 摘要印出來。
     4. **`status` = `changed` 的榜，一定要填 `leaderboards.boards[i].analysis`**：繁中 3–5 句，只根據抓到的數字（加上相關的真實發布新聞）：誰上升／下滑、幅度多少；哪些模型新進前 10；有沒有突破（新的第 1 名、分數大跳、開源模型擠進前段）；代表什麼意義。`unchanged`／`baseline` 不用寫分析。
     5. 某個榜抓不到（JS 渲染、被擋）時，先試公開 API／資料檔或其他可信彙整站（如 BenchLeader）；仍失敗就**不要放進 fresh.json**（該榜那天不顯示），並在 caveats 註明。不要拿舊資料假裝是當天抓的。
   - 同一天重跑 `lb_diff.py` 沒問題：它永遠和「今天以前」的最新快照比較，並覆寫今天的快照；已寫好的 `analysis` 只要該榜仍是 `changed` 就會保留。
5. **寫 `ai/issues/YYYY-MM-DD/data.json`**（可複製上一期再改）：
   - `date`、`weekday`、`issue_no`、`lede`（1–2 句）
   - `ainews[]`：`{id, org, tag, date, title, orig, summary, links[[名稱, url]], image|null, short_title, one, gloss?}`；`closed`／`open`／`news` 留空陣列
   - `tutorials[]`：見上方教學區欄位
   - `leaderboards`：由 `tools/lb_diff.py` 產生，**不要手寫**；status = changed 時補 `analysis`（3–5 句）與 `analysis_short`（1–2 句，頁面顯示這個）
   - `watch[]`：`{id, model, kind, status, updates[]}`；update 是 `{title, date, summary, links, image|null, short_title, one, gloss?}`
   - `video`：`{title, orig, channel, youtube_id, url, date, thumb{file, alt, credit}, one}`
   - `caveats[]`：最多 2 行
6. **更新** `reported.json`（`category`：`ainews`／`watch:*`／`tutorial`／`youtube`／`seen-not-reported`；教學加 `topic`）與 `/workspace/ai-digest/today_summary.md`（3–5 行：AI 新聞、榜單、追蹤清單、教學重點）。
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
- **正式**：GitHub Pages（`main` / root，含 `.nojekyll`），push 即更新，網址永久。gh CLI 已在本機以 `CMCDesignAI` 登入（active，git 經 gh auth setup-git）。
- **已棄用備案**：flypod 匿名部署 https://2b80368e7d1741c6.flypod.page（2026-10-22 到期；`tools/publish-flypod.sh`）。更新權杖在本機 `~/.config/flypod/`，絕不可 commit。

## 新車特報（`breaking`，選填）
重大新車消息可在當期 `data.json` 加 `breaking`，會以紅框卡片顯示在設計新聞上方（沒有此欄位的期數不受影響）。欄位：`label`（預設「新車特報」）、`brand`、`date`、`title`、`points`（4–6 則重點，標明哪些是廠商說法）、`image`（`file`/`alt`/`credit`/`credit_url`）、`video`（`{"type":"youtube","id":…}` 嵌入 iframe，或 `{"type":"x","url":…,"title":…}` 嵌入 X 貼文並附連結）、`sources`（`[名稱, 網址]`）。只放已有官方來源查證的消息。


## 內裝配色模板（door／IP）
**2026-10-19 起**：改用單張一點透視車室圖 `assets/ip-combined-template.svg`（全寬置中，圖說「車室透視（…）」），由 `tools/gen_ip_combined.py` 產生（改幾何才需重跑；它會讀 `ip-template.svg` 的儀表板正面）。分界日在 `tools/build.py` 的 `COMBINED_FROM`；10/18 以前的期數仍用舊的兩張並排圖。同一組變數照樣上色；透視圖額外對應：`headliner`→車頂＋A/B 柱＋側窗周邊飾板、`door-lower`→地毯／腳踏區側板、`door-upper`→後門段＋門與儀表板交界、`ip-upper`→儀表板上表面、`seat-*`→座墊。黑色陶瓷印刷、後視鏡／照後鏡、方向盤柱與下輻、踏板、螢幕、出風口葉片為固定色。**每日流程不用改**：照常填 `color_data.interior`。

**車室透視圖配色規則（10/19 起）**
- 地毯（地板＋腳踏區側板）固定深黑 `#141516`＋織紋，不吃色盤。
- 車頂襯（車頂、A/B 柱、側窗周邊飾板、握把）只有兩種：`vars.headliner` 填 `"light"`（淺灰 `#C8CBD0`）或 `"dark"`（深灰 `#4A4E55`），預設 light；握把自動用同色系略淺一階。填 HEX 或其他值，`check_cmf.py` 會擋下（build 只會依明暗自動歸類並警告）；`parts` 裡不要放 headliner。
- 互動標示：點色票或「部位與材質」項目，插圖中用到該變數（含 build 對應，例如 door-upper＝ip-upper）的部位維持原色，其餘變暗；再點一次／點空白處／Esc 取消。樣式由 `tools/build.py` 的 `IP_HL_MODE`（`"dark"` 變暗其餘｜`"glow"` 光暈描邊）切換。插圖上緣裁切為約 2:1、全寬顯示。
- 門板主色（`door-upper`：門上飾板、後門段、門與儀表板交界）一律等於儀表板主色 `ip-upper`，build 會強制套用；門板嵌飾 `door-insert`、扶手 `armrest`、下門板 `door-lower` 仍各自配色。

舊版：`assets/door-template.svg`（實用型前門板）與 `assets/ip-template.svg`（正視方正儀表板＋中控塔＋座椅）是兩張固定插圖，並排顯示。每天只換顏色：build.py 讀 `data.json → color_data.interior`，把色值注入成 CSS 變數。
- `parts`：`[部位說明, 色名, HEX, 是否官方, 變數名]`，會顯示成色票與材質清單。
- `vars`：不顯示色票但要上色的部位。
- 變數名：`ip-upper`（上儀表板軟質）、`ip-decor`（儀表板／門板飾條、出風口框、門把）、`ip-lower`（下儀表板）、`door-upper`（門上飾板）、`door-insert`（門板嵌飾）、`armrest`（門扶手、中央扶手）、`door-lower`（下門板、喇叭網）、`stitch`（縫線）、`console`（中央通道）、`seat`（座椅）、`steering`（方向盤）、`headliner`（車頂襯）、`seat-bolster`（座椅側翼／頭枕，預設←seat）、`seat-center`（座椅中央，預設←seat）、`console-arm`（中央扶手，預設←armrest）、`accent-pod`（左杯架點綴，預設←ip-decor）、`accent-pod2`（右杯架點綴，預設←accent-pod）。
- 沒給的變數會套預設（如 ip-lower←door-lower、seat←door-insert）。材質紋理（皮紋、織紋、拉絲）是半透明疊層，跟顏色無關。

## 色彩與材質（CMF）每日 4–7 張卡
- 一類一列：A 車型（`cmf` kind=car，1–2）、B 色彩／塗料／材質（`cmf` kind=trend|paint|material，2–3）、C 介面與 HMI（`hmi[]`，0–2）。每列 1 張全寬／2 張各半／3 張三等分。
- 替代內容留在原欄位並加 `note`（顯示為 ⚠）。發布前跑 `python3 tools/check_cmf.py <日期>`。

## 色彩與材質 合併版（2026-10-16 起）
有 `color_data` 的期數不再有獨立「情緒板」區塊與導覽；全部併入「色彩與材質」，順序（三個模組都用同一種小標題樣式；導覽列只有 設計新聞／色彩與材質／汽車新知）：
1. 新色彩發布（`color_data.release`，**只在當天有新年度色或新色彩報告發布時才填**；沒有就不顯示）：
   `{"date":"YYYY-MM-DD","title":"…","points":[…],"hues":[[機構, 色名, 色號, HEX, 是否官方, url],…],"pop":{"title","rows":[[色,HEX,%],…],"note","src":[名,url]},"dirs":{"title","items":[…],"src":[名,url]},"mat":{…},"sources":[[名,url],…]}`，各欄皆可省略
2. 「色彩・材質・介面動態」卡片模組（4–7 張，一類一列，見上）
3. 每日內裝配色示例（`color_data.interior`：門板＋儀表板插圖、色票、情緒、部位）
- 色票即佐證：`parts` 每項可加第 6 欄 `{"src":"來源短名","url":"..."}`；沒填時用 `evidence` 中「色名：來源」比對同名色。有來源的色票整塊可點、下方顯示來源小字；沒有來源只顯示「示意色」。
- 舊期數（無 `color_data`）照舊顯示獨立情緒板。

## 小工具 · 內裝配色（tool/）
- 頁面：`tool/index.html`（由 `tools/build.py` 的 `tool_page()` 產生，內嵌 `assets/ip-combined-template.svg`）；互動邏輯 `tool/interior.js`、樣式 `tool/tool.css`（手寫、純前端、離線可用、不連伺服器、不用 AI）。
- `tool/palettes.js` 由 build 產生：所有有 `color_data.interior` 的期數配色（套用合併插圖規則後的變數），最新一期＝開啟時的預設。
- `TOOL_FROM`（2026-10-19）起，期刊頁與首頁不再放「內裝配色」模組，改由頂部導覽「小工具」連到工具頁；更早的期刊保留原本模組不動。每日 routine 仍照常寫 `color_data.interior`（工具的資料來源）。
- 規則同合併插圖：地毯固定 `#141516`、頂棚只有淺灰／深灰兩種、門板主色 `door-upper` 永遠＝`ip-upper`。
- 情緒字典來源 `tools/moods.txt`（約 524 組、2,495 個中英文／簡體同義詞），改完執行 `python3 tools/gen_moods.py` 產生 `tool/moods.js`（需 opencc 才會自動補簡體）。找不到的詞會依子字串、共同漢字、英文編輯距離改用最相近的一組並顯示提示；完全沒有才列熱門關鍵字。原本約 196 組，以色相／飽和度／明度範圍描述；依 6 種配色規則（類比、互補點綴、分裂互補、單色、三角、中性＋亮點）決定性產生組合（同樣關鍵字永遠得到同樣結果）。
- 材質為 SVG pattern／gradient 疊層（織布、皮紋、咬花、金屬髮絲紋、鋼琴烤漆、碳纖維、打孔皮、無紋理、預設）。分享連結把配色、材質、頂棚寫在 URL hash。
