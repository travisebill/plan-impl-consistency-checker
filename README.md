# Plan vs Implementation 一致性檢查工具

> 自動比對 plan 文件與程式碼的關鍵字串是否一致，提早抓出「plan 寫一套，code 做一套」的問題。

## 安裝

在你想使用這個工具的專案根目錄執行：

```bash
python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/install.py
```

這會在專案的 `.git/hooks/pre-commit` 寫入鉤子。以後每次 `git commit` 都會自動檢查。

## 手動使用

```bash
python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/check_plan_impl_consistency.py \
  --plan docs/changes/phase-l-cloud-saas/03-plan.md \
  --scope src/scraper/,scripts/
```

### 自動發現 plan 文件

```bash
python check_plan_impl_consistency.py \
  --auto-discover \
  --scope src/,scripts/
```

這會自動掃描 `docs/changes/**/03-plan.md` 和 `docs/designs/*.md`。

### 只檢查特定類別

```bash
# 只檢查 R2 key
python check_plan_impl_consistency.py --plan ... --category r2_key

# 只檢查環境變數
python check_plan_impl_consistency.py --plan ... --category env_var
```

### 使用豁免清單

```bash
python check_plan_impl_consistency.py \
  --plan ... \
  --ignore-file .consistency_ignore.yaml
```

## 支援的關鍵字類別

| 類別 | 說明 | Plan 範例 | Code 範例 |
|------|------|----------|----------|
| `r2_key` | R2 物件 key | `gamelogs/{date}.jsonl.gz` | `f"gamelogs/cpbl_full_{date}.json"` |
| `env_var` | 環境變數名稱 | `R2_ACCOUNT_ID` | `os.environ["R2_ACCOUNT_ID"]` |
| `api_path` | API 路徑 | `/api/v1/health` | `"/api/v1/health"` |
| `func_sig` | 函式簽名 | `def upload_file(path, key)` | `def upload_file(local_path, remote_key)` |
| `error_code` | 錯誤碼常量 | `R2_UPLOAD_FAILED` | `NETWORK_TIMEOUT_ERROR` |

## 豁免管理

在專案根目錄建立 `.consistency_ignore.yaml`：

```yaml
phase_l:
  - key: "gamelogs/cpbl_full_{date}.json"
    reason: "Rebuild snapshot 與增量爬蟲 jsonl.gz 並存，plan 已確認"
    expires: "phase-l-completion"

  - key: "R2_ACCOUNT_ID"
    reason: "env var,plan L.1.1 已說明"
    expires: "never"
```

`expires` 可用：
- `"never"` — 永遠豁免
- `"phase-l-completion"` — Phase L 完成後過期（目前僅 warn，不自動刪除）
- 日期如 `"2026-09-01"` — 到期後過期

## 輸出格式

### 文字報告（預設）

```
⚠️  共 2 個一致性警告：

  [r2_key] 📄 Plan 提到「gamelogs/{date}.jsonl.gz」但 Code 中未找到
  [r2_key] 💻 Code 使用「gamelogs/cpbl_full_{date}.json」但 Plan 未記載
```

### JSON 報告

```bash
python check_plan_impl_consistency.py --plan ... --output-format json
```

```json
{
  "total_warnings": 2,
  "warnings": [
    {
      "category": "r2_key",
      "plan_key": "gamelogs/{date}.jsonl.gz",
      "code_key": "gamelogs/cpbl_full_{date}.json",
      "message": "📄 Plan 提到..."
    }
  ]
}
```

## 測試

```bash
cd ~/.openclaw/workspace/skills/plan-impl-consistency-checker
python3 -m pytest tests/ -v
```

## 架構

```
check_plan_impl_consistency.py
├── R2KeyExtractor        # 抽 R2 object key
├── EnvVarExtractor      # 抽環境變數名稱
├── ApiPathExtractor     # 抽 API 路徑
├── FunctionSigExtractor # 抽函式簽名
├── ErrorCodeExtractor  # 抽錯誤碼常量
├── ConsistencyChecker   # 比對 + 豁免 + 報告
├── scan_directory()     # 掃描程式碼目錄
├── discover_plan_files() # 自動發現 plan 文件
└── main()              # CLI 進入點

bin/install.py          # Pre-commit hook 安裝腳本
```
