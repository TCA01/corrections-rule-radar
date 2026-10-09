import { afterEach, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { Header } from '../components/Header';
import { OpsStatus } from '../types';

afterEach(cleanup);
const base={last_scan_status:'OK',last_scan_result:'NO_CHANGE',last_scan_completed_at:'2026-10-09T00:05:00Z',schedule_kst:['08:37','20:37']} as OpsStatus;

it('labels an actual scheduled check as automatic and renders Korea time',()=>{
  render(<Header health={null} ops={{...base,trigger:'SCHEDULE'}}/>);
  expect(screen.getByText('최근 자동 확인')).toBeInTheDocument();
  expect(screen.getByText('2026.10.09 09:05 · 정상')).toBeInTheDocument();
  expect(screen.queryByText(/수동 실행/)).not.toBeInTheDocument();
});

it('preserves independently visible scheduled freshness after a manual rehearsal',()=>{
  render(<Header health={null} ops={{...base,trigger:'MANUAL',last_scheduled_scan:{started_at:'2026-10-06T17:24:14Z',completed_at:'2026-10-06T17:32:06Z',result:'NO_CHANGE',dataset_version:'ds-'+'1'.repeat(64),cron:'37 11 * * *',github_run_id:'37503211648'}}}/>);
  expect(screen.getByText('최근 시스템 확인')).toBeInTheDocument();
  expect(screen.getByText('2026.10.09 09:05 · 정상 · 수동 실행')).toBeInTheDocument();
  expect(screen.getByText('최근 예약 확인: 2026.10.07 02:32')).toBeInTheDocument();
  expect(screen.queryByText('최근 자동 확인')).not.toBeInTheDocument();
});

it('never infers an automatic trigger from legacy status or missing data',()=>{
  const {rerender}=render(<Header health={null} ops={base}/>);
  expect(screen.queryByText('최근 자동 확인')).not.toBeInTheDocument();
  rerender(<Header health={null} ops={null}/>);
  expect(screen.getByText('확인 기록을 불러오지 못했습니다')).toBeInTheDocument();
  expect(screen.queryByText(/· 정상/)).not.toBeInTheDocument();
});
