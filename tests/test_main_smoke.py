"""Smoke test: running main() writes a markdown file to output/."""

from datetime import date
from pathlib import Path

from src import main as main_module
from src.post_generator import output_filename


def test_main_writes_dated_markdown_file():
    out_path = main_module.main(argv=[])
    assert out_path.exists()
    assert out_path.name == output_filename(date.today())
    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("# DrZeroTrust Market Signal Watch")
    assert "Not investment advice" in content


def test_state_file_recorded():
    main_module.main(argv=[])
    state_file = Path(main_module.STATE_DIR) / "state.json"
    assert state_file.exists()
