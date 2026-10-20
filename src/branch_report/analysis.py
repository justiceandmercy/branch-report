import fnmatch
import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Branch:
    name: str
    remote: bool = False
    last_commit_date: Optional[datetime.datetime] = None
    author: str = ''
    merged: bool = False
    ahead: int = 0
    behind: int = 0
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


def _short(name):
    if name.startswith('origin/'):
        return name[len('origin/'):]
    return name


def is_protected(name, patterns):
    short = _short(name)
    for p in patterns:
        if fnmatch.fnmatch(short, p) or fnmatch.fnmatch(name, p):
            return True
    return False


def age_days(branch, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if branch.last_commit_date is None:
        return None
    d = branch.last_commit_date
    if d.tzinfo is None:
        d = d.replace(tzinfo=datetime.timezone.utc)
    return (now - d).days


def classify(branch, config, now=None):
    labels = []
    if branch.merged:
        labels.append('merged')
    ad = age_days(branch, now)
    if ad is not None and ad >= config.stale_days:
        labels.append('stale')
    if not labels:
        labels.append('active')
    if is_protected(branch.name, config.protected):
        labels.append('protected')
    return labels


def suggest_cleanup(branches, config, now=None):
    suggestions = []
    for b in branches:
        labels = classify(b, config, now)
        if 'protected' in labels:
            continue
        if 'merged' in labels or 'stale' in labels:
            suggestions.append((b, labels))
    return suggestions
