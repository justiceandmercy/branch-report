import subprocess
import datetime
import re
from typing import List
from .analysis import Branch


class GitError(Exception):
    pass


def parse_date(s):
    s = (s or '').strip()
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace(' ', 'T'))
    except ValueError:
        return None


def parse_track(s):
    ahead = behind = 0
    m = re.search(r'ahead (\d+)', s or '')
    if m:
        ahead = int(m.group(1))
    m = re.search(r'behind (\d+)', s or '')
    if m:
        behind = int(m.group(1))
    return ahead, behind


class GitRunner:
    def __init__(self, repo='.', runner=subprocess.run):
        self.repo = repo
        self.runner = runner

    def _run(self, args):
        cmd = ['git', '-C', self.repo] + list(args)
        try:
            r = self.runner(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            raise GitError('git not found')
        if r.returncode != 0:
            raise GitError((r.stderr or '').strip() or 'git command failed')
        return r.stdout

    def is_repo(self):
        try:
            self._run(['rev-parse', '--is-inside-work-tree'])
            return True
        except GitError:
            return False

    def default_base(self):
        try:
            out = self._run(['symbolic-ref', 'refs/remotes/origin/HEAD']).strip()
            return out.split('/')[-1]
        except GitError:
            pass
        for cand in ('main', 'master'):
            try:
                self._run(['rev-parse', '--verify', cand])
                return cand
            except GitError:
                continue
        return 'main'

    def merged_branches(self, base):
        names = set()
        for flag in ([], ['-r']):
            try:
                args = ['branch'] + flag + ['--merged', base]
                out = self._run(args)
            except GitError:
                continue
            for line in out.splitlines():
                line = line.strip().lstrip('*').strip()
                if line and not line.endswith('/HEAD'):
                    names.add(line)
        return names

    def ahead_behind(self, base, branch):
        try:
            out = self._run(['rev-list', '--left-right', '--count', f'{base}...{branch}']).strip()
            left, right = out.split()
            return int(right), int(left)
        except (GitError, ValueError):
            return 0, 0

    def list_branches(self, base='main', include_remote=True):
        merged_set = self.merged_branches(base)
        branches = []
        fmt = '%(refname:short)\t%(committerdate:iso8601)\t%(authorname)'
        out = self._run(['for-each-ref', f'--format={fmt}', 'refs/heads'])
        for line in out.splitlines():
            if not line.strip():
                continue
            parts = line.split('\t')
            name = parts[0]
            if name.endswith('/HEAD'):
                continue
            dt = parse_date(parts[1] if len(parts) > 1 else '')
            author = parts[2] if len(parts) > 2 else ''
            ahead, behind = self.ahead_behind(base, name)
            branches.append(Branch(name=name, remote=False, last_commit_date=dt,
                                 author=author, merged=name in merged_set,
                                 ahead=ahead, behind=behind))
        if include_remote:
            try:
                out = self._run(['for-each-ref', f'--format={fmt}', 'refs/remotes'])
            except GitError:
                out = ''
            for line in out.splitlines():
                if not line.strip():
                    continue
                parts = line.split('\t')
                name = parts[0]
                if name.endswith('/HEAD'):
                    continue
                dt = parse_date(parts[1] if len(parts) > 1 else '')
                author = parts[2] if len(parts) > 2 else ''
                branches.append(Branch(name=name, remote=True, last_commit_date=dt,
                                     author=author, merged=name in merged_set,
                                     ahead=0, behind=0))
        return branches

    def delete_branch(self, name, remote=False, force=False):
        if remote:
            remote_name, br = name.split('/', 1)
            self._run(['push', remote_name, '--delete', br])
        else:
            flag = '-D' if force else '-d'
            self._run(['branch', flag, name])
