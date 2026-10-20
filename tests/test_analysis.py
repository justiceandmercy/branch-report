import datetime
from branch_report.analysis import Branch, classify, is_protected, age_days, suggest_cleanup


def test_age_days():
    now = datetime.datetime(2026, 10, 20, tzinfo=datetime.timezone.utc)
    b = Branch(name='x', last_commit_date=datetime.datetime(2026, 9, 20, tzinfo=datetime.timezone.utc))
    assert age_days(b, now) == 30


def test_classify_stale():
    now = datetime.datetime(2026, 10, 20, tzinfo=datetime.timezone.utc)
    cfg = type('C', (), {'stale_days': 30, 'protected': []})()
    b = Branch(name='feature', last_commit_date=datetime.datetime(2026, 8, 1, tzinfo=datetime.timezone.utc), merged=False)
    labs = classify(b, cfg, now=now)
    assert 'stale' in labs


def test_classify_merged():
    cfg = type('C', (), {'stale_days': 30, 'protected': []})()
    b = Branch(name='feature', last_commit_date=datetime.datetime.now(datetime.timezone.utc), merged=True)
    labs = classify(b, cfg)
    assert 'merged' in labs


def test_protected():
    assert is_protected('main', ['main', 'master'])
    assert is_protected('release/1.0', ['release/*'])
    assert not is_protected('feature/x', ['main'])


def test_suggest_cleanup_skips_protected():
    now = datetime.datetime(2026, 10, 20, tzinfo=datetime.timezone.utc)
    cfg = type('C', (), {'stale_days': 30, 'protected': ['main']})()
    branches = [
        Branch(name='main', last_commit_date=now, merged=False),
        Branch(name='old', last_commit_date=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc), merged=False),
    ]
    sugs = suggest_cleanup(branches, cfg, now=now)
    names = [b.name for b, _ in sugs]
    assert 'old' in names
    assert 'main' not in names
