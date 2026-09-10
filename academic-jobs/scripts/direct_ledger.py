#!/usr/bin/env python3
"""Validate and compare human-verified direct academic opportunity snapshots."""
import argparse
from collections import Counter
from datetime import date, datetime
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

TEXT_FIELDS = (
    'institution group pi country title rank research method_fit domain_fit '
    'transition_cost eligibility term salary funding start deadline documents '
    'application_url contact application_policy next_action'
).split()
KINDS = {'vacancy', 'standing_route', 'research_lead', 'host_funding_call'}
STATUSES = {'open', 'standing', 'prospect', 'conflict', 'expired', 'closed', 'unknown'}
ROLES = {'research', 'availability', 'deadline', 'eligibility', 'policy', 'terms', 'identity'}
RECORD_FIELDS = set(TEXT_FIELDS) | {
    'key', 'kind', 'status', 'audience', 'cutoff', 'cutoff_kind',
    'accepts_late', 'evidence', 'board_check',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    require(isinstance(value, str), 'timestamp must be a string')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'timestamp needs a timezone')
    return parsed


def day(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value),
            'date must be YYYY-MM-DD')
    return date.fromisoformat(value)


def web_url(value):
    require(isinstance(value, str), 'URL must be a string')
    parsed = urlparse(value)
    require(parsed.scheme in {'http', 'https'} and bool(parsed.hostname),
            'evidence/application URL must be HTTP(S)')
    require(parsed.username is None and parsed.password is None, 'URL must not contain credentials')


