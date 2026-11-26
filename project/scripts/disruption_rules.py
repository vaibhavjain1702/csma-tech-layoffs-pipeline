"""Versioned lexical screens for review, not relevance or qualitative labels."""
import hashlib
import json
import re
from research_common import URL

VERSION = 'employment-screen-v1'
# Conditions apply within the same field (title or own body), not across a thread.
EMPLOYMENT = r'\b(?:jobs?|employment|unemploy\w*|employees?|workers?|workforce|hiring|hires?|hired|recruit\w*|careers?|layoffs?|laid\s+off|salaries|salary|wages?|engineers?|developers?)\b'
RULES = {
    'layoffs': {
        'pattern': r'\b(?:layoffs?|laid\s+off|laying\s+off|lay\s+off|job\s+cuts?|workforce\s+reductions?|reduction\s+in\s+force|downsizing|furlough\w*)\b',
        'requires_employment': False,
    },
    'hiring_conditions': {
        'pattern': r'\b(?:hiring\s+freez\w*|hiring\s+slowdown|job\s+(?:search\w*|hunt\w*|market|applications?|offers?)|looking\s+for\s+(?:a\s+)?job|unemploy\w*|recruit\w*|interviews?|resumes?|hiring)\b',
        'requires_employment': True,
    },
    'ai_work_change': {
        'pattern': r'\b(?:ai|artificial\s+intelligence|generative\s+ai|chatgpt|llms?|automation|automat\w*)\b',
        'requires_employment': True,
    },
    'corporate_restructuring': {
        'pattern': r'\b(?:restructur\w*|reorgani[sz]\w*|mergers?|acquisitions?|return\s+to\s+(?:the\s+)?office|rto|offshor\w*|outsourc\w*)\b',
        'requires_employment': True,
    },
    'economic_policy': {
        'pattern': r'\b(?:recession\w*|economy|economic|interest\s+rates?|inflation|tariffs?|immigration|visas?|h[ -]?1b|labor\s+market|labour\s+market)\b',
        'requires_employment': True,
    },
    'career_transition': {
        'pattern': r'\b(?:career\s+(?:chang\w*|transition\w*|switch\w*)|chang\w*\s+careers?|switch\w*\s+careers?|reskill\w*|upskill\w*|retrain\w*|leaving\s+(?:the\s+)?(?:tech|technology|industry)|quit\w*|resign\w*)\b',
        'requires_employment': True,
    },
}
FACETS = tuple(RULES)
FINGERPRINT = hashlib.sha256(json.dumps({'version': VERSION, 'employment': EMPLOYMENT, 'rules': RULES}, sort_keys=True).encode()).hexdigest()
COMPILED = {name: re.compile(rule['pattern'], re.I) for name, rule in RULES.items()}
EMPLOYMENT_RE = re.compile(EMPLOYMENT, re.I)


def screen(title, own_text):
    """Return matching facets and exact matched terms by field; URLs excluded.

    An employment anchor is required in the same field for contextual rules.
    Co-occurrence may span sentences. Negated claims remain candidates for reading.
    """
    evidence = {}
    for field, text in (('title', title), ('own_text', own_text)):
        text = URL.sub(' ', text or '')
        anchor = EMPLOYMENT_RE.search(text)
        for name, pattern in COMPILED.items():
            if RULES[name]['requires_employment'] and not anchor:
                continue
            terms = sorted({match.group(0) for match in pattern.finditer(text)}, key=lambda s: (s.lower(), s))
            if terms:
                item = {'field': field, 'terms': terms}
                if RULES[name]['requires_employment']:
                    item['employment_anchor'] = anchor.group(0)
                evidence.setdefault(name, []).append(item)
    return evidence
