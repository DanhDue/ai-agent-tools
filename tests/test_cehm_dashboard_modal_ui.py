"""BDD & integration tests for Check Tasks Epic History Modal UI & shared helpers.

Covers Tier C scenarios:
- CEHM-HP-04: Roadmap click opens epic history modal, shared compact 6-stage stepper,
  4 direct tabs, timeline category filters, expandable task evidence, in-modal
  Principal/Cross-Model review round switching, HTTP error retry banner, XSS escaping.
- CEHM-EC-03: Roadmap PIC select interaction remains isolated and never opens modal.
- CEHM-ST-02: Worktree task precedence rendered accurately and active tab preserved
  across silent pollDashboard() refreshes for in-progress epics.
- CEHM-ST-03: Modal dismissal via close button, backdrop click, or Escape restores
  body overflow and stops /api/epic/history polling.
- CEHM-AR-02: Monotonic requestToken + AbortController discards stale slow response.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_TASKS_SCRIPTS_DIR = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(CHECK_TASKS_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(CHECK_TASKS_SCRIPTS_DIR))

from tasks_server import parse_review_results  # type: ignore[import-not-found]  # noqa: E402
from tests.test_rsdh_tasks_dashboard_ui import (  # noqa: E402
    _NODE_DOM_HARNESS_PREAMBLE,
    _run_node_script,
    DASHBOARD_HTML,
)


def _load_check_tasks_module() -> Any:
    """Load the skill backend check_tasks module explicitly by file path."""
    target_path = CHECK_TASKS_SCRIPTS_DIR / "check_tasks.py"
    spec = importlib.util.spec_from_file_location("_cehm_check_tasks_mod", target_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_cehm_check_tasks_mod"] = module
    spec.loader.exec_module(module)
    return module


_CEHM_HARNESS_EXTRAS = r"""
function validateDashboardSyntax() {
  new vm.Script(dashboardScript, { filename: 'tasks_dashboard.html' });
}

function extractModalMarkupById(sourceHtml, modalId) {
  const startMarker = `<div id="${modalId}"`;
  const startIdx = sourceHtml.indexOf(startMarker);
  assert.notEqual(
    startIdx,
    -1,
    `Expected element <div id="${modalId}"> in tasks_dashboard.html`,
  );
  const tagRegex = /<\/?div\b[^>]*>/gi;
  tagRegex.lastIndex = startIdx;
  let depth = 0;
  let m;
  while ((m = tagRegex.exec(sourceHtml)) !== null) {
    const token = m[0];
    if (token.startsWith('</')) {
      depth -= 1;
      if (depth === 0) {
        return sourceHtml.slice(startIdx, m.index + token.length);
      }
    } else if (!/\/>\s*$/.test(token)) {
      depth += 1;
    }
  }
  assert.fail(`Unbalanced <div> tags while extracting #${modalId}`);
  return '';
}

function patchElementTree(root) {
  if (!root || !root.style) return;
  if (typeof root.style.setProperty !== 'function') {
    root.style.setProperty = function (prop, val) {
      this[prop] = String(val);
    };
  }
  for (const ch of root.children || []) {
    patchElementTree(ch);
  }
}

function createCehmDomHarness(fetchHandler) {
  validateDashboardSyntax();
  const harness = createFakeDomHarness(fetchHandler);
  const { sandbox, doc } = harness;
  sandbox.AbortController = AbortController;
  sandbox.URLSearchParams = URLSearchParams;

  const origCreateElement = doc.createElement.bind(doc);
  doc.createElement = function (tag) {
    const el = origCreateElement(tag);
    patchElementTree(el);
    return el;
  };
  patchElementTree(doc.body);

  const modalsWrapper = doc.createElement('div');
  const crossReviewMarkup = extractModalMarkupById(html, 'modal-cross-review');
  const epicHistoryMarkup = extractModalMarkupById(html, 'modal-epic-history');
  modalsWrapper.innerHTML = `${crossReviewMarkup}\n${epicHistoryMarkup}`;
  while (modalsWrapper.children.length > 0) {
    const modalNode = modalsWrapper.children.shift();
    modalNode.parentNode = doc.body;
    patchElementTree(modalNode);
    modalNode.style.display = 'none';
    doc.body.children.push(modalNode);
    if (modalNode.id) doc._byId.set(modalNode.id, modalNode);
  }

  if (typeof sandbox.initModalClickOutside === 'function') {
    sandbox.initModalClickOutside();
  }
  return harness;
}

function makeClickEvent(targetEl) {
  return {
    type: 'click',
    target: targetEl,
    currentTarget: null,
    propagationStopped: false,
    defaultPrevented: false,
    stopPropagation() {
      this.propagationStopped = true;
    },
    preventDefault() {
      this.defaultPrevented = true;
    },
  };
}

function simulateDomClick(targetEl, ctx) {
  assert.ok(targetEl, 'simulateDomClick requires a non-null target element');
  const evt = makeClickEvent(targetEl);
  let cur = targetEl;
  while (cur && !evt.propagationStopped) {
    evt.currentTarget = cur;
    const listeners = (cur.listeners && cur.listeners.get('click')) || [];
    for (const fn of listeners) {
      if (evt.propagationStopped) break;
      fn(evt);
    }
    const onclickAttr = typeof cur.getAttribute === 'function' ? cur.getAttribute('onclick') : null;
    if (!evt.propagationStopped && onclickAttr) {
      ctx.__cehmEvt = evt;
      ctx.__cehmThis = cur;
      vm.runInContext(
        `(function(event){ ${onclickAttr} }).call(__cehmThis, __cehmEvt)`,
        ctx,
      );
    }
    cur = cur.parentNode;
  }
  return evt;
}

function simulateSelectChange(selectEl, newValue, ctx) {
  assert.ok(selectEl, 'simulateSelectChange requires a non-null select element');
  selectEl.value = newValue;
  const evt = {
    type: 'change',
    target: selectEl,
    currentTarget: selectEl,
    propagationStopped: false,
    stopPropagation() {
      this.propagationStopped = true;
    },
    preventDefault() {},
  };
  const onchangeAttr = selectEl.getAttribute('onchange');
  if (onchangeAttr) {
    ctx.__cehmEvt = evt;
    ctx.__cehmThis = selectEl;
    vm.runInContext(
      `(function(event){ ${onchangeAttr} }).call(__cehmThis, __cehmEvt)`,
      ctx,
    );
  }
  selectEl.dispatchEvent(evt);
  return evt;
}

function simulateDocumentKeydown(doc, key) {
  const fns = (doc._listeners && doc._listeners.get('keydown')) || [];
  const evt = {
    type: 'keydown',
    key,
    target: doc.activeElement || doc.body,
    preventDefault() {},
  };
  fns.forEach((fn) => fn(evt));
  return evt;
}

