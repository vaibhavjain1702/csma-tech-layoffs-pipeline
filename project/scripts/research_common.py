"""Shared preparation helpers; no network access or third-party dependencies."""
import hashlib
import html
import re
from urllib.parse import urlsplit

URL = re.compile(r'https?://[^\s<>]+', re.I)
SPACE = re.compile(r'\s+')


def author_key(author):
    if not isinstance(author, str) or not author or author.lower() in {'[deleted]', '[removed]'}:
        return None
    return 'u_' + hashlib.sha256(author.lower().encode()).hexdigest()[:24]


def prepare_text(text, available=True):
    if not available:
        return {'clean_text': '', 'own_text': '', 'quoted_text': '', 'urls': [], 'word_count': 0, 'char_count': 0}
    decoded = html.unescape(text or '').replace('\r\n', '\n').replace('\r', '\n')
    quotes, own = [], []
    for line in decoded.splitlines():
        if line.lstrip().startswith('>'):
            quotes.append(line.lstrip().lstrip('>').strip())
        else:
            own.append(line)
    clean = SPACE.sub(' ', decoded).strip()
    return {'clean_text': clean, 'own_text': SPACE.sub(' ', '\n'.join(own)).strip(),
            'quoted_text': '\n'.join(quotes), 'urls': list(dict.fromkeys(u.rstrip('.,;!?)]}') for u in URL.findall(decoded))),
            'word_count': len(clean.split()), 'char_count': len(clean)}


def domain_of(url):
    try:
        return urlsplit(url or '').hostname
    except ValueError:
        return None


def thread_depths(comments, root_id):
    """Depth 1 = reply to root; unknown/cyclic ancestry gets depth None.

    Works on one thread at a time. Depth is resolved iteratively to avoid
    recursion limits. Missing submission content does not invalidate the known
    structural root. An absent intermediate parent does invalidate full depth.
    """
    parents = {r['id']: r['parent_id'] for r in comments}
    resolved = {}
    for start in parents:
        if start in resolved:
            continue
        path, visited, current = [], set(), start
        while current not in resolved:
            if current in visited:
                base = (None, 'cycle')
                break
            if current not in parents:
                base = (None, 'missing_parent')
                break
            path.append(current)
            visited.add(current)
            parent = parents[current]
            if parent == root_id:
                base = (0, 'resolved')
                break
            if not parent or not parent.startswith('t1_'):
                base = (None, 'invalid_parent')
                break
            current = parent[3:]
        else:
            base = resolved[current]
        depth, state = base
        for node in reversed(path):
            depth = depth + 1 if depth is not None else None
            resolved[node] = (depth, state)
    return resolved
