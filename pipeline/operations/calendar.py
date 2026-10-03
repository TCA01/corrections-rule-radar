"""Effective dates are civil dates. Only an instant is converted to Seoul."""
from datetime import date,datetime,timedelta,timezone

SEOUL=timezone(timedelta(hours=9))
def seoul_date(instant=None):
    instant=instant or datetime.now(timezone.utc)
    if instant.tzinfo is None: raise ValueError('TIMESTAMP_TIMEZONE_REQUIRED')
    return instant.astimezone(SEOUL).date()
def d_day(effective_date,instant=None):
    return (date.fromisoformat(effective_date)-seoul_date(instant)).days
