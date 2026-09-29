import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from analyst_review_index import COMPACT_COLUMNS
from run_match_reorganization_demo import run_demo


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        self.paths.extend(value for key, value in attrs if key in {"href", "src"} and not value.startswith("#"))


@pytest.mark.parametrize("media", [False, True])
def test_portable_review_navigation_and_roles(tmp_path, media, monkeypatch):
    if media:
        import selected_window_demo as bounded
        monkeypatch.setattr(bounded, 'recover', lambda *a: {'cache': {'top_three_contributions_m':[3.,2.,1.]}})
        def render(row, detail, destination):
            files = [destination / f'{row.peak_time_s}.{ext}' for ext in ('png','gif')]
            for path in files:
                path.write_bytes(b'synthetic media')
            return files
        monkeypatch.setattr(bounded, 'render_detail', render)
    data = tmp_path / 'data'
    (data / 'metrica_sample_game_2').mkdir(parents=True)
    output = tmp_path / "review"
    run_demo(output, render_media=media, data_root=data)
    html = (output / "analyst_review_index.html").read_text()
    links = Links(); links.feed(html)
    assert all(not Path(path).is_absolute() and (output / path).is_file() for path in links.paths)
    assert "/Users/" not in html and str(tmp_path) not in html
    for section in ('id="representative"', 'id="diagnostic"', 'id="rejected"'):
        assert section in html
    assert "REJECTED — trajectory integrity failure" in html
    assert "Impossible native-frame movement detected" in html
    assert "goalkeeper-distribution special context" in html
    compact = pd.read_csv(output / "compact_episode_review.csv", keep_default_na=False)
    assert tuple(compact.columns) == COMPACT_COLUMNS
    assert len(compact) == 5
    assert not compact.eq("").any().any()
    if not media:
        assert "not_evaluated — absent from closed summary" in compact["Top defender contributors"].tolist()
    else:
        assert compact['Top defender contributors'].str.contains('#3: 1.00 m').all()
    reps = pd.read_csv(output / "representative_examples.csv")
    assert reps.peak_time_s.tolist() == [5355.64, 336.76]
    assert reps.ball_alignment_support_status.eq("supported").all()
    assert reps.media_status.eq("supported" if media else "not_rendered").all()
    if media:
        assert all((output / p).is_file() for p in reps.gif_path)
    rejected = pd.read_csv(output / "rejected_examples.csv")
    assert rejected.peak_time_s.tolist() == [1734.72]
    assert rejected.media_status.eq("integrity_failed" if media else "not_rendered").all()
    if not media:
        assert list((output / "rejected_examples").iterdir()) == []
    assert len(pd.read_csv(output / "detailed_episode_table.csv")) == 5


def test_double_data_free_package_is_byte_identical(tmp_path):
    left, right = tmp_path / "left", tmp_path / "right"
    run_demo(left); run_demo(right)
    a = {str(p.relative_to(left)): p.read_bytes() for p in left.rglob("*") if p.is_file()}
    b = {str(p.relative_to(right)): p.read_bytes() for p in right.rglob("*") if p.is_file()}
    assert a == b
    manifest = json.loads((left / "manifest.json").read_text())
    import hashlib
    assert all(hashlib.sha256((left / p).read_bytes()).hexdigest() == h for p,h in manifest["files_sha256"].items())


def test_cli_completion_and_collision(tmp_path):
    data = tmp_path / "data"
    for game in (1, 2):
        (data / f"metrica_sample_game_{game}").mkdir(parents=True)
    command = [sys.executable, str(ROOT / "src/run_match_reorganization_demo.py"),
               "--data-root", str(data), "--output-dir", str(tmp_path / "out"), "--no-media"]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "Review complete." in result.stdout and "analyst_review_index.html" in result.stdout
    assert "Representative: 2" in result.stdout and "Rejected: 1" in result.stdout
    assert subprocess.run(command, capture_output=True).returncode != 0
