import json
from branch_report.config import Config


def test_from_dict_defaults():
    c = Config.from_dict({})
    assert c.base == 'main'
    assert c.stale_days == 30


def test_load_file(tmp_path):
    p = tmp_path / 'cfg.json'
    p.write_text(json.dumps({'base': 'develop', 'stale_days': 14}))
    c, src = Config.load(str(p))
    assert c.base == 'develop'
    assert c.stale_days == 14
    assert src == str(p)


def test_save_roundtrip(tmp_path):
    c = Config.from_dict({'base': 'dev'})
    p = tmp_path / 'out.json'
    c.save(str(p))
    c2, _ = Config.load(str(p))
    assert c2.base == 'dev'
