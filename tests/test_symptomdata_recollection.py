# SPDX-License-Identifier: Apache-2.0
"""Exercise archive replacement using real filesystem and ZIP readback."""
import io
from pathlib import Path
from zipfile import ZipFile

import pytest

from ricxappframe.xapp_symptomdata import Symptomdata


@pytest.mark.parametrize("template", ["symptoms.zip", "symptoms-%Y-%m-%d-%H-%M-%S.zip"])
def test_collect_same_archive_name_twice(tmp_path, monkeypatch, template):
    source = tmp_path / "inputs"
    source.mkdir()
    log = source / "xapp.log"
    log.write_text("first collection")
    output = tmp_path / "archives"
    output.mkdir()
    collector = Symptomdata(path=str(output) + "/")
    # The baseline's optional-timer bug is independent of archive replacement.
    collector.subscribetimer = None
    monkeypatch.setattr("ricxappframe.xapp_symptomdata.time.time", lambda: 1700000000)
    first = collector.collect(template, (str(source) + r"/.*\.log",), 0, 0)
    assert first is not None and Path(first).is_file()
    log.write_text("second collection")
    second = collector.collect(template, (str(source) + r"/.*\.log",), 0, 0)
    assert second == first
    assert Path(second).is_file()
    name, length, data = collector.read()
    assert name == second and length == len(data)
    with ZipFile(io.BytesIO(data)) as archive:
        assert archive.testzip() is None
        assert archive.read(archive.namelist()[0]) == b"second collection"
    collector.remove()
    assert not Path(second).exists()
