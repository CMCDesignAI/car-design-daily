# 零件圖庫網頁回報

- 前端：`report.js` → `POST https://parts-report.cmcdesignai.workers.dev`
- 儲存：R2 bucket `cdd-parts`，鍵 `reports/YYYY-MM-DD/<id>.json`（日＝**Asia/Taipei**）
- CORS：僅允許 `https://cmcdesignai.github.io`

Bot／例行讀取請用 `/workspace/parts/b2/fetch_reports.py` **live list R2**，不要只信當日早上寫入的空 `reports_cache`。晨間 0 筆不代表中午前沒有新回報。
