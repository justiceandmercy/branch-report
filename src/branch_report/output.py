import csv
import io
import json
from .analysis import Branch


def render(branches, config, labels_map, fmt=None):
    fmt = fmt or config.format
    if fmt == 'json':
        data = []
        for b in branches:
            data.append({
                'name': b.name,
                'remote': b.remote,
                'author': b.author,
                'last_commit': b.last_commit_date.isoformat() if b.last_commit_date else None,
                'merged': b.merged,
                'ahead': b.ahead,
                'behind': b.behind,
                'labels': labels_map.get(id(b), []),
            })
        return json.dumps(data, indent=2)
    if fmt == 'csv':
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['name', 'remote', 'author', 'last_commit', 'merged', 'ahead', 'behind', 'labels'])
        for b in branches:
            w.writerow([b.name, b.remote, b.author,
                        b.last_commit_date.isoformat() if b.last_commit_date else '',
                        b.merged, b.ahead, b.behind, ';'.join(labels_map.get(id(b), []))])
        return buf.getvalue()
    lines = []
    header = f"{'NAME':<40} {'REMOTE':<6} {'LAST COMMIT':<20} {'MERGED':<7} {'LABELS'}"
    lines.append(header)
    lines.append('-' * len(header))
    for b in branches:
        lc = b.last_commit_date.strftime('%Y-%m-%d') if b.last_commit_date else '-'
        labels = ','.join(labels_map.get(id(b), []))
        lines.append(f'{b.name:<40} {str(b.remote):<6} {lc:<20} {str(b.merged):<7} {labels}')
    return '\n'.join(lines)