function stripTags(markup) {
  return String(markup || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function getAllText(el) {
  if (!el) return '';
  const childText = (el.children || []).map((ch) => getAllText(ch)).join(' ');
  return [el.textContent || '', stripTags(el.innerHTML || ''), childText]
    .filter(Boolean)
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function findAllByPredicate(root, predicate) {
  const matches = [];
  const visit = (node) => {
    if (!node) return;
    if (predicate(node)) matches.push(node);
    for (const ch of node.children || []) visit(ch);
  };
  visit(root);
  return matches;
}

async function flushMicrotasks(ticks = 6) {
  for (let i = 0; i < ticks; i += 1) {
    await Promise.resolve();
  }
}
"""


def _eval_cehm_js(test_body_js: str) -> dict[str, Any]:
    preamble = _NODE_DOM_HARNESS_PREAMBLE.replace(
        "__HTML_PATH__", json.dumps(str(DASHBOARD_HTML))
    )
    return _run_node_script(
        f"{preamble}\n{_CEHM_HARNESS_EXTRAS}\n(async () => {{\n{test_body_js}\n}})().catch((err) => {{ console.error(err); process.exit(1); }});\n"
    )


def _assert_cehm_hp_04_flow() -> None:
    """Shared CEHM-HP-04 full modal UI verification against real extracted DOM & JS."""
    res = _eval_cehm_js(
        r"""
        const historyCalls = [];
        const reviewCalls = [];
        let failHistoryOnce = true;

        const baseStages = [
          { id: 'spec', index: 1, label: '1. Spec', status: 'done', summary: 'Gate 1 PASS', sub_steps: [] },
          { id: 'hld_principal', index: 2, label: '2. HLD & Principal', status: 'done', summary: 'Gate 2 PASS', sub_steps: [] },
          { id: 'tasks', index: 3, label: '3. Tasks', status: 'done', summary: '4/4 (100%)', sub_steps: [] },
          { id: 'gate4_quality', index: 4, label: '4. Gate 4 QA', status: 'done', summary: 'All checks PASS', sub_steps: [] },
          {
            id: 'cross_review',
            index: 5,
            label: '5. Cross-Review',
            status: 'running',
            summary: 'Round 1/3 · codex',
            sub_steps: [
              { id: 'reviewing', label: 'Reviewing', status: 'done', detail: 'codex' },
              { id: 'triage', label: 'Triage', status: 'running', detail: 'Analyzing findings' },
            ],
          },
          { id: 'finish', index: 6, label: '6. Finish', status: 'pending', summary: 'Pending Gate 5', sub_steps: [] },
        ];

        const makeEpicPayload = (slug, status, roundCross = 1) => ({
          success: true,
          epic: {
            slug,
            title: `${slug} <script>alert(1)</script>`,
            status,
            pic: 'phungthuy8901',
            has_worktree: status === 'in_progress',
            worktree_path: status === 'in_progress' ? `/tmp/ai-agent-tools/.worktrees/${slug}` : null,
            done_tasks: 1,
            total_tasks: 2,
            last_updated: '2026-11-15T01:00:00Z',
            last_updated_human: '5m ago',
          },
          pipeline_telemetry: {
            epic_slug: slug,
            task_completion_pct: 50,
            lifecycle_progress_pct: 68,
            current_stage_index: 5,
            active_sub_step_summary: 'Cross-Review R1',
            stages: baseStages,
            events: [],
          },
          tasks: [
            {
              id: 'task_01',
              title: 'Build shared helpers <script>alert("task")</script>',
              status: 'done',
              priority: 'high',
              epic: slug,
              labels: ['ui'],
              time: '2026-11-15T00:30:00Z',
              source: status === 'in_progress' ? 'worktree' : 'root',
              evidence: {
                phase: 'verify',
                status: 'PASS',
                head: 'deadbeef1234',
                started: '2026-11-15T00:31:00Z',
                finished: '2026-11-15T00:32:00Z',
                passed_rows: 3,
                total_rows: 3,
                rows: [
                  {
                    id: 'V1',
                    phase: 'verify',
                    command: 'pytest -q tests/test_cehm_dashboard_modal_ui.py',
                    outcome: 'PASS',
                    reason: '',
                    started: '2026-11-15T00:31:00Z',
                    finished: '2026-11-15T00:31:15Z',
                    output_tail: ['3 passed in 0.42s', '<script>alert("tail")</script>'],
                  },
                ],
              },
            },
            {
              id: 'task_02',
              title: 'Pending integration task',
              status: 'todo',
              priority: 'medium',
              epic: slug,
              labels: [],
              time: '',
              source: 'root',
              evidence: null,
            },
          ],
          timeline: [
            { ts: '2026-11-15T00:10:00Z', category: 'gate', stage: 'Gate 1', sub_step: 'approve', detail: 'Gate 1 approved by architect', message: 'Gate 1 PASS', source: 'checkpoint' },
            { ts: '2026-11-15T00:20:00Z', category: 'step', stage: 'Stage 3', sub_step: 'implement', detail: 'Running TDD loop', message: 'Step event <script>alert("tl")</script>', source: 'heartbeat' },
            { ts: '2026-11-15T00:30:00Z', category: 'activity', stage: 'Activity', sub_step: 'commit', detail: 'Saved progress', message: 'Programmer committed task_01', source: 'activity_log' },
            { ts: '2026-11-15T00:40:00Z', category: 'evidence', stage: 'Verify', sub_step: 'verify', detail: 'PASS 3/3', message: 'Verification evidence recorded', source: 'verification_evidence' },
          ],
          reviews: {
            principal: {
              repo: 'ai-agent-tools',
              epic: slug,
              round: 1,
              available_rounds: [1],
              kind: 'principal',
              present: true,
              verdict: 'PASS',
              sha: 'aaaa1111bbbb',
              reviewer: 'claude',
              model: 'claude-opus',
              thinking: 'High',
              theme_color: '#38bdf8',
              findings: [
                { id: 'PR-1', severity: 'Minor', location: 'docs/hld.md:10', problem: 'Clarify API route', proposed_action: 'Document error 404', decision: 'Fixed in aaa1111' },
              ],
              raw_output: 'Principal raw log',
            },
            cross_model: {
              repo: 'ai-agent-tools',
              epic: slug,
              round: roundCross,
              available_rounds: [1, 2],
              kind: 'cross-model',
              present: true,
              verdict: roundCross === 2 ? 'PASS (CONVERGED)' : 'CHANGES REQUIRED',
              sha: roundCross === 2 ? 'cccc2222dddd' : 'bbbb2222cccc',
              reviewer: 'codex',
              model: 'gpt-5-codex',
              thinking: 'xhigh',
              theme_color: '#38bdf8',
              findings: roundCross === 2
                ? [{ id: 'CR-R2-1', severity: 'Minor', location: 'tests/test_ui.py:55', problem: 'Add aria assertion', proposed_action: 'Keep attribute', decision: 'open' }]
                : [{ id: 'CR-1', severity: 'Important', location: 'dashboard.html:1200', problem: 'Escape <script>alert("xss")</script> cleanly', proposed_action: 'Use escapeHtml', decision: 'pending' }],
              raw_output: `Cross review round ${roundCross} raw log`,
            },
          },
          log_completeness: 'full_stream',
        });

        const repo = {
          name: 'ai-agent-tools',
          path: '/tmp/ai-agent-tools',
          theme_color: '#38bdf8',
          active_epic: 'epic_in_progress',
          worktrees: [{ path: '/tmp/ai-agent-tools', branch: 'main', dirty_files_count: 0 }],
          pipeline_telemetry: {
            epic_slug: 'epic_in_progress',
            task_completion_pct: 50,
            lifecycle_progress_pct: 60,
            current_stage_index: 5,
            stages: baseStages,
            events: [{ ts: '2026-11-15T00:05:00Z', stage: 'Cross-Review', sub_step: 'triage', message: 'Section II log' }],
          },
          task_progress: {
            done: 1,
            total: 2,
            tasks: [
              { id: 'task_01', title: 'Done task', status: 'done', priority: 'high', epic: 'epic_in_progress' },
              { id: 'task_02', title: 'Todo task', status: 'todo', priority: 'medium', epic: 'epic_in_progress' },
            ],
          },
          epics_summary: {
            total: 5,
            completed: 1,
            in_progress: 1,
            unstarted: 2,
            abandoned: 1,
            epics: [
              { slug: 'epic_done', status: 'done', task_count: 4, pic: 'phungthuy8901', last_updated: '2026-11-15T00:00:00Z', last_updated_human: '1h ago' },
              { slug: 'epic_in_progress', status: 'in_progress', task_count: 2, pic: 'phungthuy8901', last_updated: '2026-11-15T01:00:00Z', last_updated_human: '5m ago' },
              { slug: 'epic_packaged', status: 'packaged', task_count: 3, pic: 'danhdue', last_updated: '2026-11-14T20:00:00Z', last_updated_human: '5h ago' },
              { slug: 'epic_backlog', status: 'backlog', task_count: 0, pic: null, last_updated: '2026-11-14T10:00:00Z', last_updated_human: '15h ago' },
              { slug: 'epic_abandon', status: 'abandon', task_count: 1, pic: null, last_updated: '2026-11-10T00:00:00Z', last_updated_human: '5d ago' },
            ],
          },
        };

        const { sandbox, doc } = createCehmDomHarness(async (url) => {
          const parsed = new URL(url, 'http://127.0.0.1:8766');
          if (parsed.pathname === '/api/tasks') {
            return {
              ok: true,
              status: 200,
              async json() {
                return { repos: [repo], available_profiles: ['phungthuy8901', 'danhdue'] };
              },
            };
          }
          if (parsed.pathname === '/api/epic/history') {
            historyCalls.push(parsed.searchParams.toString());
            if (failHistoryOnce) {
              failHistoryOnce = false;
              return {
                ok: false,
                status: 500,
                async json() {
                  return { success: false, error: 'Database read timeout' };
                },
              };
            }
            const slug = parsed.searchParams.get('epic') || 'epic_done';
            const roundCross = Number(parsed.searchParams.get('round_cross') || '1');
            return {
              ok: true,
              status: 200,
              async json() {
                return makeEpicPayload(slug, slug.replace('epic_', ''), roundCross);
              },
            };
          }
          if (parsed.pathname === '/api/review') {
            reviewCalls.push(parsed.searchParams.toString());
            return {
              ok: true,
              status: 200,
              async json() {
                return {
                  repo: 'ai-agent-tools',
                  epic: parsed.searchParams.get('epic'),
                  round: 1,
                  available_rounds: [1],
                  kind: 'cross-model',
                  present: true,
                  verdict: 'PASS',
                  sha: 'facebeef1234',
                  reviewer: 'codex',
                  model: 'gpt-5-codex',
                  thinking: 'High',
                  theme_color: '#38bdf8',
                  findings: [{ id: 'RV-9', severity: 'Minor', location: 'app.js:12', problem: 'Sample problem', proposed_action: 'Fix it', decision: 'deadbeef' }],
                  raw_output: 'Verbatim legacy review output',
                };
              },
            };
          }
          return { ok: true, status: 200, async json() { return { profiles: [] }; } };
        });

        // 1. Verify shared helpers exist as callable functions
        assert.equal(typeof sandbox.buildPipelineStepperHtml, 'function', 'buildPipelineStepperHtml must exist');
        assert.equal(typeof sandbox.buildReviewHeaderHtml, 'function', 'buildReviewHeaderHtml must exist');
        assert.equal(typeof sandbox.buildReviewFindingsTableHtml, 'function', 'buildReviewFindingsTableHtml must exist');

        // 2. Render repo detail view containing all 5 roadmap statuses + Section II telemetry via pollDashboard()
        await sandbox.pollDashboard();
        await flushMicrotasks();

        const detailView = doc.getElementById('repo-detail-view');
        const sectionIIStepper = findAllByPredicate(detailView, (el) => el.getAttribute('data-telemetry') === 'pipeline-stepper');
        assert.ok(sectionIIStepper.length >= 1, 'Section II pipeline-stepper must still render');

        const rows = detailView.querySelectorAll('.roadmap-epic-row');
        assert.equal(rows.length, 5, 'All 5 roadmap rows must render');
        for (const r of rows) {
          assert.ok(r.getAttribute('data-epic-slug'), 'Row must have data-epic-slug');
          assert.equal(r.getAttribute('data-repo-name'), 'ai-agent-tools', 'Row must have data-repo-name');
        }

        // 3. First row click hits HTTP 500 -> error banner + Retry -> Retry succeeds
        simulateDomClick(rows[0], sandbox);
        await flushMicrotasks();

        const modal = doc.getElementById('modal-epic-history');
        assert.equal(modal.style.display, 'flex', 'Modal must open immediately on click (even while loading/error)');
        const errorBanner = doc.getElementById('epic-history-error-banner');
        assert.ok(errorBanner && errorBanner.style.display !== 'none', 'Error banner must show on HTTP 500');
        assert.ok(getAllText(errorBanner).includes('Database read timeout'), 'Error banner must display server error text');

        const retryBtn = doc.getElementById('epic-history-retry-btn') || findAllByPredicate(errorBanner, (el) => el.tagName === 'BUTTON')[0];
        assert.ok(retryBtn, 'Inline Retry button must exist inside error banner');
        simulateDomClick(retryBtn, sandbox);
        await flushMicrotasks();
        assert.equal(errorBanner.style.display, 'none', 'Error banner must hide after successful retry');

        // Verify clicking all remaining 4 roadmap statuses also fetches and renders
        for (let idx = 1; idx < rows.length; idx += 1) {
          simulateDomClick(rows[idx], sandbox);
          await flushMicrotasks();
          const expectedSlug = rows[idx].getAttribute('data-epic-slug');
          assert.ok(
            getAllText(doc.getElementById('epic-history-title')).includes(expectedSlug),
            `Modal title must reflect clicked epic ${expectedSlug}`,
          );
        }

        // Now inspect epic_in_progress (clicked above, or re-click rows[1])
        simulateDomClick(rows[1], sandbox);
        await flushMicrotasks();

        // Compact header & 6-stage stepper
        const stepperEl = doc.getElementById('epic-history-stepper');
        const modalStagePills = stepperEl.querySelectorAll('[data-stage-id]');
        assert.equal(modalStagePills.length, 6, 'Compact header must render all 6 pipeline stages');
        assert.ok(getAllText(doc.getElementById('epic-history-meta')).includes('full_stream'), 'Stream completeness badge must render');

        // Verify no Vietnamese text leaked into modal
        const modalFullText = getAllText(modal);
        assert.ok(
          !/(Trạng thái|Giai đoạn|Chưa có|Kiểm tra lại|Thử lại|Đóng)/i.test(modalFullText),
          `Modal must contain English-only copy, got: ${modalFullText}`,
        );

        // 4. Tab 1: Timeline & Step Logs + all 5 filter pills
        const bodyEl = doc.getElementById('epic-history-body');
        assert.ok(getAllText(bodyEl).includes('Gate 1 PASS'));
        assert.ok(getAllText(bodyEl).includes('Programmer committed task_01'));
        assert.ok(getAllText(bodyEl).includes('Verification evidence recorded'));

        const findFilterBtn = (cat) => findAllByPredicate(bodyEl, (el) => el.getAttribute('data-timeline-filter') === cat)[0];
        for (const [cat, expectedText, absentText] of [
          ['gate', 'Gate 1 PASS', 'Verification evidence recorded'],
          ['step', 'Step event', 'Gate 1 PASS'],
          ['activity', 'Programmer committed task_01', 'Gate 1 PASS'],
          ['evidence', 'Verification evidence recorded', 'Gate 1 PASS'],
          ['all', 'Gate 1 PASS', null],
        ]) {
          const btn = findFilterBtn(cat);
          assert.ok(btn, `Timeline filter pill "${cat}" must exist`);
          simulateDomClick(btn, sandbox);
          const bodyTxt = getAllText(bodyEl);
          assert.ok(bodyTxt.includes(expectedText), `Filter "${cat}" must show "${expectedText}"`);
          if (absentText) {
            assert.ok(!bodyTxt.includes(absentText), `Filter "${cat}" must hide "${absentText}"`);
          }
        }

        // 5. Tab 2: Tasks & Evidence + expand evidence row
        const findTabBtn = (tabName) => findAllByPredicate(modal, (el) => el.getAttribute('data-history-tab') === tabName)[0];
        simulateDomClick(findTabBtn('tasks'), sandbox);
        let tasksText = getAllText(bodyEl);
        assert.ok(tasksText.includes('3/3'), 'Task row must show passed_rows/total_rows (3/3)');
        assert.ok(tasksText.includes('deadbeef1234'), 'Task row must show head commit');

        const toggleBtn = findAllByPredicate(bodyEl, (el) => el.getAttribute('data-evidence-task-id') === 'task_01')[0];
        assert.ok(toggleBtn, 'Expandable task evidence toggle button must exist for task_01');
        simulateDomClick(toggleBtn, sandbox);
        tasksText = getAllText(bodyEl);
        assert.ok(tasksText.includes('pytest -q tests/test_cehm_dashboard_modal_ui.py'), 'Expanded evidence must show command');
        assert.ok(tasksText.includes('3 passed in 0.42s'), 'Expanded evidence must show output_tail');

        // Verify XSS escaping on task title & output_tail
        assert.ok(!bodyEl.innerHTML.includes('<script>alert'), 'Tasks & evidence HTML must not render unescaped <script> tags');
        assert.ok(bodyEl.innerHTML.includes('&lt;script&gt;'), 'Escaped <script> must be safely present');

        // 6. Tab 3: Principal Review
        simulateDomClick(findTabBtn('principal'), sandbox);
        let principalText = getAllText(bodyEl);
        assert.ok(principalText.includes('PR-1'), 'Principal Review must show finding PR-1');
        assert.ok(principalText.includes('aaaa1111bbbb'), 'Principal Review must show commit SHA');

        // 7. Tab 4: Cross-Model Review + in-modal Round 2 switcher without opening #modal-cross-review
        simulateDomClick(findTabBtn('cross_model'), sandbox);
        let crossText = getAllText(bodyEl);
        assert.ok(crossText.includes('CR-1'), 'Cross-Model Review must show Round 1 finding CR-1');
        assert.ok(!bodyEl.innerHTML.includes('<script>alert'), 'Review findings HTML must escape <script>');

        const round2Btn = findAllByPredicate(bodyEl, (el) => el.getAttribute('data-review-round') === '2')[0];
        assert.ok(round2Btn, 'In-modal Round 2 button must exist');
        simulateDomClick(round2Btn, sandbox);
        await flushMicrotasks();

        crossText = getAllText(bodyEl);
        assert.ok(crossText.includes('CR-R2-1'), 'Switching round in-modal must render Round 2 finding CR-R2-1');
        assert.ok(historyCalls.some((qs) => qs.includes('round_cross=2')), 'Switching round must request round_cross=2 on /api/epic/history');
        assert.equal(doc.getElementById('modal-cross-review').style.display, 'none', 'Legacy #modal-cross-review must NOT open while inside #modal-epic-history');

        // 8. Verify legacy openReviewModal still works with shared helpers
        sandbox.openReviewModal('ai-agent-tools', 'epic_done', 1, 'cross-model');
        await flushMicrotasks();
        assert.equal(reviewCalls.length, 1, 'Legacy openReviewModal must call /api/review');
        assert.equal(doc.getElementById('modal-cross-review').style.display, 'flex', 'Legacy #modal-cross-review must still open cleanly');
        assert.ok(getAllText(doc.getElementById('review-findings-body')).includes('RV-9'), 'Legacy #modal-cross-review must render findings via shared helper');

        console.log(JSON.stringify({ ok: true, historyCallsCount: historyCalls.length }));
        """
    )
    assert res["ok"] is True


def test_cehm_hp_04_roadmap_click_opens_modal_and_tabs() -> None:
    """CEHM-HP-04: Clicking any roadmap epic opens modal with shared stepper, tabs, filters, evidence, and round switcher."""
    _assert_cehm_hp_04_flow()


class TestCehmDashboardModalUi_Integration:
    """Tier C Integration test suite for CEHM dashboard modal UI scenarios."""

    def test_cehm_hp_04_integration_roadmap_modal_tabs_filters_reviews_and_xss(
        self,
    ) -> None:
        """[CEHM-HP-04] [Tier C - Integration] Full roadmap modal UI, tabs, filters, round switching, error retry, and XSS safety."""
        _assert_cehm_hp_04_flow()

    def test_cehm_ec_03_integration_pic_select_does_not_open_modal(self) -> None:
        """[CEHM-EC-03] [Tier C - Integration] Clicking or changing PIC select on roadmap row updates PIC without opening modal."""
        res = _eval_cehm_js(
            r"""
            const historyCalls = [];
            const picCalls = [];

            const repo = {
              name: 'ai-agent-tools',
              path: '/tmp/ai-agent-tools',
              theme_color: '#38bdf8',
              worktrees: [{ path: '/tmp/ai-agent-tools', branch: 'main', dirty_files_count: 0 }],
              epics_summary: {
                total: 1,
                completed: 0,
                in_progress: 1,
                unstarted: 0,
                abandoned: 0,
                epics: [
                  { slug: 'isolated_pic_epic', status: 'in_progress', task_count: 2, pic: 'phungthuy8901', last_updated_human: '2m ago' },
                ],
              },
            };

            const { sandbox, doc } = createCehmDomHarness(async (url, opts) => {
              const parsed = new URL(url, 'http://127.0.0.1:8766');
              if (parsed.pathname === '/api/tasks') {
                return {
                  ok: true,
                  status: 200,
                  async json() {
                    return { repos: [repo], available_profiles: ['phungthuy8901', 'danhdue'] };
                  },
                };
              }
              if (parsed.pathname === '/api/epic/history') {
                historyCalls.push(parsed.toString());
                return { ok: true, status: 200, async json() { return { success: true }; } };
              }
              if (parsed.pathname === '/api/epic/pic') {
                picCalls.push(JSON.parse(opts.body));
                return { ok: true, status: 200, async json() { return { status: 'ok', updated_files: [] }; } };
              }
              return { ok: true, status: 200, async json() { return {}; } };
            });

            await sandbox.pollDashboard();
            await flushMicrotasks();

            const selectEl = doc.getElementById('repo-detail-view').querySelectorAll('.select-pic-roadmap')[0];
            assert.ok(selectEl, 'PIC select control must exist in roadmap row');

            // Click select directly
            simulateDomClick(selectEl, sandbox);
            // Click an inner <option> element too (descendant click bubbling check)
            const optEl = selectEl.children[0];
            if (optEl) simulateDomClick(optEl, sandbox);
            // Change PIC value
            simulateSelectChange(selectEl, 'danhdue', sandbox);
            await flushMicrotasks();

            const modal = doc.getElementById('modal-epic-history');
            assert.equal(modal.style.display, 'none', 'Modal must remain closed when interacting with PIC select');
            assert.equal(historyCalls.length, 0, '/api/epic/history must NOT be called');
            assert.equal(picCalls.length, 1, '/api/epic/pic must receive PIC assignment');
            assert.deepEqual(picCalls[0], { repo: 'ai-agent-tools', epic: 'isolated_pic_epic', pic: 'danhdue' });

            console.log(JSON.stringify({ ok: true }));
            """
        )
        assert res["ok"] is True

    def test_cehm_st_02_integration_worktree_precedence_and_tab_persistence_on_poll(
        self, tmp_path: Path
    ) -> None:
        """[CEHM-ST-02] [Tier C - Integration] Real worktree-precedence harvest payload renders worktree status and preserves active tab across pollDashboard()."""
        repo_dir = tmp_path / "demo_repo"
        epic_slug = "wt_live_epic"
        root_feat = repo_dir / ".devtool" / "features"
        root_feat.mkdir(parents=True)
        (root_feat / "task_01_live_task.md").write_text(
            "---\nid: task_01_live_task\ntitle: Live worktree task\nstatus: todo\npriority: high\nepic: wt_live_epic\n---\n\nRoot stale copy.\n",
            encoding="utf-8",
        )
        wt_root = repo_dir / ".worktrees" / epic_slug
        wt_feat = wt_root / ".devtool" / "features"
        wt_feat.mkdir(parents=True)
        (wt_feat / "task_01_live_task.md").write_text(
            "---\nid: task_01_live_task\ntitle: Live worktree task\nstatus: in-progress\npriority: high\nepic: wt_live_epic\n---\n\nWorktree active copy.\n",
            encoding="utf-8",
        )
        wt_epic_dir = wt_root / ".devtool" / "epic" / epic_slug
        wt_epic_dir.mkdir(parents=True)
        (wt_epic_dir / f"{epic_slug}.en.md").write_text(
            "# Live Worktree Epic\n\nHLD summary.\n",
            encoding="utf-8",
        )

        # Call real Python backend harvester to verify exact JSON contract & precedence
        check_tasks_mod = _load_check_tasks_module()
        harvested_initial = check_tasks_mod.harvest_epic_history(repo_dir, epic_slug)
        assert harvested_initial["tasks"][0]["status"] == "in-progress"
        assert harvested_initial["tasks"][0]["source"] == "worktree"
        harvested_initial["epic"]["status"] = "in_progress"
        harvested_initial["reviews"] = {
            "principal": {
                "repo": "demo_repo",
                "epic": epic_slug,
                "round": 1,
                "available_rounds": [1],
                "kind": "principal",
                "present": True,
                "verdict": "PASS",
                "sha": "1111aaaa",
                "reviewer": "claude",
                "model": "claude-opus",
                "thinking": "High",
                "findings": [],
                "raw_output": "",
            },
            "cross_model": {
                "repo": "demo_repo",
                "epic": epic_slug,
                "round": 1,
                "available_rounds": [1],
                "kind": "cross-model",
                "present": True,
                "verdict": "CHANGES REQUIRED",
                "sha": "2222bbbb",
                "reviewer": "codex",
                "model": "gpt-5-codex",
                "thinking": "xhigh",
                "findings": [
                    {
                        "id": "CR-ST2",
                        "severity": "Minor",
                        "location": "src/app.py:8",
                        "problem": "Keep active tab on poll",
                        "proposed_action": "Preserve state",
                        "decision": "open",
                    }
                ],
                "raw_output": "Poll round output",
            },
        }
        payload_initial_json = json.dumps({"success": True, **harvested_initial})

        harvested_poll = json.loads(payload_initial_json)
        harvested_poll["epic"]["last_updated_human"] = "just now"
        harvested_poll["tasks"][0]["title"] = "Live worktree task (updated via poll)"
        payload_poll_json = json.dumps(harvested_poll)

        harvested_done = json.loads(payload_initial_json)
        harvested_done["epic"]["slug"] = "done_epic"
        harvested_done["epic"]["status"] = "done"
        payload_done_json = json.dumps(harvested_done)

        res = _eval_cehm_js(
            f"""
            const initialPayload = {payload_initial_json};
            const pollPayload = {payload_poll_json};
            const donePayload = {payload_done_json};
            const historyUrls = [];
            let historyCount = 0;

            const makeRepoSnapshot = () => ({{
              name: 'D3Nexus',
              path: {json.dumps(str(repo_dir))},
              theme_color: '#38bdf8',
              active_epic: 'wt_live_epic',
              worktrees: [{{ path: {json.dumps(str(wt_root))}, branch: 'feat/wt_live_epic', dirty_files_count: 1 }}],
              epics_summary: {{
                total: 2,
                completed: 1,
                in_progress: 1,
                unstarted: 0,
                abandoned: 0,
                epics: [
                  {{ slug: 'wt_live_epic', status: 'in_progress', task_count: 1, pic: 'phungthuy8901', last_updated_human: '2m ago' }},
                  {{ slug: 'done_epic', status: 'done', task_count: 1, pic: 'phungthuy8901', last_updated_human: '1d ago' }},
                ],
              }},
            }});

            const {{ sandbox, doc }} = createCehmDomHarness(async (url) => {{
              const parsed = new URL(url, 'http://127.0.0.1:8766');
              if (parsed.pathname === '/api/epic/history') {{
                historyUrls.push(parsed.searchParams.get('epic'));
                if (parsed.searchParams.get('epic') === 'done_epic') {{
                  return {{ ok: true, status: 200, async json() {{ return donePayload; }} }};
                }}
                historyCount += 1;
                return {{
                  ok: true,
                  status: 200,
                  async json() {{ return historyCount === 1 ? initialPayload : pollPayload; }},
                }};
              }}
              if (parsed.pathname === '/api/tasks') {{
                return {{
                  ok: true,
                  status: 200,
                  async json() {{ return {{ repos: [makeRepoSnapshot()], available_profiles: ['phungthuy8901'] }}; }},
                }};
              }}
              return {{ ok: true, status: 200, async json() {{ return {{}}; }} }};
            }});

            await sandbox.pollDashboard();
            await flushMicrotasks();

            const rows = doc.getElementById('repo-detail-view').querySelectorAll('.roadmap-epic-row');
            const liveRow = rows.find((r) => r.getAttribute('data-epic-slug') === 'wt_live_epic');
            assert.ok(liveRow, 'wt_live_epic row must exist');
            simulateDomClick(liveRow, sandbox);
            await flushMicrotasks();

            // Check Tasks tab shows worktree status in-progress + worktree badge
            const modal = doc.getElementById('modal-epic-history');
            const tasksTab = findAllByPredicate(modal, (el) => el.getAttribute('data-history-tab') === 'tasks')[0];
            simulateDomClick(tasksTab, sandbox);
            let bodyText = getAllText(doc.getElementById('epic-history-body'));
            assert.ok(bodyText.includes('in-progress'), 'Tasks tab must display worktree status "in-progress"');
            assert.ok(bodyText.includes('worktree'), 'Tasks tab must display worktree source indicator');

            // Switch to Cross-Model Review tab before pollDashboard()
            const crossTab = findAllByPredicate(modal, (el) => el.getAttribute('data-history-tab') === 'cross_model')[0];
            simulateDomClick(crossTab, sandbox);
            assert.ok(getAllText(doc.getElementById('epic-history-body')).includes('CR-ST2'));

            // Trigger silent pollDashboard() while modal inspects in_progress epic
            await sandbox.pollDashboard();
            await flushMicrotasks();

            assert.equal(historyCount, 2, 'pollDashboard() must silently refresh in_progress epic history');
            assert.equal(modal.style.display, 'flex', 'Modal must remain open after pollDashboard()');
            assert.ok(crossTab.classList.contains('active'), 'Active Cross-Model Review tab must be preserved across pollDashboard()');
            assert.ok(getAllText(doc.getElementById('epic-history-meta')).includes('just now'), 'Header timestamp must silently update on poll');
            assert.ok(getAllText(doc.getElementById('epic-history-body')).includes('CR-ST2'), 'Active tab content must stay rendered');

            // Verify done epic does NOT trigger background history re-fetch on pollDashboard()
            const doneRow = doc.getElementById('repo-detail-view').querySelectorAll('.roadmap-epic-row').find((r) => r.getAttribute('data-epic-slug') === 'done_epic');
            simulateDomClick(doneRow, sandbox);
            await flushMicrotasks();
            const countBeforeDonePoll = historyUrls.length;
            await sandbox.pollDashboard();
            await flushMicrotasks();
            assert.equal(historyUrls.length, countBeforeDonePoll, 'pollDashboard() must NOT re-fetch /api/epic/history when open epic status is done');

            console.log(JSON.stringify({{ ok: true }}));
            """
        )
        assert res["ok"] is True

    def test_cehm_st_03_integration_close_controls_overflow_and_poll_stop(self) -> None:
        """[CEHM-ST-03] [Tier C - Integration] Closing via X, backdrop, or Escape restores body overflow and stops /api/epic/history polling."""
        res = _eval_cehm_js(
            r"""
            let historyCallCount = 0;

            const makeInProgressPayload = () => ({
              success: true,
              epic: {
                slug: 'active_close_epic',
                title: 'Active Close Epic',
                status: 'in_progress',
                pic: 'phungthuy8901',
                done_tasks: 0,
                total_tasks: 1,
                last_updated_human: '1m ago',
              },
              pipeline_telemetry: { epic_slug: 'active_close_epic', current_stage_index: 3, stages: [], events: [] },
              tasks: [],
              timeline: [],
              reviews: { principal: { present: false, findings: [] }, cross_model: { present: false, findings: [] } },
              log_completeness: 'snapshot_and_ledger',
            });

            const repo = {
              name: 'D3Nexus',
              path: '/tmp/D3Nexus',
              theme_color: '#38bdf8',
              worktrees: [],
              epics_summary: {
                total: 1,
                completed: 0,
                in_progress: 1,
                unstarted: 0,
                abandoned: 0,
                epics: [{ slug: 'active_close_epic', status: 'in_progress', task_count: 1, pic: 'phungthuy8901', last_updated_human: '1m ago' }],
              },
            };

            const { sandbox, doc } = createCehmDomHarness(async (url) => {
              const parsed = new URL(url, 'http://127.0.0.1:8766');
              if (parsed.pathname === '/api/epic/history') {
                historyCallCount += 1;
                return { ok: true, status: 200, async json() { return makeInProgressPayload(); } };
              }
              if (parsed.pathname === '/api/tasks') {
                return { ok: true, status: 200, async json() { return { repos: [repo], available_profiles: ['phungthuy8901'] }; } };
              }
              return { ok: true, status: 200, async json() { return {}; } };
            });

            await sandbox.pollDashboard();
            await flushMicrotasks();

            const modal = doc.getElementById('modal-epic-history');
            const getRow = () => doc.getElementById('repo-detail-view').querySelectorAll('.roadmap-epic-row')[0];

            // 1. Close via ✕ button
            simulateDomClick(getRow(), sandbox);
            await flushMicrotasks();
            assert.equal(modal.style.display, 'flex');
            assert.equal(doc.body.style.overflow, 'hidden');
            const closeBtn = findAllByPredicate(modal, (el) => el.classList.contains('modal-close-btn'))[0];
            assert.ok(closeBtn, 'Modal close button (✕) must exist');
            simulateDomClick(closeBtn, sandbox);
            assert.equal(modal.style.display, 'none', '✕ click must hide modal');
            assert.equal(doc.body.style.overflow, '', '✕ click must restore body overflow');
            const callsAfterCloseBtn = historyCallCount;
            await sandbox.pollDashboard();
            await flushMicrotasks();
            assert.equal(historyCallCount, callsAfterCloseBtn, 'No /api/epic/history polling after ✕ close');

            // 2. Close via .modal-backdrop click
            simulateDomClick(getRow(), sandbox);
            await flushMicrotasks();
            assert.equal(modal.style.display, 'flex');
            assert.equal(doc.body.style.overflow, 'hidden');
            simulateDomClick(modal, sandbox);
            assert.equal(modal.style.display, 'none', 'Backdrop click must hide modal');
            assert.equal(doc.body.style.overflow, '', 'Backdrop click must restore body overflow');
            const callsAfterBackdrop = historyCallCount;
            await sandbox.pollDashboard();
            await flushMicrotasks();
            assert.equal(historyCallCount, callsAfterBackdrop, 'No /api/epic/history polling after backdrop close');

            // 3. Close via Escape key
            simulateDomClick(getRow(), sandbox);
            await flushMicrotasks();
            assert.equal(modal.style.display, 'flex');
            assert.equal(doc.body.style.overflow, 'hidden');
            simulateDocumentKeydown(doc, 'Escape');
            assert.equal(modal.style.display, 'none', 'Escape key must hide modal');
            assert.equal(doc.body.style.overflow, '', 'Escape key must restore body overflow');
            const callsAfterEsc = historyCallCount;
            await sandbox.pollDashboard();
            await flushMicrotasks();
            assert.equal(historyCallCount, callsAfterEsc, 'No /api/epic/history polling after Escape close');

            console.log(JSON.stringify({ ok: true }));
            """
        )
        assert res["ok"] is True

    def test_cehm_ar_02_integration_race_guard_discards_stale_response(self) -> None:
        """[CEHM-AR-02] [Tier C - Integration] Slower response for epic A never overwrites faster response for epic B."""
        res = _eval_cehm_js(
            r"""
            const abortedEpics = [];

            const makePayload = (slug, title, logMsg) => ({
              success: true,
              epic: {
                slug,
                title,
                status: 'done',
                pic: 'phungthuy8901',
                done_tasks: 1,
                total_tasks: 1,
                last_updated_human: '1m ago',
              },
              pipeline_telemetry: { epic_slug: slug, current_stage_index: 6, stages: [], events: [] },
              tasks: [{ id: 't1', title: `${slug} task`, status: 'done', priority: 'high', epic: slug, labels: [], source: 'root', evidence: null }],
              timeline: [{ ts: '2026-11-15T01:00:00Z', category: 'step', stage: 'Stage 3', sub_step: 'run', detail: '', message: logMsg, source: 'heartbeat' }],
              reviews: { principal: { present: false, findings: [] }, cross_model: { present: false, findings: [] } },
              log_completeness: 'full_stream',
            });

            const repo = {
              name: 'D3Nexus',
              path: '/tmp/D3Nexus',
              theme_color: '#38bdf8',
              worktrees: [],
              epics_summary: {
                total: 2,
                completed: 2,
                in_progress: 0,
                unstarted: 0,
                abandoned: 0,
                epics: [
                  { slug: 'epic_alpha', status: 'done', task_count: 1, pic: 'phungthuy8901', last_updated_human: '2m ago' },
                  { slug: 'epic_beta', status: 'done', task_count: 1, pic: 'phungthuy8901', last_updated_human: '1m ago' },
                ],
              },
            };

            const { sandbox, doc } = createCehmDomHarness((url, opts) => {
              const parsed = new URL(url, 'http://127.0.0.1:8766');
              if (parsed.pathname === '/api/epic/history') {
                const epic = parsed.searchParams.get('epic');
                const delayMs = epic === 'epic_alpha' ? 120 : 10;
                if (opts && opts.signal) {
                  if (opts.signal.aborted) {
                    abortedEpics.push(epic);
                  } else {
                    opts.signal.addEventListener('abort', () => abortedEpics.push(epic));
                  }
                }
                return new Promise((resolve) => {
                  setTimeout(() => {
                    resolve({
                      ok: true,
                      status: 200,
                      async json() {
                        return epic === 'epic_alpha'
                          ? makePayload('epic_alpha', 'Alpha Legacy Epic', 'Alpha stale log')
                          : makePayload('epic_beta', 'Beta Winning Epic', 'Beta winning log');
                      },
                    });
                  }, delayMs);
                });
              }
              if (parsed.pathname === '/api/tasks') {
                return Promise.resolve({
                  ok: true,
                  status: 200,
                  async json() { return { repos: [repo], available_profiles: ['phungthuy8901'] }; },
                });
              }
              return Promise.resolve({ ok: true, status: 200, async json() { return {}; } });
            });

            await sandbox.pollDashboard();
            await flushMicrotasks();

            const rows = doc.getElementById('repo-detail-view').querySelectorAll('.roadmap-epic-row');
            const rowAlpha = rows.find((r) => r.getAttribute('data-epic-slug') === 'epic_alpha');
            const rowBeta = rows.find((r) => r.getAttribute('data-epic-slug') === 'epic_beta');

            // Click slow epic A first, then immediately click fast epic B
            simulateDomClick(rowAlpha, sandbox);
            simulateDomClick(rowBeta, sandbox);

            // Wait well past slow epic A's 120ms resolution
            await new Promise((resolve) => setTimeout(resolve, 180));
            await flushMicrotasks(10);

            const titleText = getAllText(doc.getElementById('epic-history-title'));
            const bodyText = getAllText(doc.getElementById('epic-history-body'));
            assert.ok(titleText.includes('Beta Winning Epic'), `Expected Beta title to win, got: ${titleText}`);
            assert.ok(!titleText.includes('Alpha Legacy Epic'), 'Stale Alpha title must never overwrite Beta');
            assert.ok(bodyText.includes('Beta winning log'), 'Expected Beta log to remain visible');
            assert.ok(!bodyText.includes('Alpha stale log'), 'Stale Alpha log must never overwrite Beta');
            assert.ok(abortedEpics.includes('epic_alpha'), 'Opening epic_beta must abort epic_alpha in-flight request');

            console.log(JSON.stringify({ ok: true, abortedEpics }));
            """
        )
        assert res["ok"] is True

    def test_cehm_real_run_task_checks_evidence_and_absent_review_ui(
        self, tmp_path: Path
    ) -> None:
        """Real run_task_checks evidence (no top-level status), absent reviews, and Backlog status label."""
        repo_dir = tmp_path / "demo_repo"
        epic_slug = "real_ev_epic"
        epic_dir = repo_dir / ".devtool" / "epic" / epic_slug
        ev_dir = epic_dir / "evidence"
        feat_dir = repo_dir / ".devtool" / "features"
        ev_dir.mkdir(parents=True)
        feat_dir.mkdir(parents=True)

        (epic_dir / f"{epic_slug}.en.md").write_text(
            "# Real Evidence Epic\n\n- **Status**: In Progress\n",
            encoding="utf-8",
        )
        (feat_dir / "task_01_pass.md").write_text(
            "---\nid: task_01_pass\ntitle: Passing Evidence Task\nstatus: done\npriority: high\nepic: real_ev_epic\n---\n",
            encoding="utf-8",
        )
        (feat_dir / "task_02_fail.md").write_text(
            "---\nid: task_02_fail\ntitle: Failing Evidence Task\nstatus: in-progress\npriority: high\nepic: real_ev_epic\n---\n",
            encoding="utf-8",
        )

        # Real run_task_checks.py format: {schema, task, runs: {red, verify}} with NO top-level "status"
        (ev_dir / "task_01_pass.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "task": "task_01_pass",
                    "runs": {
                        "red": {
                            "head": "11111111",
                            "passed": True,
                            "rows": [
                                {
                                    "id": "V1",
                                    "phase": "RED",
                                    "command": "pytest -q",
                                    "outcome": "PASS",
                                }
                            ],
                        },
                        "verify": {
                            "head": "abc123def456",
                            "started": "2026-11-15T01:00:00Z",
                            "finished": "2026-11-15T01:01:00Z",
                            "passed": True,
                            "rows": [
                                {
                                    "id": f"V{i}",
                                    "phase": "GREEN",
                                    "command": f"check_{i}",
                                    "outcome": "PASS",
                                    "output_tail": [f"passed row {i}"],
                                }
                                for i in range(1, 7)
                            ],
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        (ev_dir / "task_02_fail.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "task": "task_02_fail",
                    "runs": {
                        "red": {
                            "head": "22222222",
                            "passed": True,
                            "rows": [
                                {
                                    "id": "V1",
                                    "phase": "RED",
                                    "command": "pytest -q",
                                    "outcome": "PASS",
                                }
                            ],
                        },
                        "verify": {
                            "head": "fed456cba321",
                            "started": "2026-11-15T01:02:00Z",
                            "finished": "2026-11-15T01:03:00Z",
                            "passed": False,
                            "rows": [
                                {
                                    "id": f"V{i}",
                                    "phase": "GREEN" if i <= 4 else "TIER-C",
                                    "command": f"check_{i}",
                                    "outcome": "PASS" if i <= 4 else "FAIL",
                                    "reason": "" if i <= 4 else "Assertion failed",
                                    "output_tail": [f"row {i}"],
                                }
                                for i in range(1, 7)
                            ],
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

        backlog_slug = "backlog_only_epic"
        backlog_dir = repo_dir / ".devtool" / "epic" / backlog_slug
        backlog_dir.mkdir(parents=True)
        (backlog_dir / f"{backlog_slug}.en.md").write_text(
            "# Backlog Epic\n\nNo tasks or reviews yet.\n",
            encoding="utf-8",
        )

        check_tasks_mod = _load_check_tasks_module()
        harvested = check_tasks_mod.harvest_epic_history(repo_dir, epic_slug)
        harvested["reviews"] = {
            "principal": parse_review_results(
                repo_dir, active_epic=epic_slug, kind="principal", strict_epic=True
            ),
            "cross_model": parse_review_results(
                repo_dir, active_epic=epic_slug, kind="cross-model", strict_epic=True
            ),
        }
        harvested_backlog = check_tasks_mod.harvest_epic_history(repo_dir, backlog_slug)
        harvested_backlog["reviews"] = {
            "principal": parse_review_results(
                repo_dir, active_epic=backlog_slug, kind="principal", strict_epic=True
            ),
            "cross_model": parse_review_results(
                repo_dir, active_epic=backlog_slug, kind="cross-model", strict_epic=True
            ),
        }

        tasks_by_id = {t["id"]: t for t in harvested["tasks"]}
        assert tasks_by_id["task_01_pass"]["evidence"]["status"] == ""
        assert tasks_by_id["task_01_pass"]["evidence"]["passed_rows"] == 6
        assert tasks_by_id["task_01_pass"]["evidence"]["total_rows"] == 6
        assert tasks_by_id["task_02_fail"]["evidence"]["status"] == ""
        assert tasks_by_id["task_02_fail"]["evidence"]["passed_rows"] == 4
        assert tasks_by_id["task_02_fail"]["evidence"]["total_rows"] == 6
        assert harvested["reviews"]["principal"]["present"] is False
        assert harvested["reviews"]["principal"]["available_rounds"] == [1]
        assert harvested["reviews"]["cross_model"]["present"] is False
        assert harvested["reviews"]["cross_model"]["available_rounds"] == [1]
        assert harvested_backlog["epic"]["status"] == "unstarted"

        payload_real_json = json.dumps({"success": True, **harvested})
        payload_backlog_json = json.dumps({"success": True, **harvested_backlog})

        res = _eval_cehm_js(
            f"""
            const payloadReal = {payload_real_json};
            const payloadBacklog = {payload_backlog_json};

            const {{ sandbox, doc }} = createCehmDomHarness(async (url) => {{
              const parsed = new URL(url, 'http://127.0.0.1:8766');
              if (parsed.pathname === '/api/epic/history') {{
                const ep = parsed.searchParams.get('epic');
                return {{
                  ok: true,
                  status: 200,
                  async json() {{
                    return ep === 'backlog_only_epic' ? payloadBacklog : payloadReal;
                  }},
                }};
              }}
              return {{ ok: true, status: 200, async json() {{ return {{}}; }} }};
            }});

            await sandbox.openEpicHistoryModal('demo_repo', 'real_ev_epic');
            await flushMicrotasks();

            const modal = doc.getElementById('modal-epic-history');
            const bodyEl = doc.getElementById('epic-history-body');
            const findTab = (name) => findAllByPredicate(modal, (el) => el.getAttribute('data-history-tab') === name)[0];

            // 1. Real run_task_checks.py evidence with empty status derives PASS 6/6 (#34d399) and FAIL 4/6 (#f87171)
            simulateDomClick(findTab('tasks'), sandbox);
            const tasksText = getAllText(bodyEl);
            assert.ok(tasksText.includes('PASS 6/6'), `Expected PASS 6/6, got: ${{tasksText}}`);
            assert.ok(tasksText.includes('FAIL 4/6'), `Expected FAIL 4/6, got: ${{tasksText}}`);
            assert.ok(!tasksText.includes('UNKNOWN'), `Must NOT render UNKNOWN for real evidence rows: ${{tasksText}}`);

            const passCard = findAllByPredicate(bodyEl, (el) => el.getAttribute('data-task-id') === 'task_01_pass')[0];
            const failCard = findAllByPredicate(bodyEl, (el) => el.getAttribute('data-task-id') === 'task_02_fail')[0];
            assert.ok(passCard.innerHTML.includes('#34d399') && passCard.innerHTML.includes('PASS 6/6'));
            assert.ok(failCard.innerHTML.includes('#f87171') && failCard.innerHTML.includes('FAIL 4/6'));

            // Direct variant status coverage (PASSED/DONE -> #34d399, FAILED -> #f87171, 0/0 -> UNKNOWN #fbbf24)
            const variantHtml = sandbox.renderEpicHistoryTasksTab({{
              tasks: [
                {{ id: 't_passed', title: 'Passed', status: 'done', evidence: {{ status: 'passed', passed_rows: 2, total_rows: 2 }} }},
                {{ id: 't_done', title: 'Done', status: 'done', evidence: {{ status: 'done', passed_rows: 1, total_rows: 1 }} }},
                {{ id: 't_failed', title: 'Failed', status: 'in-progress', evidence: {{ status: 'failed', passed_rows: 1, total_rows: 2 }} }},
                {{ id: 't_empty', title: 'Empty', status: 'todo', evidence: {{ status: '', passed_rows: 0, total_rows: 0 }} }},
              ],
            }});
            assert.ok(variantHtml.includes('color: #34d399') && variantHtml.includes('PASSED 2/2') && variantHtml.includes('DONE 1/1'));
            assert.ok(variantHtml.includes('color: #f87171') && variantHtml.includes('FAILED 1/2'));
            assert.ok(variantHtml.includes('color: #fbbf24') && variantHtml.includes('UNKNOWN 0/0'));

            // 2. Absent review report renders zero Round buttons (no stray Round 1 button)
            simulateDomClick(findTab('principal'), sandbox);
            assert.equal(bodyEl.querySelectorAll('[data-review-round]').length, 0, 'Absent Principal Review must render zero Round buttons');
            assert.ok(getAllText(bodyEl).includes('No Principal Review report recorded for this epic yet.'));

            simulateDomClick(findTab('cross_model'), sandbox);
            assert.equal(bodyEl.querySelectorAll('[data-review-round]').length, 0, 'Absent Cross-Model Review must render zero Round buttons');
            assert.ok(getAllText(bodyEl).includes('No Cross-Model Review report recorded for this epic yet.'));

            // 3. Unstarted epic badge aligns with Roadmap "Backlog" label
            await sandbox.openEpicHistoryModal('demo_repo', 'backlog_only_epic');
            await flushMicrotasks();
            assert.equal(doc.getElementById('epic-history-status-badge').textContent, 'Backlog', 'Unstarted epic modal badge must say Backlog');

            console.log(JSON.stringify({{ ok: true }}));
            """
        )
        assert res["ok"] is True

    def test_cehm_reopen_after_close_on_fetch_reject_and_scroll_preservation(
        self,
    ) -> None:
        """Close resets stale data/status so reopen+reject shows clean error without polling; scrollTop and data-* attrs hold."""
        res = _eval_cehm_js(
            r"""
            let historyCalls = 0;
            let rejectNextHistory = false;
            let timelineMsg = 'Live step before close';

            const makePayload = () => ({
              success: true,
              epic: {
                slug: 'live_reopen_epic',
                title: 'Live Reopen Epic',
                status: 'in_progress',
                pic: 'phungthuy8901',
                done_tasks: 0,
                total_tasks: 1,
                last_updated_human: '1m ago',
              },
              pipeline_telemetry: { epic_slug: 'live_reopen_epic', current_stage_index: 3, stages: [], events: [] },
              tasks: [],
              timeline: [
                { ts: '2026-11-15T01:00:00Z', category: 'step', stage: 'Stage 3', sub_step: 'run', detail: '', message: timelineMsg, source: 'heartbeat' },
              ],
              reviews: { principal: { present: false, findings: [] }, cross_model: { present: false, findings: [] } },
              log_completeness: 'full_stream',
            });

            const repo = {
              name: 'ai-agent-tools',
              path: '/tmp/ai-agent-tools',
              theme_color: '#38bdf8',
              active_epic: 'live_reopen_epic',
              worktrees: [{ path: '/tmp/ai-agent-tools', branch: 'feat/live', dirty_files_count: 0 }],
              pipeline_telemetry: {
                epic_slug: 'live_reopen_epic',
                task_completion_pct: 50,
                lifecycle_progress_pct: 50,
                current_stage_index: 3,
                stages: [{ id: 'tasks', index: 3, label: '3. Tasks', status: 'running', summary: '1/2', sub_steps: [] }],
                events: Array.from({ length: 6 }, (_, idx) => ({
                  ts: `2026-11-15T01:0${idx}:00Z`,
                  stage: 'Tasks',
                  sub_step: 'verify',
                  message: `Event ${idx + 1}`,
                })),
              },
              epics_summary: {
                total: 1,
                completed: 0,
                in_progress: 1,
                unstarted: 0,
                abandoned: 0,
                epics: [
                  { slug: 'live_reopen_epic', status: 'in_progress', task_count: 1, pic: 'phungthuy8901', last_updated_human: '1m ago' },
                ],
              },
            };

            const { sandbox, doc } = createCehmDomHarness(async (url) => {
              const parsed = new URL(url, 'http://127.0.0.1:8766');
              if (parsed.pathname === '/api/tasks') {
                return {
                  ok: true,
                  status: 200,
                  async json() { return { repos: [repo], available_profiles: ['phungthuy8901', 'danhdue'] }; },
                };
              }
              if (parsed.pathname === '/api/epic/history') {
                historyCalls += 1;
                if (rejectNextHistory) {
                  throw new Error('Upstream timeout');
                }
                return {
                  ok: true,
                  status: 200,
                  async json() { return makePayload(); },
                };
              }
              return { ok: true, status: 200, async json() { return {}; } };
            });

            await sandbox.pollDashboard();
            await flushMicrotasks();

            // 1. Verify data-attribute onclick/onchange handlers (no single-quoted string interpolation)
            const detailView = doc.getElementById('repo-detail-view');
            const logToggleBtn = findAllByPredicate(detailView, (el) => el.hasAttribute('data-epic-key'))[0];
            assert.ok(logToggleBtn, 'Execution logs toggle button must carry data-epic-key attribute');
            assert.ok(
              (logToggleBtn.getAttribute('onclick') || '').includes("this.getAttribute('data-epic-key')"),
              'toggleEpicEventLogs must read data-epic-key via this.getAttribute',
            );
            simulateDomClick(logToggleBtn, sandbox);

            const picSelect = detailView.querySelectorAll('.select-pic-roadmap')[0];
            assert.ok(picSelect, 'Roadmap PIC select must exist');
            assert.ok(
              (picSelect.getAttribute('onchange') || '').includes("this.getAttribute('data-repo')"),
              'updateEpicPic onchange must read data-repo via this.getAttribute',
            );

            // 2. Open in_progress epic and verify scrollTop preservation + no-op skip on silent poll
            const row = detailView.querySelectorAll('.roadmap-epic-row')[0];
            simulateDomClick(row, sandbox);
            await flushMicrotasks();

            const statusBadge = doc.getElementById('epic-history-status-badge');
            const bodyEl = doc.getElementById('epic-history-body');
            assert.equal(statusBadge.textContent, 'In Progress');
            assert.ok(getAllText(bodyEl).includes('Live step before close'));

            let innerHtmlWrites = 0;
            const protoDesc = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(bodyEl), 'innerHTML');
            Object.defineProperty(bodyEl, 'innerHTML', {
              configurable: true,
              get() {
                return protoDesc.get.call(this);
              },
              set(val) {
                innerHtmlWrites += 1;
                protoDesc.set.call(this, val);
                this.scrollTop = 0; // Simulate browser resetting scrollTop on innerHTML replacement
              },
            });

            bodyEl.scrollTop = 240;
            await sandbox.pollDashboard();
            await flushMicrotasks();
            assert.equal(innerHtmlWrites, 0, 'Identical poll payload must NOT rewrite #epic-history-body.innerHTML');
            assert.equal(bodyEl.scrollTop, 240, 'scrollTop must stay intact across identical silent poll');

            timelineMsg = 'Live step tick 2';
            await sandbox.pollDashboard();
            await flushMicrotasks();
            assert.equal(innerHtmlWrites, 1, 'Changed poll payload must update #epic-history-body.innerHTML');
            assert.equal(bodyEl.scrollTop, 240, 'scrollTop must be restored immediately after DOM update');
            assert.ok(getAllText(bodyEl).includes('Live step tick 2'));
            delete bodyEl.innerHTML;

            // 3. Close modal -> verify pollDashboard does NOT fetch while closed
            sandbox.closeLiveModal('modal-epic-history');
            const callsAtClose = historyCalls;
            await sandbox.pollDashboard();
            await flushMicrotasks();
            assert.equal(historyCalls, callsAtClose, 'Closed modal must NOT poll /api/epic/history');

            // 4. Reopen same epic when fetch rejects -> clean error banner, no stale body/status, and pollDashboard stops
            rejectNextHistory = true;
            simulateDomClick(row, sandbox);
            await flushMicrotasks();

            const errBanner = doc.getElementById('epic-history-error-banner');
            assert.ok(errBanner && errBanner.style.display !== 'none', 'Error banner must appear when reopen fetch rejects');
            assert.ok(getAllText(errBanner).includes('Upstream timeout'));
            const bodyTextOnError = getAllText(bodyEl);
            assert.ok(!bodyTextOnError.includes('Live step tick 2'), 'Stale previous body must NOT remain after close + reopen failure');
            assert.ok(bodyTextOnError.includes('Unable to load epic history'), 'Error body must replace loading message');
            assert.notEqual(statusBadge.textContent, 'In Progress', 'Stale loaded status badge must NOT remain on error');

            const callsAfterReject = historyCalls;
            await sandbox.pollDashboard();
            await flushMicrotasks();
            assert.equal(historyCalls, callsAfterReject, 'pollDashboard() must NOT trigger silent refresh while modal is in error state');

            console.log(JSON.stringify({ ok: true }));
            """
        )
        assert res["ok"] is True


def test_cehm_regression_round1_substeps_strip_and_malformed_json() -> None:
    """Regression #4 & #5:
    - #4: History modal stepper renders the required sub-step strip when telemetry supplies sub-steps.
    - #5: Malformed HTTP 200 JSON decoding failures propagate to show the Retry error banner.
    """
    res = _eval_cehm_js(
        r"""
            let returnMalformedJson = false;

            const makePayload = () => ({
              success: true,
              epic: {
                slug: 'substep_test_epic',
                title: 'Substep Test Epic',
                status: 'in_progress',
                pic: 'danhdue',
                has_worktree: true,
                done_tasks: 1,
                total_tasks: 2,
                last_updated_human: 'just now',
              },
              pipeline_telemetry: {
                epic_slug: 'substep_test_epic',
                current_stage_index: 5,
                stages: [
                  { id: 'gate_1', index: 1, label: '1. Inception', status: 'done', summary: 'Gate 1', sub_steps: [] },
                  { id: 'gate_2', index: 2, label: '2. Design', status: 'done', summary: 'Gate 2', sub_steps: [] },
                  { id: 'tasks', index: 3, label: '3. Tasks', status: 'done', summary: 'Tasks Done', sub_steps: [] },
                  { id: 'gate_4', index: 4, label: '4. QA Gate', status: 'done', summary: 'Gate 4', sub_steps: [] },
                  {
                    id: 'cross_review',
                    index: 5,
                    label: '5. Review',
                    status: 'running',
                    summary: 'Cross-Model Review',
                    sub_steps: [
                      { id: 'reviewing', label: 'Reviewing', status: 'done', detail: '' },
                      { id: 'triage', label: 'Triage', status: 'running', detail: 'AUTO_FIX_ELIGIBLE' },
                      { id: 'fixing', label: 'Fixing', status: 'pending', detail: '' },
                      { id: 'verifying', label: 'Verifying', status: 'pending', detail: '' },
                    ],
                  },
                  { id: 'gate_5', index: 6, label: '6. Sign-off', status: 'pending', summary: 'Gate 5', sub_steps: [] },
                ],
                events: [],
              },
              tasks: [],
              timeline: [],
              reviews: { principal: { present: false, findings: [] }, cross_model: { present: false, findings: [] } },
              log_completeness: 'full_stream',
            });

            const { sandbox, doc } = createCehmDomHarness(async (url) => {
              const parsed = new URL(url, 'http://127.0.0.1:8766');
              if (parsed.pathname === '/api/tasks') {
                return {
                  ok: true,
                  status: 200,
                  async json() {
                    return {
                      repos: [{
                        name: 'demo-repo',
                        path: '/tmp/demo-repo',
                        active_epic: 'substep_test_epic',
                        epics_summary: {
                          total: 1,
                          completed: 0,
                          in_progress: 1,
                          unstarted: 0,
                          abandoned: 0,
                          epics: [{ slug: 'substep_test_epic', status: 'in_progress', task_count: 2, pic: 'danhdue' }],
                        },
                      }],
                      available_profiles: ['danhdue'],
                    };
                  },
                };
              }
              if (parsed.pathname === '/api/epic/history') {
                if (returnMalformedJson) {
                  return {
                    ok: true,
                    status: 200,
                    async json() {
                      throw new SyntaxError('Unexpected token < in JSON at position 0');
                    },
                  };
                }
                return {
                  ok: true,
                  status: 200,
                  async json() { return makePayload(); },
                };
              }
              throw new Error(`Unexpected URL: ${url}`);
            });

            await sandbox.pollDashboard();
            await flushMicrotasks();

            // 1. Verify Finding #4: History modal stepper renders sub-steps strip
            sandbox.openEpicHistoryModal('demo-repo', 'substep_test_epic');
            await flushMicrotasks();

            const stepperEl = doc.getElementById('epic-history-stepper');
            assert.ok(stepperEl, 'Modal must contain #epic-history-stepper');
            const subStepsStrip = findAllByPredicate(stepperEl, (el) => el.getAttribute('data-telemetry') === 'sub-steps');
            assert.ok(subStepsStrip.length >= 1, 'Stepper must render [data-telemetry="sub-steps"] container');
            const subStepElements = stepperEl.querySelectorAll('[data-substep-id]');
            assert.ok(subStepElements.length >= 4, `Expected at least 4 sub-step chips, got ${subStepElements.length}`);
            const triageChip = subStepElements.find((el) => el.getAttribute('data-substep-id') === 'triage');
            assert.ok(triageChip, 'Stepper must contain triage sub-step chip');
            assert.ok(getAllText(triageChip).includes('Triage'), 'Triage chip must render label');

            // 2. Verify Finding #5: JSON decoding failure propagates and shows error banner + retry
            returnMalformedJson = true;
            sandbox.refreshEpicHistoryModal();
            await flushMicrotasks();

            const errBanner = doc.getElementById('epic-history-error-banner');
            assert.ok(errBanner && errBanner.style.display !== 'none', 'Error banner must be visible on malformed JSON response');
            const bannerText = getAllText(errBanner);
            assert.ok(bannerText.includes('Failed to parse epic history JSON') || bannerText.includes('Unexpected token'),
              `Error banner should describe JSON failure, got: ${bannerText}`);
            const retryBtns = errBanner.querySelectorAll('button');
            assert.ok(retryBtns.length >= 1, 'Error banner must provide a Retry button');

            console.log(JSON.stringify({ ok: true }));
        """
    )
    assert res["ok"] is True
