/** Run inside cua_repl with an existing homepage tab and viewport capability.
 * Browser actions use only the supported cua API. No synthetic DOM mutation.
 */
export function probeLayout() {
  const modal = document.querySelector('[role="dialog"]');
  if (!modal) throw new Error('Modal missing');
  const box = element => {
    const r = element.getBoundingClientRect();
    return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, height: r.height };
  };
  const failures = [];
  const appendices = [...modal.querySelectorAll('.appendix-item')].map(row => {
    const title = row.querySelector('.appendix-title');
    const info = box(row.querySelector('.appendix-info'));
    const control = row.querySelector('.appendix-action-btn,.appendix-deleted-badge');
    const action = control ? box(control) : null;
    if (action && Math.min(info.right, action.right) > Math.max(info.left, action.left) + 1
      && Math.min(info.bottom, action.bottom) > Math.max(info.top, action.top) + 1) failures.push('Appendix overlap: ' + title.textContent);
    if (row.scrollWidth > row.clientWidth + 1) failures.push('Appendix overflow: ' + title.textContent);
    if (row.classList.contains('deleted') && row.querySelector('a')) failures.push('Deleted appendix action');
    if (control?.tagName === 'A' && innerWidth <= 480 && action.height < 44) failures.push('Touch target below 44px');
    if (title.textContent.includes('&lt;') || title.textContent.includes('&gt;')) failures.push('Raw title entity');
    return { title: title.textContent, info, action, display: getComputedStyle(row).display, deleted: row.classList.contains('deleted') };
  });
  for (const content of modal.querySelectorAll('.unified-diff-content,.diff-panel .legal-text-wrap')) {
    const bounds = content.getBoundingClientRect();
    if (content.scrollWidth > content.clientWidth + 1) failures.push('Diff text overflow');
    for (const token of innerWidth <= 480 ? content.querySelectorAll('del,ins,span') : []) {
      for (const r of token.getClientRects()) {
        if (r.left < bounds.left - 1 || r.right > bounds.right + 1) failures.push('Inline token overflow');
      }
    }
  }
  if (modal.scrollWidth > modal.clientWidth + 1) failures.push('Modal overflow');
  const education = [...modal.querySelectorAll('.diff-article-card')].find(card => card.querySelector('.diff-card-title')?.textContent === '제14조(교육면제)');
  const article14 = education ? {
    text: education.textContent,
    highlights: [...education.querySelectorAll('del,ins')].map(node => ({ kind: node.tagName, text: node.textContent })),
  } : null;
  return { width: innerWidth, failures, appendices, article14 };
}

export async function verifyPhase1IMobile(tab, viewport) {
  const cases = [
    ['deleted appendix', '가석방자관리규정 조문 상세 보기'],
    ['long appendices', '형의 집행 및 수용자의 처우에 관한 법률 시행규칙 조문 상세 보기'],
    ['education14', '수용자 교육교화 운영지침 변경 내용 보기'],
  ];
  const results = [];
  for (const [name, button] of cases) {
    await tab.playwright.getByRole('button', { name: button, exact: true }).click();
    if (name === 'education14') await tab.playwright.getByText(/문구 비교: 해당 개정/).waitFor({ state: 'visible' });
    else await tab.playwright.getByText(/관련 별표·서식/).waitFor({ state: 'visible' });
    for (const width of [360, 390, 412, 1280]) {
      await viewport.set({ width, height: 800 });
      const result = await tab.playwright.evaluate(probeLayout);
      if (name === 'deleted appendix' && !result.appendices.some(row => row.deleted && row.title === '삭제 <2016.1.22.>')) result.failures.push('Expected deleted title missing');
      if (name === 'long appendices' && !result.appendices.some(row => row.title.startsWith('포승 사용방법3'))) result.failures.push('Expected long title missing');
      if (name === 'education14') {
        if (!result.article14 || result.article14.highlights.some(node => /생\s*략|현행과 같음/.test(node.text))) result.failures.push('Placeholder false diff');
        if (!result.article14?.highlights.some(node => node.kind === 'DEL' && node.text.includes('형기주기별'))) result.failures.push('Substantive change missing');
        if (!result.article14?.text.includes('5. 삭제')) result.failures.push('Literal deletion missing');
      }
      results.push({ case: name, ...result });
    }
    await tab.playwright.getByRole('button', { name: '닫기', exact: true }).click();
  }
  if (results.some(row => row.failures.length)) throw new Error(JSON.stringify(results.filter(row => row.failures.length).map(row => ({ case: row.case, width: row.width, failures: row.failures }))));
  return results;
}
