# SPDX-License-Identifier: Apache-2.0
"""Static registration does not create a timer but must support cleanup."""
from unittest.mock import Mock

import pytest

from ricxappframe.xapp_symptomdata import Symptomdata


@pytest.mark.parametrize("cleanup", ["stop", "__del__"])
def test_static_symptomdata_cleanup(tmp_path, cleanup):
    collector = Symptomdata(path=str(tmp_path) + "/")
    getattr(collector, cleanup)()
    getattr(collector, cleanup)()


def test_dynamic_symptomdata_cleanup_cancels_timer(tmp_path):
    collector = Symptomdata(path=str(tmp_path) + "/")
    timer = Mock()
    collector.subscribetimer = timer
    collector.stop()
    timer.cancel.assert_called_once_with()
    collector.subscribetimer = None
