import { it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import fs from 'fs';
import path from 'path';
import { officialSource } from '../utils/officialSource';
import { formatDateTime } from '../utils/date';
import { RegulationDirectory } from '../components/RegulationDirectory';
import { Header } from '../components/Header';
import { RuleDetailModal } from '../components/RuleDetailModal';
import { api } from '../services/api';
import { OpsStatus, RuleDetailResponse, RulesResponse } from '../types';
const root=path.resolve(__dirname,'../../../public/api/v1');
const rules: RulesResponse=JSON.parse(fs.readFileSync(path.join(root,'rules.json'),'utf8'));
const detail: RuleDetailResponse=JSON.parse(fs.readFileSync(path.join(root,'rules/law-001671.json'),'utf8'));
afterEach(()=>{cleanup();vi.restoreAllMocks();});

it('counts only visible directory rows for current, historical, domain and search',()=>{
  const {container}=render(<RegulationDirectory rules={rules.rules} onSelectRule={vi.fn()}/>);
  const check=(n:number)=>{expect(container.querySelectorAll('.directory-table-row')).toHaveLength(n);expect(container.querySelector('.section-badge')?.textContent).toContain(`${n}개`);};
  check(105); expect(screen.getByText('현행 105개')).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText('폐지 규정 포함'));check(107);
  fireEvent.change(screen.getByLabelText('업무 분야 필터'),{target:{value:'의료'}});
  check(rules.rules.filter(r=>r.business_domains.includes('의료')).length);
  fireEvent.change(screen.getByLabelText('규정명 및 이전 명칭 검색'),{target:{value:'law-001671'}});check(0);
  fireEvent.change(screen.getByLabelText('업무 분야 필터'),{target:{value:'all'}});check(1);
});

it('preserves official administrative links and refuses invented identifiers',()=>{
  for(const r of rules.rules.filter(r=>r.source_kind==='admrul')) expect(officialSource(r)).toBe(r.official_source_url);
  expect(officialSource({source_kind:'law',effective_date:'2027-02-05'})).toBe('https://www.law.go.kr/');
  expect(officialSource({official_source_url:'https://evil.example/law'})).toBe('https://www.law.go.kr');
});

it.each([detail.current,...detail.upcoming])('links the exact structured state $version_id / $metadata.effective_date',(state)=>{
  const url=new URL(officialSource(state));
  expect(url.searchParams.get('lsiSeq')).toBe(state.version_id);
  expect(url.searchParams.get('efYd')).toBe(state.metadata.effective_date!.replace(/-/g,''));
});

it('keeps future source links on the selected state in both comparison modes',async()=>{
  vi.spyOn(api,'getRuleDetail').mockResolvedValue(detail);
  const {container}=render(<RuleDetailModal rule={detail.rule} initialEffectiveDate="2027-02-05" onClose={vi.fn()}/>);
  await waitFor(()=>expect(screen.getByText('직전 시행상태 대비 해당 시행일에 새로 달라지는 조문입니다.')).toBeInTheDocument());
  for(const day of ['2027.02.05','2027.08.05','2027.12.31']) {
    fireEvent.click(screen.getByRole('tab',{name:`시행 예정 ${day} 시행 예정`}));
    const links=[...container.querySelectorAll<HTMLAnchorElement>('a')].filter(a=>a.textContent?.includes('공식 원문'));
    expect(links.length).toBeGreaterThanOrEqual(2);
    for(const a of links) expect(new URL(a.href).searchParams.get('efYd')).toBe(day.replace(/\./g,''));
    fireEvent.click(screen.getByRole('button',{name:'현재 기준 누적 비교'}));
    expect(screen.getByText('현재 시행상태 대비 해당 날짜까지 누적된 변경입니다.')).toBeInTheDocument();
    for(const a of links) expect(new URL(a.href).searchParams.get('efYd')).toBe(day.replace(/\./g,''));
  }
});

it('separates last successful scan from legal data publication and missing status',()=>{
  const health=JSON.parse(fs.readFileSync(path.join(root,'health.json'),'utf8'));
  const ops={last_scan_status:'OK',last_scan_result:'NO_CHANGE',last_scan_completed_at:'2026-10-06T00:40:00Z',schedule_kst:['08:37','20:37']} as OpsStatus;
  const {rerender}=render(<Header health={health} ops={ops}/>);
  expect(screen.getByText('2026.10.06 09:40 · 정상')).toBeInTheDocument();
  expect(screen.getByText('변경 없음')).toBeInTheDocument();
  expect(screen.getByText(formatDateTime(health.last_successful_sync))).toBeInTheDocument();
  expect(screen.getByText(/08:37 · 20:37/)).toBeInTheDocument();
  rerender(<Header health={health} ops={null}/>);
  expect(screen.queryByText('변경 없음')).not.toBeInTheDocument();
});

it('keeps a historical event with zero changed articles on its own official state',async()=>{
  vi.spyOn(api,'getRuleDetail').mockResolvedValue(detail);
  const events=JSON.parse(fs.readFileSync(path.join(root,'changes/history.json'),'utf8')).events;
  const event=events.find((e: {canonical_id:string;changed_article_count:number;after_version:{identifier:string}})=>e.canonical_id==='law-001671' && e.changed_article_count===0 && e.after_version.identifier==='290189');
  render(<RuleDetailModal rule={detail.rule} initialEvent={event} onClose={vi.fn()}/>);
  await waitFor(()=>expect(screen.getByRole('link',{name:'공식 원문'})).toHaveAttribute('href','https://www.law.go.kr/LSW/lsInfoP.do?efYd=20261002&lsiSeq=290189'));
});
