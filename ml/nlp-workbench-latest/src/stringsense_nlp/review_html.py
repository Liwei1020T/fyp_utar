from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Sequence

import pandas as pd

from .annotation import ALLOWED_LABELS
from .annotation import label_column


ASPECT_DISPLAY_NAMES = {
    "attack": "Attack / Repulsion",
    "comfort": "Comfort",
    "control": "Control",
    "durability": "Durability",
    "elasticity": "Elasticity",
    "sound": "Sound",
    "string_movement": "String movement",
    "tension_retention": "Tension retention",
    "value_for_money": "Value for money",
}


def build_review_payload(
    draft: pd.DataFrame,
    evidence: pd.DataFrame,
    aspects: Sequence[str],
    run_id: str,
    draft_sha256: str,
    evidence_sha256: str,
) -> dict[str, object]:
    required_draft = {
        "annotation_id",
        "sample_number",
        "review_id",
        "raw_string_name",
        "canonical_string_name",
        "language",
        "raw_text",
        "normalized_text",
        "annotator_notes",
        *[label_column(aspect) for aspect in aspects],
    }
    missing_draft = sorted(required_draft.difference(draft.columns))
    if missing_draft:
        raise ValueError(f"Annotation draft is missing columns: {missing_draft}")
    if draft["annotation_id"].duplicated().any():
        raise ValueError("Annotation draft IDs must be unique")

    required_evidence = {
        "annotation_id",
        "review_id",
        "aspect",
        "label_text",
        "suggested_label",
        "needs_manual_review",
        "conversion_rule",
    }
    missing_evidence = sorted(required_evidence.difference(evidence.columns))
    if missing_evidence:
        raise ValueError(f"Annotation evidence is missing columns: {missing_evidence}")
    if evidence.duplicated(["annotation_id", "aspect"]).any():
        raise ValueError("Annotation evidence review-aspect rows must be unique")

    allowed = set(ALLOWED_LABELS)
    evidence_index = evidence.set_index(["annotation_id", "aspect"])
    reviews: list[dict[str, object]] = []
    for row in draft.to_dict("records"):
        annotation_id = str(row["annotation_id"])
        aspect_rows: dict[str, object] = {}
        for aspect in aspects:
            key = (annotation_id, aspect)
            if key not in evidence_index.index:
                raise ValueError(f"Missing evidence for {annotation_id}/{aspect}")
            evidence_row = evidence_index.loc[key]
            suggested = str(row[label_column(aspect)]).strip()
            if suggested not in allowed:
                raise ValueError(f"Invalid draft label for {annotation_id}/{aspect}")
            aspect_rows[aspect] = {
                "initialLabel": suggested,
                "silverLabel": str(evidence_row["label_text"]),
                "needsManualReview": str(evidence_row["needs_manual_review"])
                in {"1", "true", "True"},
                "conversionRule": str(evidence_row["conversion_rule"]),
            }
        reviews.append(
            {
                "annotationId": annotation_id,
                "sampleNumber": int(row["sample_number"]),
                "reviewId": str(row["review_id"]),
                "rawStringName": str(row["raw_string_name"]),
                "canonicalStringName": str(row["canonical_string_name"]),
                "language": str(row["language"]),
                "rawText": str(row["raw_text"]),
                "normalizedText": str(row["normalized_text"]),
                "fields": {str(key): str(value) for key, value in row.items()},
                "aspects": aspect_rows,
            }
        )

    expected_evidence_rows = len(draft) * len(aspects)
    if len(evidence) != expected_evidence_rows:
        raise ValueError(
            f"Expected {expected_evidence_rows} evidence rows, found {len(evidence)}"
        )
    return {
        "schemaVersion": "stringsense.annotation-review-html.v1",
        "runId": run_id,
        "generatedAt": datetime.now(UTC).isoformat(),
        "source": {
            "draftSha256": draft_sha256,
            "evidenceSha256": evidence_sha256,
        },
        "sourceColumns": [str(column) for column in draft.columns],
        "aspects": [
            {"id": aspect, "name": ASPECT_DISPLAY_NAMES.get(aspect, aspect)}
            for aspect in aspects
        ],
        "allowedLabels": list(ALLOWED_LABELS),
        "reviews": reviews,
    }


