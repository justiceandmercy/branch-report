import subprocess
from branch_report.cli import main


def init_repo(tmp_path):
    subprocess.run(['git', 'init', '-b', 'main', str(tmp_path)], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(tmp_path), 'config', 'user.email', 't@t.com'], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'config', 'user.name', 't'], check=True)
    (tmp_path / 'f.txt').write_text('hi')
    subprocess.run(['git', '-C', str(tmp_path), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'commit', '-m', 'init'], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(tmp_path), 'branch', 'feature/old'], check=True)
    return tmp_path


def test_list_runs(tmp_path, capsys):
    repo = init_repo(tmp_path)
    rc = main(['list', '--repo', str(repo), '--format', 'json'])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'main' in out


def test_config_init(tmp_path, capsys):
    rc = main(['config', 'init', '--path', str(tmp_path / '.branchreportrc.json')])
    assert rc == 0
    assert (tmp_path / '.branchreportrc.json').is_file()
