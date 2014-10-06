from tarantool import DatabaseError
import unittest
import mock

from source.lib import worker


class WorkerTestCase(unittest.TestCase):
    def test_get_redirect_history_from_task_error_and_no_recheck(self):
        """
        path with 'ERROR' in history_types and not is_recheck
        """
        task = mock.Mock()
        task.data = dict(url='some_url', recheck=False, url_id='url_id', suspicious='suspicious')
        is_input = True
        data_modified = task.data.copy()
        data_modified['recheck'] = True
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=(['ERROR'], [], []))):
            self.assertEquals((is_input, data_modified), (worker.get_redirect_history_from_task(task, 1)))

    def test_get_redirect_history_from_task_error_(self):
        """
        alter path
        """
        task = mock.Mock()
        task.data = dict(url='some_url', recheck=True, url_id='url_id')
        return_value = [['ERROR'], [], []]
        is_input = False
        data_modified = dict(url_id=task.data['url_id'], result=return_value, check_type='normal')
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=return_value)):
            self.assertEquals((is_input, data_modified), worker.get_redirect_history_from_task(task, 1))

    def test_get_redirect_history_from_task_with_suspicious(self):
        """
        with suspicious
        """
        task = mock.Mock()
        task.data = dict(url='some_url', recheck=False, url_id='url_id', suspicious='suspicious')
        return_value = [[], [], []]
        is_input = False
        data_modified = dict(url_id=task.data['url_id'], result=return_value, check_type='normal',
                             suspicious=task.data['suspicious'])
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=return_value)):
            self.assertEquals((is_input, data_modified), worker.get_redirect_history_from_task(task, 1))

    def test_worker_parent_is_dead(self):
        """
        let parent is dead - is_path_exists - false
        """
        config = mock.MagicMock()
        parent_pid = 123
        tube = mock.MagicMock()
        input_tube = mock.MagicMock()
        output_tube = mock.MagicMock()
        is_path_exists = False
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)), \
             mock.patch('os.path.exists', mock.Mock(return_value=is_path_exists)), \
             mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])):
            worker.worker(config, parent_pid)

        self.assertFalse(input_tube.called)

    def test_worker_task_is_none(self):
        """
        task is none
        """
        config = mock.MagicMock()
        parent_pid = 123
        tube = mock.MagicMock()
        input_tube_take = None
        tube.take = mock.Mock(return_value=input_tube_take)
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)),\
             mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock())\
                as get_redirect_history_from_task:
            worker.worker(config, parent_pid)

        self.assertFalse(get_redirect_history_from_task.called)

    def test_worker_result_is_none(self):
        """
        result is None.
        """
        config = mock.MagicMock()
        parent_pid = 123
        tube = mock.MagicMock()
        is_result = None
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)),\
             mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=is_result)),\
             mock.patch('source.lib.worker.logger', mock.Mock()) as logger:
                        worker.worker(config, parent_pid)
        self.assertFalse(logger.debug.called)

    def test_worker_result_is_input(self):
        """
        is_input isnt none
        """
        config = mock.MagicMock()
        parent_pid = 123
        tube = mock.MagicMock()
        input_tube = mock.MagicMock()
        output_tube = mock.MagicMock()
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)),\
             mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])),\
             mock.patch('source.lib.worker.get_redirect_history_from_task',
                        mock.Mock(return_value=['is_input', 'data'])),\
             mock.patch('source.lib.worker.logger', mock.Mock()):
            worker.worker(config, parent_pid)
        self.assertFalse(output_tube.put.called)

    def test_worker_result_not_is_input(self):
        """
        is_input is None
        """
        config = mock.MagicMock()
        parent_pid = 123
        tube = mock.MagicMock()
        input_tube = mock.MagicMock()
        output_tube = mock.MagicMock()
        is_input = None
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)),\
             mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[input_tube, output_tube])),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=[is_input, 'data'])),\
             mock.patch('source.lib.worker.logger', mock.Mock()):
            worker.worker(config, parent_pid)
        self.assertFalse(input_tube.put.called)

    def test_worker_not_result_database_error(self):
        """
        Raise exception
        """

        config = mock.MagicMock()
        parent_pid = 123
        tube = mock.MagicMock()
        task = mock.MagicMock()
        tube.take = mock.Mock(return_value=task)
        task.ack = mock.Mock(side_effect=DatabaseError)
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube)),\
             mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=None)),\
             mock.patch('source.lib.worker.logger', mock.Mock()) as logger:
            worker.worker(config, parent_pid)
        self.assertTrue(logger.exception.called)