"""Run the actual deployment shell gate locally, never deployment actions."""
from pathlib import Path
import re
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/deploy-analyst-demo-pages.yml'


def gate():
    text = WORKFLOW.read_text()
    block = text.split('        run: |\n', 1)[1].split('      - name:', 1)[0]
    return '\n'.join(line[10:] for line in block.splitlines())


def test_workflow_contract():
    text = WORKFLOW.read_text()
    assert text.split('on:\n', 1)[1].split('\n\n', 1)[0] == '  workflow_dispatch:'
    assert text.split('permissions:\n', 1)[1].split('\n\n', 1)[0] == '  contents: read\n  pages: write\n  id-token: write'
    assert "if: github.ref == 'refs/heads/main' && github.event_name == 'workflow_dispatch'" in text
    assert '  group: pages\n  cancel-in-progress: false' in text
    assert '      name: github-pages\n      url: ${{ steps.deployment.outputs.page_url }}' in text
    assert '          path: docs/demo\n' in text
    assert '          persist-credentials: false' in text
    assert '          enablement: false' in text
    actions = re.findall(r'uses: (\S+)@([0-9a-f]{40})', text)
    assert [a[0] for a in actions] == ['actions/checkout', 'actions/configure-pages', 'actions/upload-pages-artifact', 'actions/deploy-pages']
    assert text.count('        run: |') == 1
    assert not any(x in gate() for x in ['export_site(', 'pip install', 'execute-response', 'data/skillcorner', 'run_match_reorganization_demo'])


def test_actual_gate_accepts_reviewed_package():
    result = subprocess.run(['bash', '-c', gate()], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'exactly 11' in result.stdout


@pytest.fixture
def checkout(tmp_path):
    shutil.copytree(ROOT / 'docs/demo', tmp_path / 'docs/demo')
    (tmp_path / 'docs/protocols').mkdir()
    shutil.copy2(ROOT / 'docs/protocols/p1_demo_public_asset_allowlist_v1.md', tmp_path / 'docs/protocols')
    (tmp_path / 'src').mkdir()
    shutil.copy2(ROOT / 'src/export_match_reorganization_demo_site.py', tmp_path / 'src')
    return tmp_path


@pytest.mark.parametrize('mutation', ['extra', 'hidden', 'directory', 'symlink', 'missing', 'tamper', 'manifest', 'validator', 'private_path'])
def test_actual_gate_rejects(checkout, mutation):
    root = checkout / 'docs/demo'
    asset = root / 'assets/representative/home_p2_5355.64.png'
    if mutation == 'extra': (root / 'tracking.csv').write_text('not approved')
    elif mutation == 'hidden': (root / '.cache').write_text('not approved')
    elif mutation == 'directory': (root / 'extra').mkdir()
    elif mutation == 'symlink':
        asset.unlink(); asset.symlink_to(root / 'index.html')
    elif mutation == 'missing': asset.unlink()
    elif mutation == 'tamper': asset.write_bytes(b'altered')
    elif mutation == 'manifest': (root / 'manifest.json').write_text('{}')
    elif mutation == 'validator': (checkout / 'src/export_match_reorganization_demo_site.py').write_text('raise RuntimeError("unsafe import")')
    else: (root / 'index.html').write_text('/home/private/file')
    result = subprocess.run(['bash', '-c', gate()], cwd=checkout, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'unsafe import' not in result.stderr
