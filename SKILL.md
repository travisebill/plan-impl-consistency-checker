---
name: plan-impl-consistency-checker
description: 自動比對 plan 文件與程式碼的關鍵字串是否一致,提早抓出「plan 寫一套,code 做一套」的問題。整合 pre-commit hook,讓 Ruka 提 PR 前就自動攔截。
---

# Plan vs Implementation 一致性檢查工具

## 觸發時機

- **Ruka 提 PR 前**: 必跑,0 warnings 才能 push
- **Ryo code review 開始**: 必跑,確認 Ruka 跑過
- **Mame QA 收尾(Phase 完成)**: 跑全套 plan files

## 安裝

```bash
# 在使用此 skill 的專案根目錄執行
python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/install.py
```

## 手動使用

```bash
python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/check_plan_impl_consistency.py \
  --plan docs/changes/phase-l-cloud-saas/03-plan.md \
  --scope src/,scripts/
```

## 豁免管理

在專案根目錄放 `.consistency_ignore.yaml`:

```yaml
phase_l:
  - key: "gamelogs/cpbl_full_{date}.json"
    reason: "Rebuild snapshot 與增量爬蟲 jsonl.gz 並存"
    expires: "phase-l-completion"
```

## 詳見

- `README.md` — 完整使用文件
- `check_plan_impl_consistency.py` — 主程式
- `tests/` — TDD 測試
