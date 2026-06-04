# Plan vs Implementation 一致性檢查工具

> 自動比對 plan 文件與程式碼的關鍵字串是否一致,提早抓出「plan 寫一套,code 做一套」的問題。

[![GitHub](https://img.shields.io/badge/GitHub-travisebill%2Fplan--impl--consistency--checker-blue)](https://github.com/travisebill/plan-impl-consistency-checker)
[![Status](https://img.shields.io/badge/status-skeleton-yellow)]()

## 為什麼需要這個工具?

在 AI 輔助開發流程中,**plan 文件**(PM 寫的設計/實作計畫)和**程式碼**(工程師實作的結果)之間常常會出現落差:

- Plan 寫 `gamelogs/{date}.jsonl.gz`,code 寫 `gamelogs/cpbl_full_{date}.json`
- Plan 寫 `def upload_file(path, key)`,code 寫 `def upload_file(local_path, remote_key, ...)`
- Plan 寫 `R2_ACCOUNT_ID`,code 卻讀 `R2_BUCKET_NAME`

這些落差**在 review 階段很難全部抓到**,因為 reviewer 看到的是「程式碼看起來合理」+「plan 看起來完整」,**卻沒有人把兩邊字串一一比對**。這個工具就是自動做這件事。

## 五大檢查類別

| # | 類型 | Plan 範例 | Code 範例 |
|---|------|----------|----------|
| 1 | **R2/S3 keys** | `gamelogs/{season}/{date}.jsonl.gz` | `f"gamelogs/cpbl_full_{date_str}.json"` |
| 2 | **Env var names** | `R2_ACCOUNT_ID` | `os.environ["R2_ACCOUNT_ID"]` |
| 3 | **API paths** | `/api/v1/health` | `"/api/v1/health"` |
| 4 | **Function signatures** | `def upload_file(path: Path, key: str)` | `def upload_file(local_path, remote_key, ...)` |
| 5 | **Error codes** | `R2_UPLOAD_FAILED` | raise exception / return False |

## 安裝

### 方式 1: 直接 clone(推薦)

```bash
git clone https://github.com/travisebill/plan-impl-consistency-checker.git \
  ~/.openclaw/workspace/skills/plan-impl-consistency-checker
```

### 方式 2: 安裝 pre-commit hook 到現有專案

```bash
# 在你的專案根目錄執行
python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/install.py
```

安裝後,**每次 `git commit` 都會自動跑一致性檢查**,0 warnings 才能 commit。

需要跳過檢查時(罕見):

```bash
git commit --no-verify -m "emergency hotfix"
```

## 使用方式

### 手動掃描單一 plan

```bash
python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/check_plan_impl_consistency.py \
  --plan docs/changes/phase-l-cloud-saas/03-plan.md \
  --scope src/scraper/,scripts/
```

### 自動發現所有 plan(新舊 Phase 都支援)

```bash
python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/check_plan_impl_consistency.py \
  --auto-discover \
  --scope src/,scripts/
```

工具會自動掃描:
- `docs/changes/phase-*/03-plan.md`(Phase L+ 新格式)
- `docs/designs/2026-*-phase-*.md`(Phase A-K 舊格式)
- `docs/designs/phase-*.md`(混合格式)

### 輸出格式

```bash
# 人讀(預設)
--output-format text

# 機器讀(CI 用)
--output-format json
```

## 豁免管理

某些落差是**刻意的**(如 plan 同時描述兩種 R2 物件佈局),這時可以用豁免清單標記。

在專案根目錄放 `.consistency_ignore.yaml`:

```yaml
phase_l:
  - key: "gamelogs/cpbl_full_{date}.json"
    reason: "Rebuild snapshot 與增量爬蟲 jsonl.gz 並存於 R2,plan 09-plan-revision-sora.md 已確認"
    expires: "phase-l-completion"

  - key: "R2_ACCOUNT_ID"
    reason: "env var,plan L.1.1 已說明,純粹是 reminder 而非未實作"
    expires: "never"
```

**重要**: 每個豁免都必須有 `reason` 和 `expires`,否則審查時無法判斷是否合理。

## 開發流程整合

### 觸發時機

- 🔴 **Ruka 提 PR 前**: 必跑,0 warnings 才能 push
- 🔴 **Ryo code review 開始**: 必跑,確認 Ruka 跑過
- 🟡 **Mame QA 收尾(Phase 完成)**: 跑全套 plan files

### 失敗處理

- **1-2 個 warnings + 理由明確** → 加豁免後通過
- **3+ 個 warnings** → 視為 plan 與 impl 不一致,需修正 plan 或 code
- **0 warnings** → 完美,commit 通過

## 跨專案適用

這個 skill 設計為**完全獨立**於任何特定專案:

```bash
# 任何專案的根目錄都能用
cd ~/my-new-project
python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/check_plan_impl_consistency.py \
  --plan docs/design.md \
  --scope src/
```

只要專案有 `docs/*.md` + `src/*.py`,就能跑。

## 開發狀態

🚧 **目前狀態: Skeleton 階段**

- [x] 初始結構(.gitignore、SKILL.md、豁免清單範例)
- [x] GitHub repo 建立
- [ ] 5 類 extractor(R2 keys、env vars、API paths、function signatures、error codes)
- [ ] ConsistencyChecker + 豁免機制
- [ ] CLI + 自動發現
- [ ] pre-commit hook 安裝腳本
- [ ] 跨專案驗證(CPBL Predictor + 全新專案)

詳見 [TDD 開發進度](https://github.com/travisebill/plan-impl-consistency-checker/commits/main)。

## 授權

MIT