def validate(data):
    require(isinstance(data, dict), 'snapshot must be an object')
    require(data.get('schema_version') == 1, 'unsupported schema_version')
    observed = timestamp(data.get('checked_at'))
    require(isinstance(data.get('scope_id'), str) and data['scope_id'].strip(), 'scope_id required')
    require(isinstance(data.get('scope'), list) and data['scope'] and
            all(isinstance(s, str) and s.strip() for s in data['scope']), 'scope must name search boundaries')
    require(isinstance(data.get('profile'), dict), 'profile assumptions required')
    require(isinstance(data.get('records'), list), 'records must be an array')
    seen = set()
    for r in data['records']:
        require(isinstance(r, dict), 'record must be an object')
        key = r.get('key')
        require(isinstance(key, str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', key), 'invalid key')
        require(key not in seen, f'duplicate key: {key}')
        seen.add(key)
        require(RECORD_FIELDS <= r.keys(), f'{key}: missing {sorted(RECORD_FIELDS - r.keys())}')
        for field in TEXT_FIELDS:
            value = r[field]
            require(value is None or isinstance(value, str) and value.strip(), f'{key}: invalid {field}')
        require(r['institution'] and r['title'] and r['rank'], f'{key}: identity/rank required')
        require(r['country'] is None or re.fullmatch(r'[A-Z]{2}', r['country']), f'{key}: invalid ISO2 country')
        require(r['kind'] in KINDS and r['status'] in STATUSES, f'{key}: invalid kind/status')
        require(r['audience'] in {'candidate', 'supervisor', 'unknown'}, f'{key}: invalid audience')
        require(r['cutoff_kind'] in {'hard', 'priority', 'rolling', 'unknown'}, f'{key}: invalid cutoff_kind')
        require(r['accepts_late'] is None or type(r['accepts_late']) is bool, f'{key}: invalid accepts_late')
        cutoff = day(r['cutoff']) if r['cutoff'] is not None else None
        if r['application_url']:
            web_url(r['application_url'])
        require(isinstance(r['evidence'], list) and r['evidence'], f'{key}: evidence required')
        for e in r['evidence']:
            require(isinstance(e, dict) and {'url', 'quote', 'role', 'official', 'retrieved_at',
                    'source_date', 'snapshot_path'} <= e.keys(), f'{key}: incomplete evidence')
            web_url(e['url'])
            require(isinstance(e['quote'], str) and e['quote'].strip(), f'{key}: empty quote')
            require(e['role'] in ROLES and type(e['official']) is bool, f'{key}: invalid evidence role')
            require(timestamp(e['retrieved_at']) <= observed, f'{key}: evidence newer than snapshot')
            if e['source_date'] is not None:
                require(day(e['source_date']) <= timestamp(e['retrieved_at']).date(), f'{key}: future source_date')
            require(e['snapshot_path'] is None or isinstance(e['snapshot_path'], str), f'{key}: invalid evidence path')
        board = r['board_check']
        require(isinstance(board, dict) and {'status', 'matches', 'checked_at', 'note'} <= board.keys(),
                f'{key}: incomplete board_check')
        require(board['status'] in {'matched', 'not_in_local_store', 'not_checked'}, f'{key}: invalid board status')
        require(isinstance(board['matches'], list) and isinstance(board['note'], str), f'{key}: invalid board check')
        for match in board['matches']:
            require(isinstance(match, dict) and match.get('source') in {'ajo', 'inspire'} and
                    type(match.get('id')) is int and match['id'] > 0, f'{key}: invalid board identity')
        require(bool(board['matches']) == (board['status'] == 'matched'), f'{key}: inconsistent board matches')
        if board['status'] != 'not_checked':
            require(timestamp(board['checked_at']) <= observed, f'{key}: invalid board check time')
        elif board['checked_at'] is not None:
            timestamp(board['checked_at'])
        if r['status'] == 'open':
            require(r['kind'] == 'vacancy' and r['audience'] == 'candidate', f'{key}: open must be candidate vacancy')
            require(r['application_url'] or r['contact'], f'{key}: open needs application channel')
            require(any(e['official'] and e['role'] == 'availability' for e in r['evidence']),
                    f'{key}: open needs official availability evidence')
            if cutoff and cutoff < observed.date():
                require(r['cutoff_kind'] == 'priority' and r['accepts_late'] is True,
                        f'{key}: open contradicts elapsed cutoff')
        if r['status'] in {'open', 'standing'}:
            require(re.search(r'\bpost[- ]?doc(?:toral)?\b|박사\s*후', r['rank'], re.I),
                    f'{key}: open/standing route must identify a postdoc branch in rank')
        if r['status'] == 'standing':
            require(r['kind'] == 'standing_route' and r['audience'] == 'candidate', f'{key}: invalid standing route')
            require(any(e['official'] and e['role'] in {'availability', 'policy'} for e in r['evidence']),
                    f'{key}: standing route needs official policy evidence')
    return data


def substantive(record):
    result = {k: v for k, v in record.items() if k not in {'evidence', 'board_check'}}
    result['evidence'] = sorted(
        [{k: e[k] for k in ('url', 'quote', 'role', 'official', 'source_date')} for e in record['evidence']],
        key=lambda e: json.dumps(e, sort_keys=True),
    )
    result['board_check'] = {k: v for k, v in record['board_check'].items() if k != 'checked_at'}
    result['board_check']['matches'] = sorted(result['board_check']['matches'], key=lambda m: (m['source'], m['id']))
    return result


def compare(before, after, allow_scope_change=False):
    scope_changed = before['scope_id'] != after['scope_id']
    require(not scope_changed or allow_scope_change, 'different scope_id; use --allow-scope-change for partial observations')
    left = {r['key']: substantive(r) for r in before['records']}
    right = {r['key']: substantive(r) for r in after['records']}
    changed = []
    for key in sorted(left.keys() & right.keys()):
        fields = sorted(k for k in left[key].keys() | right[key].keys() if left[key].get(k) != right[key].get(k))
        if fields:
            changed.append({'key': key, 'fields': fields, 'before_status': left[key]['status'],
                            'after_status': right[key]['status']})
    return {'scope_changed': scope_changed, 'added': sorted(right.keys() - left.keys()),
            'not_observed': sorted(left.keys() - right.keys()), 'changed': changed,
            'unchanged': len(left.keys() & right.keys()) - len(changed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('validate').add_argument('snapshot', type=Path)
    diff = sub.add_parser('diff')
    diff.add_argument('before', type=Path)
    diff.add_argument('after', type=Path)
    diff.add_argument('--allow-scope-change', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'validate':
            data = validate(json.loads(args.snapshot.read_text()))
            result = {'valid': True, 'records': len(data['records']),
                      'statuses': dict(sorted(Counter(r['status'] for r in data['records']).items()))}
        else:
            before = validate(json.loads(args.before.read_text()))
            after = validate(json.loads(args.after.read_text()))
            result = compare(before, after, args.allow_scope_change)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({'valid': False, 'error': str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