def render_annotation_review_html(payload: dict[str, object]) -> str:
    payload_json = (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return HTML_SHELL.replace("__PAYLOAD_JSON__", payload_json)


HTML_SHELL = r"""<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>StringSense · Annotation Review</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b0d12;
      --panel: #121620;
      --panel-2: #181d29;
      --line: #2a3140;
      --text: #e8ebf2;
      --muted: #9099aa;
      --accent: #67e8b3;
      --accent-2: #58a6ff;
      --amber: #f5bd4f;
      --red: #ff6b7a;
      --radius: 12px;
      font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--text); min-height: 100vh; }
    button, input, select, textarea { font: inherit; }
    button, select, input, textarea {
      color: var(--text); background: var(--panel-2); border: 1px solid var(--line);
      border-radius: 8px;
    }
    button { cursor: pointer; padding: 8px 11px; }
    button:hover { border-color: #455169; }
    button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
      outline: 2px solid var(--accent-2); outline-offset: 2px;
    }
    .topbar {
      position: sticky; top: 0; z-index: 20; display: flex; align-items: center;
      justify-content: space-between; gap: 20px; padding: 14px 20px;
      background: rgba(11, 13, 18, .96); border-bottom: 1px solid var(--line);
      backdrop-filter: blur(12px);
    }
    .brand { display: flex; align-items: baseline; gap: 10px; }
    .brand h1 { font-size: 18px; margin: 0; letter-spacing: -.02em; }
    .brand span { color: var(--muted); font-size: 12px; }
    .progress-wrap { display: flex; align-items: center; gap: 12px; min-width: 310px; }
    .progress-track { height: 7px; flex: 1; background: #202635; border-radius: 99px; overflow: hidden; }
    .progress-bar { height: 100%; width: 0; background: linear-gradient(90deg, var(--accent-2), var(--accent)); }
    .progress-text { font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; white-space: nowrap; }
    .notice {
      margin: 14px 20px 0; padding: 11px 14px; border: 1px solid rgba(245,189,79,.35);
      background: rgba(245,189,79,.07); color: #f8d78f; border-radius: var(--radius); font-size: 13px;
    }
    .workspace { display: grid; grid-template-columns: 330px minmax(0, 1fr); min-height: calc(100vh - 128px); }
    .sidebar { border-right: 1px solid var(--line); padding: 16px; min-width: 0; }
    .filters { display: grid; gap: 9px; position: sticky; top: 75px; }
    .search { width: 100%; padding: 10px 12px; }
    .filter-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    select { width: 100%; padding: 8px; }
    .presets { display: flex; flex-wrap: wrap; gap: 6px; }
    .preset { padding: 6px 8px; color: var(--muted); font-size: 12px; }
    .preset.active { color: var(--text); border-color: var(--accent-2); background: rgba(88,166,255,.12); }
    .list-meta { display: flex; justify-content: space-between; color: var(--muted); font-size: 12px; margin: 5px 1px; }
    .review-list { height: calc(100vh - 315px); overflow: auto; display: grid; gap: 7px; padding-right: 3px; }
    .review-item { text-align: left; padding: 10px; display: grid; gap: 5px; width: 100%; }
    .review-item.active { border-color: var(--accent-2); background: rgba(88,166,255,.1); }
    .review-item.done { border-left: 3px solid var(--accent); }
    .item-head { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; }
    .item-string { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .item-text { color: var(--muted); font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .badges { display: flex; gap: 5px; flex-wrap: wrap; }
    .badge { font: 10px ui-monospace, SFMono-Regular, Menlo, monospace; padding: 2px 5px; border-radius: 99px; background: #242b3a; color: var(--muted); }
    .badge.flag { background: rgba(245,189,79,.13); color: var(--amber); }
    main { min-width: 0; padding: 22px clamp(18px, 3vw, 42px) 120px; }
    .empty { margin: 80px auto; max-width: 520px; text-align: center; color: var(--muted); }
    .review-header { display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; }
    .eyebrow { color: var(--accent); font: 11px ui-monospace, SFMono-Regular, Menlo, monospace; text-transform: uppercase; }
    h2 { font-size: clamp(22px, 3vw, 32px); margin: 7px 0 4px; letter-spacing: -.03em; }
    .review-subtitle { color: var(--muted); font-size: 13px; }
    .nav-actions { display: flex; gap: 7px; flex-wrap: wrap; justify-content: flex-end; }
    .primary { background: var(--accent); color: #07130e; border-color: var(--accent); font-weight: 700; }
    .review-text { margin: 22px 0; padding: 20px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); font-size: 17px; line-height: 1.8; white-space: pre-wrap; }
    details { color: var(--muted); font-size: 12px; margin-top: -13px; margin-bottom: 20px; }
    details p { white-space: pre-wrap; padding: 10px; background: var(--panel); border-radius: 8px; }
    .aspect-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin: 18px 0 9px; }
    .aspect-toolbar h3 { margin: 0; font-size: 15px; }
    .aspect-list { display: grid; gap: 8px; }
    .aspect-row { display: grid; grid-template-columns: minmax(150px, .75fr) minmax(180px, 1fr) minmax(170px, .9fr) auto; gap: 12px; align-items: center; background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 11px 12px; }
    .aspect-row.flagged { border-left: 3px solid var(--amber); }
    .aspect-row.reviewed { border-left: 3px solid var(--accent); }
    .aspect-row.changed { background: rgba(88,166,255,.06); }
    .aspect-name strong { display: block; font-size: 13px; }
    .aspect-name code { color: var(--muted); font-size: 10px; }
    .label-select { min-width: 170px; }
    .source { color: var(--muted); font-size: 11px; line-height: 1.45; }
    .source b { color: var(--text); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
    .review-check { display: flex; align-items: center; gap: 7px; color: var(--muted); font-size: 12px; white-space: nowrap; }
    input[type="checkbox"] { accent-color: var(--accent); width: 16px; height: 16px; }
    .notes { margin-top: 18px; }
    .notes label { display: block; color: var(--muted); font-size: 12px; margin-bottom: 6px; }
    textarea { width: 100%; min-height: 90px; padding: 11px; resize: vertical; }
    .dock { position: fixed; bottom: 0; left: 330px; right: 0; z-index: 15; background: rgba(11,13,18,.97); border-top: 1px solid var(--line); padding: 11px clamp(18px,3vw,42px); display: flex; justify-content: space-between; gap: 12px; align-items: center; }
    .summary { color: var(--muted); font-size: 12px; }
    .dock-actions { display: flex; gap: 7px; flex-wrap: wrap; justify-content: flex-end; }
    .hidden { display: none !important; }
    .modal { position: fixed; inset: 0; z-index: 50; display: grid; place-items: center; background: rgba(0,0,0,.72); padding: 18px; }
    .modal-card { width: min(720px, 100%); max-height: 85vh; overflow: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 20px; }
    .modal-card h3 { margin-top: 0; }
    .modal-card li { margin: 8px 0; color: var(--muted); }
    .modal-card footer { display: flex; justify-content: flex-end; margin-top: 16px; }
    .toast { position: fixed; right: 18px; top: 72px; z-index: 100; background: #243047; border: 1px solid #43516a; padding: 9px 12px; border-radius: 8px; opacity: 0; transform: translateY(-6px); transition: .2s; pointer-events: none; }
    .toast.show { opacity: 1; transform: translateY(0); }
    @media (max-width: 900px) {
      .topbar { align-items: flex-start; }
      .progress-wrap { min-width: 180px; }
      .workspace { grid-template-columns: 1fr; }
      .sidebar { border-right: 0; border-bottom: 1px solid var(--line); }
      .filters { position: static; }
      .review-list { height: 220px; }
      .dock { left: 0; }
      .aspect-row { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 600px) {
      .topbar { flex-direction: column; }
      .progress-wrap { width: 100%; }
      .notice { margin-inline: 10px; }
      .sidebar, main { padding: 12px; }
      .review-header { display: block; }
      .nav-actions { justify-content: flex-start; margin-top: 12px; }
      .aspect-row { grid-template-columns: 1fr; }
      .dock { position: static; display: grid; }
      .dock-actions { justify-content: flex-start; }
      main { padding-bottom: 20px; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand"><h1>StringSense Annotation Review</h1><span>450-review pilot · offline</span></div>
    <div class="progress-wrap" aria-label="Review progress">
      <div class="progress-track"><div class="progress-bar" id="progressBar"></div></div>
      <div class="progress-text" id="progressText">0 / 4050</div>
    </div>
  </header>
  <div class="notice"><strong>AI/Silver 辅助草稿，不是 Gold。</strong> 每个 aspect 必须由你检查后勾选“已审”。页面自动保存在本浏览器。</div>
  <div class="workspace">
    <aside class="sidebar">
      <div class="filters">
        <input class="search" id="search" type="search" placeholder="搜索 review、球线或 ID" aria-label="Search reviews">
        <div class="filter-grid">
          <select id="statusFilter" aria-label="Review status">
            <option value="pending">待审</option><option value="all">全部</option><option value="reviewed">已完成</option>
          </select>
          <select id="priorityFilter" aria-label="Review priority">
            <option value="flagged">重点项</option><option value="all">所有优先级</option>
          </select>
          <select id="stringFilter" aria-label="String filter"><option value="all">所有球线</option></select>
          <select id="languageFilter" aria-label="Language filter"><option value="all">所有语言</option></select>
          <select id="aspectFilter" aria-label="Aspect filter"><option value="all">所有 aspects</option></select>
          <select id="labelFilter" aria-label="Label filter"><option value="all">所有标签</option></select>
        </div>
        <div class="presets" aria-label="Filter presets">
          <button class="preset active" data-preset="flagged">重点待审</button>
          <button class="preset" data-preset="pending">全部待审</button>
          <button class="preset" data-preset="mixed">Mixed 待审</button>
          <button class="preset" data-preset="reviewed">已完成</button>
        </div>
        <div class="list-meta"><span id="resultCount">0 reviews</span><span id="changedCount">0 changed</span></div>
        <div class="review-list" id="reviewList"></div>
      </div>
    </aside>
    <main id="detail"></main>
  </div>
  <div class="dock">
    <div class="summary" id="summaryOutput">尚未审查任何标签。</div>
    <div class="dock-actions">
      <button id="guideButton">标签指南</button>
      <button id="copySummary">复制摘要</button>
      <button id="backupButton">备份进度 JSON</button>
      <button id="importButton">导入进度</button>
      <button class="primary" id="exportButton">导出审查 CSV</button>
      <input class="hidden" id="importInput" type="file" accept="application/json,.json">
    </div>
  </div>
  <div class="modal hidden" id="guideModal" role="dialog" aria-modal="true" aria-labelledby="guideTitle">
    <div class="modal-card">
      <h3 id="guideTitle">快速标签指南</h3>
      <ul>
        <li><b>not_mentioned</b>：该 aspect 没有表达，不能合理推断。</li>
        <li><b>positive / negative</b>：对该 aspect 有明确正面／负面评价。</li>
        <li><b>neutral</b>：只陈述该 aspect，没有正负态度。</li>
        <li><b>mixed</b>：同一个 aspect 同时出现正面和负面意见。</li>
        <li><b>uncertain</b>：文本相关但无法可靠判断，必须在 notes 说明。</li>
        <li>不要把价格、磅数、产品名本身当作 sentiment。</li>
      </ul>
      <footer><button id="closeGuide">关闭</button></footer>
    </div>
  </div>
  <div class="toast" id="toast" role="status"></div>
  <script type="application/json" id="payload">__PAYLOAD_JSON__</script>
  <script>
    'use strict';
    const DATA = JSON.parse(document.getElementById('payload').textContent);
    const STORAGE_KEY = `stringsense-review:${DATA.source.draftSha256}`;
    const aspectIds = DATA.aspects.map(item => item.id);
    const reviewById = new Map(DATA.reviews.map(review => [review.annotationId, review]));
    const initialState = () => ({
      selectedId: DATA.reviews[0]?.annotationId || null,
      labels: Object.fromEntries(DATA.reviews.map(review => [review.annotationId, Object.fromEntries(aspectIds.map(aspect => [aspect, review.aspects[aspect].initialLabel]))])),
      reviewed: Object.fromEntries(DATA.reviews.map(review => [review.annotationId, Object.fromEntries(aspectIds.map(aspect => [aspect, false]))])),
      notes: Object.fromEntries(DATA.reviews.map(review => [review.annotationId, ''])),
      annotatorId: 'project_owner',
      filters: { query: '', status: 'pending', priority: 'flagged', stringName: 'all', language: 'all', aspect: 'all', label: 'all' }
    });
    let state = loadState();
    let filteredReviews = [];

    function loadState() {
      const base = initialState();
      try {
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
        if (!saved || saved.sourceHash !== DATA.source.draftSha256) return base;
        return { ...base, ...saved.state, filters: { ...base.filters, ...(saved.state.filters || {}) } };
      } catch { return base; }
    }
    function saveState() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ sourceHash: DATA.source.draftSha256, savedAt: new Date().toISOString(), state }));
    }
    const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
    const relevantAspects = () => state.filters.aspect === 'all' ? aspectIds : [state.filters.aspect];
    const isReviewed = (id, aspect) => Boolean(state.reviewed[id]?.[aspect]);
    const isReviewComplete = review => aspectIds.every(aspect => isReviewed(review.annotationId, aspect));
    const hasPendingRelevant = review => relevantAspects().some(aspect => !isReviewed(review.annotationId, aspect));
    const hasFlaggedRelevant = review => relevantAspects().some(aspect => review.aspects[aspect].needsManualReview);
    const changedFor = (review, aspect) => state.labels[review.annotationId][aspect] !== review.aspects[aspect].initialLabel;

    function populateFilters() {
      const fill = (id, values) => {
        const select = document.getElementById(id);
        for (const value of [...new Set(values)].sort()) select.insertAdjacentHTML('beforeend', `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`);
      };
      fill('stringFilter', DATA.reviews.map(item => item.canonicalStringName));
      fill('languageFilter', DATA.reviews.map(item => item.language));
      const aspectSelect = document.getElementById('aspectFilter');
      for (const aspect of DATA.aspects) aspectSelect.insertAdjacentHTML('beforeend', `<option value="${aspect.id}">${escapeHtml(aspect.name)}</option>`);
      fill('labelFilter', DATA.allowedLabels);
    }

    function applyFilters() {
      const query = state.filters.query.trim().toLocaleLowerCase();
      filteredReviews = DATA.reviews.filter(review => {
        if (query && ![review.reviewId, review.annotationId, review.rawStringName, review.canonicalStringName, review.rawText].join(' ').toLocaleLowerCase().includes(query)) return false;
        if (state.filters.stringName !== 'all' && review.canonicalStringName !== state.filters.stringName) return false;
        if (state.filters.language !== 'all' && review.language !== state.filters.language) return false;
        if (state.filters.status === 'pending' && !hasPendingRelevant(review)) return false;
        if (state.filters.status === 'reviewed' && hasPendingRelevant(review)) return false;
        if (state.filters.priority === 'flagged' && !hasFlaggedRelevant(review)) return false;
        if (state.filters.label !== 'all' && !relevantAspects().some(aspect => state.labels[review.annotationId][aspect] === state.filters.label)) return false;
        return true;
      });
      if (!filteredReviews.some(review => review.annotationId === state.selectedId)) state.selectedId = filteredReviews[0]?.annotationId || null;
    }

    function renderList() {
      const list = document.getElementById('reviewList');
      document.getElementById('resultCount').textContent = `${filteredReviews.length} reviews`;
      if (!filteredReviews.length) { list.innerHTML = '<div class="empty">没有符合筛选条件的 review。</div>'; return; }
      list.innerHTML = filteredReviews.map(review => {
        const flags = aspectIds.filter(aspect => review.aspects[aspect].needsManualReview && !isReviewed(review.annotationId, aspect)).length;
        const done = isReviewComplete(review);
        return `<button class="review-item ${review.annotationId === state.selectedId ? 'active' : ''} ${done ? 'done' : ''}" data-id="${escapeHtml(review.annotationId)}">
          <div class="item-head"><b>#${review.sampleNumber} · ${escapeHtml(review.canonicalStringName)}</b><span>${done ? '✓' : ''}</span></div>
          <div class="item-text">${escapeHtml(review.rawText)}</div>
          <div class="badges"><span class="badge">${escapeHtml(review.language)}</span>${flags ? `<span class="badge flag">${flags} flagged</span>` : ''}</div>
        </button>`;
      }).join('');
    }

    function renderDetail() {
      const detail = document.getElementById('detail');
      const review = reviewById.get(state.selectedId);
      if (!review) { detail.innerHTML = '<div class="empty"><h2>没有结果</h2><p>调整左侧筛选条件。</p></div>'; return; }
      const visibleAspects = state.filters.aspect === 'all' ? DATA.aspects : DATA.aspects.filter(item => item.id === state.filters.aspect);
      const position = filteredReviews.findIndex(item => item.annotationId === review.annotationId);
      detail.innerHTML = `
        <div class="review-header">
          <div><div class="eyebrow">Review ${review.sampleNumber} / ${DATA.reviews.length}</div><h2>${escapeHtml(review.canonicalStringName)}</h2><div class="review-subtitle">${escapeHtml(review.reviewId)} · ${escapeHtml(review.language)} · raw: ${escapeHtml(review.rawStringName)}</div></div>
          <div class="nav-actions"><button id="previousButton" ${position <= 0 ? 'disabled' : ''}>← 上一个</button><button id="nextButton" ${position >= filteredReviews.length - 1 ? 'disabled' : ''}>下一个 →</button><button class="primary" id="markReviewButton">${visibleAspects.length === aspectIds.length ? '全部标记已审' : `标记 ${escapeHtml(visibleAspects[0].name)} 已审`}</button></div>
        </div>
        <div class="review-text">${escapeHtml(review.rawText)}</div>
        <details><summary>查看 normalized text</summary><p>${escapeHtml(review.normalizedText)}</p></details>
        <div class="aspect-toolbar"><h3>Aspect labels</h3><span class="review-subtitle">黄色＝原规则要求重点复核；蓝底＝已修改</span></div>
        <div class="aspect-list">${visibleAspects.map(aspect => renderAspectRow(review, aspect)).join('')}</div>
        <div class="notes"><label for="reviewNotes">你的备注</label><textarea id="reviewNotes" placeholder="记录 uncertain 原因或修改依据">${escapeHtml(state.notes[review.annotationId] || '')}</textarea></div>`;
      document.getElementById('previousButton').onclick = () => selectAt(position - 1);
      document.getElementById('nextButton').onclick = () => selectAt(position + 1);
      document.getElementById('markReviewButton').onclick = () => {
        for (const aspect of visibleAspects) state.reviewed[review.annotationId][aspect.id] = true;
        updateAll();
      };
      detail.querySelectorAll('[data-label]').forEach(select => select.onchange = event => {
        const aspect = event.target.dataset.label;
        state.labels[review.annotationId][aspect] = event.target.value;
        state.reviewed[review.annotationId][aspect] = true;
        updateAll();
      });
      detail.querySelectorAll('[data-reviewed]').forEach(box => box.onchange = event => {
        state.reviewed[review.annotationId][event.target.dataset.reviewed] = event.target.checked;
        updateAll();
      });
      document.getElementById('reviewNotes').oninput = event => { state.notes[review.annotationId] = event.target.value; saveState(); updateStats(); };
    }

    function renderAspectRow(review, aspect) {
      const evidence = review.aspects[aspect.id];
      const current = state.labels[review.annotationId][aspect.id];
      const reviewed = isReviewed(review.annotationId, aspect.id);
      const changed = changedFor(review, aspect.id);
      return `<div class="aspect-row ${evidence.needsManualReview ? 'flagged' : ''} ${reviewed ? 'reviewed' : ''} ${changed ? 'changed' : ''}">
        <div class="aspect-name"><strong>${escapeHtml(aspect.name)}</strong><code>${aspect.id}</code></div>
        <select class="label-select" data-label="${aspect.id}" aria-label="${escapeHtml(aspect.name)} label">${DATA.allowedLabels.map(label => `<option value="${label}" ${label === current ? 'selected' : ''}>${label}</option>`).join('')}</select>
        <div class="source">Silver: <b>${escapeHtml(evidence.silverLabel)}</b>${evidence.conversionRule !== 'identity' ? `<br>${escapeHtml(evidence.conversionRule)}` : ''}${evidence.needsManualReview ? '<br><span style="color:var(--amber)">需要重点复核</span>' : ''}</div>
        <label class="review-check"><input type="checkbox" data-reviewed="${aspect.id}" ${reviewed ? 'checked' : ''}> 已审</label>
      </div>`;
    }

    function selectAt(index) {
      if (index < 0 || index >= filteredReviews.length) return;
      state.selectedId = filteredReviews[index].annotationId;
      saveState(); renderList(); renderDetail(); window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function updateStats() {
      const total = DATA.reviews.length * aspectIds.length;
      let reviewed = 0, changed = 0, flaggedPending = 0;
      for (const review of DATA.reviews) for (const aspect of aspectIds) {
        if (isReviewed(review.annotationId, aspect)) reviewed++;
        if (changedFor(review, aspect)) changed++;
        if (review.aspects[aspect].needsManualReview && !isReviewed(review.annotationId, aspect)) flaggedPending++;
      }
      document.getElementById('progressBar').style.width = `${reviewed / total * 100}%`;
      document.getElementById('progressText').textContent = `${reviewed} / ${total}`;
      document.getElementById('changedCount').textContent = `${changed} changed`;
      document.getElementById('summaryOutput').textContent = `已审 ${reviewed}/${total}；修改 ${changed}；重点待审 ${flaggedPending}。`;
    }

    function updateAll() { applyFilters(); renderList(); renderDetail(); updateStats(); saveState(); }
    function setPreset(name) {
      const presets = {
        flagged: { status: 'pending', priority: 'flagged', label: 'all' },
        pending: { status: 'pending', priority: 'all', label: 'all' },
        mixed: { status: 'pending', priority: 'all', label: 'mixed' },
        reviewed: { status: 'reviewed', priority: 'all', label: 'all' }
      };
      Object.assign(state.filters, presets[name]);
      syncFilterControls();
      document.querySelectorAll('.preset').forEach(button => button.classList.toggle('active', button.dataset.preset === name));
      updateAll();
    }
    function syncFilterControls() {
      document.getElementById('search').value = state.filters.query;
      document.getElementById('statusFilter').value = state.filters.status;
      document.getElementById('priorityFilter').value = state.filters.priority;
      document.getElementById('stringFilter').value = state.filters.stringName;
      document.getElementById('languageFilter').value = state.filters.language;
      document.getElementById('aspectFilter').value = state.filters.aspect;
      document.getElementById('labelFilter').value = state.filters.label;
    }

    function csvEscape(value) {
      const text = String(value ?? '');
      return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
    }
    function download(name, content, type) {
      const url = URL.createObjectURL(new Blob([content], { type }));
      const link = document.createElement('a'); link.href = url; link.download = name; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
    function exportCsv() {
      const extra = ['aspect_review_status_json', 'reviewed_label_count', 'review_session_id'];
      const headers = [...new Set([...DATA.sourceColumns, ...extra])];
      const rows = DATA.reviews.map(review => {
        const row = { ...review.fields };
        for (const aspect of aspectIds) row[`${aspect}_label`] = state.labels[review.annotationId][aspect];
        const statuses = Object.fromEntries(aspectIds.map(aspect => [aspect, isReviewed(review.annotationId, aspect) ? 'reviewed' : 'pending']));
        const count = Object.values(statuses).filter(value => value === 'reviewed').length;
        row.annotator_id = state.annotatorId || 'project_owner';
        row.annotator_notes = state.notes[review.annotationId] || '';
        row.annotation_provenance = count === aspectIds.length ? 'human_reviewed_ai_assisted' : 'automatic_silver_conversion_not_human';
        row.human_review_status = count === aspectIds.length ? 'reviewed' : `partial_${count}_of_${aspectIds.length}`;
        row.aspect_review_status_json = JSON.stringify(statuses);
        row.reviewed_label_count = count;
        row.review_session_id = DATA.runId;
        return headers.map(header => csvEscape(row[header])).join(',');
      });
      download('stringsense_450_reviewed_annotations.csv', '\ufeff' + [headers.join(','), ...rows].join('\r\n'), 'text/csv;charset=utf-8');
      toast('CSV 已导出');
    }
    function backupState() {
      download('stringsense_annotation_review_progress.json', JSON.stringify({ sourceHash: DATA.source.draftSha256, exportedAt: new Date().toISOString(), state }, null, 2), 'application/json');
      toast('进度备份已导出');
    }
    async function importState(file) {
      try {
        const payload = JSON.parse(await file.text());
        if (payload.sourceHash !== DATA.source.draftSha256) throw new Error('备份来自不同的标注草稿');
        state = { ...initialState(), ...payload.state, filters: { ...initialState().filters, ...(payload.state.filters || {}) } };
        syncFilterControls(); updateAll(); toast('进度已恢复');
      } catch (error) { alert(`无法导入：${error.message}`); }
    }
    async function copySummary() {
      await navigator.clipboard.writeText(document.getElementById('summaryOutput').textContent + ` Run: ${DATA.runId}`);
      toast('摘要已复制');
    }
    function toast(message) {
      const node = document.getElementById('toast'); node.textContent = message; node.classList.add('show');
      setTimeout(() => node.classList.remove('show'), 1300);
    }

    function bindControls() {
      const bindings = {
        search: ['query', 'input'], statusFilter: ['status', 'change'], priorityFilter: ['priority', 'change'],
        stringFilter: ['stringName', 'change'], languageFilter: ['language', 'change'], aspectFilter: ['aspect', 'change'], labelFilter: ['label', 'change']
      };
      for (const [id, [field, event]] of Object.entries(bindings)) document.getElementById(id).addEventListener(event, e => { state.filters[field] = e.target.value; document.querySelectorAll('.preset').forEach(button => button.classList.remove('active')); updateAll(); });
      document.getElementById('reviewList').onclick = event => { const item = event.target.closest('[data-id]'); if (item) { state.selectedId = item.dataset.id; saveState(); renderList(); renderDetail(); } };
      document.querySelectorAll('.preset').forEach(button => button.onclick = () => setPreset(button.dataset.preset));
      document.getElementById('exportButton').onclick = exportCsv;
      document.getElementById('backupButton').onclick = backupState;
      document.getElementById('copySummary').onclick = copySummary;
      document.getElementById('importButton').onclick = () => document.getElementById('importInput').click();
      document.getElementById('importInput').onchange = event => { if (event.target.files[0]) importState(event.target.files[0]); };
      document.getElementById('guideButton').onclick = () => document.getElementById('guideModal').classList.remove('hidden');
      document.getElementById('closeGuide').onclick = () => document.getElementById('guideModal').classList.add('hidden');
      document.getElementById('guideModal').onclick = event => { if (event.target.id === 'guideModal') event.currentTarget.classList.add('hidden'); };
      document.addEventListener('keydown', event => {
        if (!(event.ctrlKey || event.metaKey)) return;
        const index = filteredReviews.findIndex(item => item.annotationId === state.selectedId);
        if (event.key === 'ArrowLeft') { event.preventDefault(); selectAt(index - 1); }
        if (event.key === 'ArrowRight') { event.preventDefault(); selectAt(index + 1); }
      });
    }

    populateFilters(); syncFilterControls(); bindControls(); updateAll();
  </script>
</body>
</html>
"""
