import argparse
import sys
import json
from . import __version__
from .config import Config
from .git import GitRunner, GitError
from .analysis import classify, suggest_cleanup
from .output import render
from .plugins import load_plugins, apply_plugins


def build_parser():
    p = argparse.ArgumentParser(prog='branch-report', description='Audit git branches.')
    p.add_argument('--version', action='version', version=__version__)
    sub = p.add_subparsers(dest='cmd', required=True)
    l = sub.add_parser('list', help='List branches')
    l.add_argument('--base')
    l.add_argument('--format', choices=['table', 'json', 'csv'])
    l.add_argument('--repo', default='.')
    l.add_argument('--no-remote', action='store_true')
    s = sub.add_parser('stale', help='Show stale branches')
    s.add_argument('--days', type=int)
    s.add_argument('--base')
    s.add_argument('--format', choices=['table', 'json', 'csv'])
    s.add_argument('--repo', default='.')
    m = sub.add_parser('merged', help='Show merged branches')
    m.add_argument('--base')
    m.add_argument('--format', choices=['table', 'json', 'csv'])
    m.add_argument('--repo', default='.')
    c = sub.add_parser('cleanup', help='Suggest branch deletions')
    c.add_argument('--execute', action='store_true')
    c.add_argument('--force', action='store_true')
    c.add_argument('--base')
    c.add_argument('--repo', default='.')
    ci = sub.add_parser('config', help='Config helpers')
    ci.add_argument('action', choices=['init', 'show'])
    ci.add_argument('--path', default='.branchreportrc.json')
    ci.add_argument('--repo', default='.')
    return p


def load_config(args):
    cfg, _ = Config.load(None)
    if getattr(args, 'base', None):
        cfg.base = args.base
    if getattr(args, 'days', None) is not None:
        cfg.stale_days = args.days
    if getattr(args, 'format', None):
        cfg.format = args.format
    if getattr(args, 'no_remote', False):
        cfg.remote = False
    return cfg


def _base(gr, cfg):
    base = cfg.base
    try:
        gr._run(['rev-parse', '--verify', base])
    except GitError:
        base = gr.default_base()
        cfg.base = base
    return base


def cmd_list(args):
    cfg = load_config(args)
    gr = GitRunner(repo=args.repo)
    if not gr.is_repo():
        print('not a git repository', file=sys.stderr)
        return 2
    base = _base(gr, cfg)
    branches = gr.list_branches(base=base, include_remote=cfg.remote)
    plugins = load_plugins(cfg.plugin_dir)
    labels_map = {}
    for b in branches:
        labels_map[id(b)] = apply_plugins(plugins, b, cfg, classify(b, cfg))
    if not cfg.remote:
        branches = [b for b in branches if not b.remote]
    print(render(branches, cfg, labels_map, cfg.format))
    return 0


def cmd_stale(args):
    cfg = load_config(args)
    gr = GitRunner(repo=args.repo)
    if not gr.is_repo():
        print('not a git repository', file=sys.stderr)
        return 2
    base = _base(gr, cfg)
    branches = gr.list_branches(base=base, include_remote=cfg.remote)
    plugins = load_plugins(cfg.plugin_dir)
    labels_map = {}
    stale_branches = []
    for b in branches:
        labs = apply_plugins(plugins, b, cfg, classify(b, cfg))
        labels_map[id(b)] = labs
        if 'stale' in labs:
            stale_branches.append(b)
    if not cfg.remote:
        stale_branches = [b for b in stale_branches if not b.remote]
    print(render(stale_branches, cfg, labels_map, cfg.format))
    return 0


def cmd_merged(args):
    cfg = load_config(args)
    gr = GitRunner(repo=args.repo)
    if not gr.is_repo():
        print('not a git repository', file=sys.stderr)
        return 2
    base = _base(gr, cfg)
    branches = gr.list_branches(base=base, include_remote=cfg.remote)
    plugins = load_plugins(cfg.plugin_dir)
    labels_map = {}
    merged_branches = []
    for b in branches:
        labs = apply_plugins(plugins, b, cfg, classify(b, cfg))
        labels_map[id(b)] = labs
        if 'merged' in labs:
            merged_branches.append(b)
    if not cfg.remote:
        merged_branches = [b for b in merged_branches if not b.remote]
    print(render(merged_branches, cfg, labels_map, cfg.format))
    return 0


def cmd_cleanup(args):
    cfg = load_config(args)
    gr = GitRunner(repo=args.repo)
    if not gr.is_repo():
        print('not a git repository', file=sys.stderr)
        return 2
    base = _base(gr, cfg)
    branches = gr.list_branches(base=base, include_remote=cfg.remote)
    plugins = load_plugins(cfg.plugin_dir)
    suggestions = suggest_cleanup(branches, cfg)
    filtered = []
    for b, labs in suggestions:
        labs = apply_plugins(plugins, b, cfg, list(labs))
        if 'protected' in labs:
            continue
        if 'merged' in labs or 'stale' in labs:
            filtered.append((b, labs))
    if not filtered:
        print('nothing to clean up')
        return 0
    for b, labs in filtered:
        if b.remote:
            remote_name, br = b.name.split('/', 1)
            cmd = f'git push {remote_name} --delete {br}'
        else:
            flag = '-D' if args.force else '-d'
            cmd = f'git branch {flag} {b.name}'
        print(f'[{",".join(labs)}] {cmd}')
    if args.execute:
        for b, labs in filtered:
            try:
                gr.delete_branch(b.name, remote=b.remote, force=args.force)
                print(f'deleted {b.name}')
            except GitError as e:
                print(f'failed to delete {b.name}: {e}', file=sys.stderr)
    else:
        print('\ndry-run: pass --execute to apply')
    return 0


def cmd_config(args):
    if args.action == 'init':
        cfg = Config.from_dict({})
        cfg.save(args.path)
        print(f'wrote {args.path}')
        return 0
    if args.action == 'show':
        cfg, path = Config.load(None)
        print(f'# source: {path}')
        print(json.dumps(cfg.to_dict(), indent=2))
        return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        'list': cmd_list,
        'stale': cmd_stale,
        'merged': cmd_merged,
        'cleanup': cmd_cleanup,
        'config': cmd_config,
    }
    return dispatch[args.cmd](args)


if __name__ == '__main__':
    raise SystemExit(main())
