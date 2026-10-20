import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

DEFAULT_CONFIG = {
    'base': 'main',
    'stale_days': 30,
    'protected': ['main', 'master', 'develop', 'release/*'],
    'remote': True,
    'format': 'table',
    'plugin_dir': None,
}


@dataclass
class Config:
    base: str = 'main'
    stale_days: int = 30
    protected: List[str] = field(default_factory=lambda: ['main', 'master', 'develop', 'release/*'])
    remote: bool = True
    format: str = 'table'
    plugin_dir: Optional[str] = None

    @classmethod
    def from_dict(cls, d):
        merged = {**DEFAULT_CONFIG, **(d or {})}
        return cls(
            base=merged['base'],
            stale_days=merged['stale_days'],
            protected=list(merged['protected']),
            remote=merged['remote'],
            format=merged['format'],
            plugin_dir=merged['plugin_dir'],
        )

    def to_dict(self):
        return asdict(self)

    @classmethod
    def load(cls, path=None):
        candidates = []
        if path:
            candidates.append(Path(path))
        env = os.environ.get('BRANCH_REPORT_CONFIG')
        if env:
            candidates.append(Path(env))
        candidates.append(Path.cwd() / '.branchreportrc.json')
        candidates.append(Path.home() / '.branchreportrc.json')
        for c in candidates:
            if c and c.is_file():
                try:
                    data = json.loads(c.read_text())
                    return cls.from_dict(data), str(c)
                except (json.JSONDecodeError, OSError):
                    continue
        return cls.from_dict({}), None

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + '\n')
