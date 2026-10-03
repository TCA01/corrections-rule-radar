import { ChangeType, RuleStatus, ClassificationStatus, AppendixItem } from '../types';

export function getChangeTypeLabel(changeType: ChangeType): string {
  switch (changeType) {
    case 'FUTURE_EFFECTIVE_VERSION':
      return '시행 예정';
    case 'RULE_AMENDED':
      return '규정 개정';
    case 'ARTICLE_CHANGED':
      return '조문 변경';
    case 'EFFECTIVE_DATE_CHANGED':
      return '시행일 변경';
    case 'APPENDIX_CHANGED':
      return '별표·서식 변경';
    case 'ATTACHMENT_CHANGED':
      return '첨부파일 변경';
    case 'RULE_RENAMED':
      return '명칭 변경';
    case 'NEW_RULE':
      return '신규 제정';
    case 'RULE_REPEALED':
      return '규정 폐지';
    case 'NEW_CORRECTIONS_SEED':
      return '추적 규정 편입';
    case 'RULE_REMOVED_FROM_CORRECTIONS_SEED':
      return '추적 제외';
    case 'DISCOVERY_CANDIDATE':
      return '신규 후보 발견';
    default:
      return changeType;
  }
}

export function getFactualDescription(
  changeType: ChangeType,
  effectiveDate?: string | null,
  articleCount?: number
): string {
  switch (changeType) {
    case 'FUTURE_EFFECTIVE_VERSION':
      return effectiveDate
        ? `${effectiveDate} 시행 예정인 조문이 공식 공포되었습니다.`
        : '향후 시행 예정인 조문이 공포되었습니다.';
    case 'ARTICLE_CHANGED':
      return articleCount && articleCount > 0
        ? `조문 ${articleCount}건의 내용 변경이 확인되었습니다.`
        : '조문 내용 변경이 확인되었습니다.';
    case 'RULE_AMENDED':
      return '규정의 개정(일부개정 등) 조항이 확인되었습니다.';
    case 'RULE_RENAMED':
      return '공식 규정 명칭이 변경되었습니다.';
    case 'APPENDIX_CHANGED':
      return '관련 별표 또는 서식의 변경이 확인되었습니다.';
    case 'ATTACHMENT_CHANGED':
      return '공식 첨부 자료의 변경이 확인되었습니다.';
    case 'RULE_REPEALED':
      return '국가법령정보센터 기준 공식 폐지된 규정입니다.';
    case 'NEW_RULE':
      return '새로운 규정이 제정되어 시행되었습니다.';
    default:
      return '공식 변경 사항이 확인되었습니다.';
  }
}

export function getStatusBadge(status: RuleStatus): { text: string; className: string } {
  switch (status) {
    case 'CURRENT':
      return { text: '현행', className: 'badge-current' };
    case 'REPEALED':
      return { text: '폐지', className: 'badge-repealed' };
    case 'REVIEW':
      return { text: '검토 중', className: 'badge-review' };
    default:
      return { text: status, className: 'badge-default' };
  }
}

export function getClassificationBadge(
  classification: ClassificationStatus,
  domains: string[]
): { text: string; className: string } {
  if (classification === 'REVIEW' || domains.length === 0) {
    return { text: '업무 분야 검토 중', className: 'badge-domain-review' };
  }
  return { text: domains.join(', '), className: 'badge-domain-reviewed' };
}

export function isRemovedAppendix(
  item:
    | AppendixItem
    | {
        title?: string | null;
        status?: string | null;
        change_type?: string | null;
        is_deleted?: boolean | null;
      }
    | null
    | undefined
): boolean {
  if (!item) return false;
  if (item.is_deleted === true) return true;
  const status = (item.status || '').trim().toUpperCase();
  if (
    status === 'REMOVED' ||
    status === 'DELETED' ||
    status === '삭제' ||
    status === 'APPENDIX_REMOVED'
  ) {
    return true;
  }
  const changeType = ((item as { change_type?: string }).change_type || '')
    .trim()
    .toUpperCase();
  if (
    changeType === 'APPENDIX_REMOVED' ||
    changeType === 'DELETED' ||
    changeType === 'REMOVED' ||
    changeType === '삭제'
  ) {
    return true;
  }
  const rawTitle = (item.title || '').trim();
  if (rawTitle === '삭제') return true;
  if (/^(\[|\()?삭제([\s(\[<\]\)>]|&lt;|$)/i.test(rawTitle)) return true;
  return false;
}
