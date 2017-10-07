import unittest
from cogitare.utils import StopTraining
import pytest
import mock
from cogitare.plugins import EarlyStopping


class TestEarlyStopping(unittest.TestCase):

    def test_create(self):
        EarlyStopping(max_tries=5, path='/tmp/tst')

    def setUp(self):
        model = mock.Mock()
        model.save = mock.MagicMock(return_value=None)
        model.load = mock.MagicMock(return_value=None)

        self.model = model

    def test_save(self):
        e = EarlyStopping(10, '/tmp/test', 'loss', None)
        e.function(self.model, 1, loss=1)

        assert self.model.save.called
        assert not self.model.load.called

        for i in range(2, 11):
            e.function(self.model, i, loss=i)

        self.assertEqual(self.model.save.call_count, 1)
        self.assertEqual(self.model.load.call_count, 0)

        e.function(self.model, 11, loss=0.5)

        for i in range(11, 22):
            e.function(self.model, i, loss=i)

        self.assertEqual(self.model.save.call_count, 2)
        self.assertEqual(self.model.load.call_count, 0)

        with pytest.raises(StopTraining):
            e.function(self.model, 22, loss=1)

        self.assertEqual(self.model.save.call_count, 2)
        self.assertEqual(self.model.load.call_count, 1)

    def test_apply_func(self):
        f = mock.MagicMock(return_value=0.5)
        e = EarlyStopping(10, '/tmp/test', 'metric', f)

        e.function(self.model, 1, metric=3)

        assert f.called
        f.assert_called_with(3)
