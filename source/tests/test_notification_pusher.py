import unittest
import mock
from mock import patch, Mock, MagicMock
import notification_pusher

class NotificationPusherTestCase(unittest.TestCase):

    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                notification_pusher.create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))


    def test_writefile_exception(self):
        pid = 24
        patch('os.getpid', Mock(return_value=pid))
        with patch('notification_pusher.open', Mock(side_effect=IOError("Can't write to a file")), create=True) as m_open:
            with self.assertRaises(IOError):
                 notification_pusher.create_pidfile('file/path')
        assert m_open.write.not_called


    def test_wrong_config_filepath(self):
        with self.assertRaises(IOError): notification_pusher.load_config_from_pyfile('wrong/path')
    
    
    def test_parent_daemonize_successful(self):
        pid = 24
        with patch('os.fork', Mock(return_value=pid)):
            with patch('os._exit', Mock()) as mock_os_exit:
                notification_pusher.daemonize()
            mock_os_exit.assert_called_once_with(0)


    def test_parent_daemonize_exception(self):
        with patch('os.fork', Mock(side_effect=OSError("OSError exception"))):
            self.assertRaises(Exception, notification_pusher.daemonize)


    def test_daemonize_child_successful(self):
        pid = 24
        with patch('os.fork', Mock(return_value=0)):
            with patch('os._exit', Mock(side_effect=None)) as mock_os_exit:
                with patch('os.setsid', Mock()):
                     with patch('os.fork', Mock(return_value=pid)):
                         notification_pusher.daemonize()
                mock_os_exit.assert_called_once(0)


    def test_daemonize_child_exception(self):
        with patch('os.fork', Mock(return_value=0)):
            with patch('os._exit', Mock()):
                with patch('os.setsid', Mock()):
                    with patch('os.fork', Mock(side_effect=OSError("OSError exception"))):
                        self.assertRaises(Exception,notification_pusher.daemonize)


    def test_parentpid_equal_null(self):
        pid = 0
        with patch('os.fork', Mock(return_value=pid)):
            with patch('os._exit', Mock()) as mock_os_exit:
                with patch('os.setsid', Mock()):
                    notification_pusher.daemonize()
                    assert mock_os_exit.not_called


    def test_parentpid_null_exception(self):
        with patch('os.fork', Mock(return_value=0)):
            with patch('os._exit', Mock(side_effect=None)):
                with patch('os.setsid', Mock(side_effect=OSError("OSError exception"))):
                    self.assertRaises(Exception,notification_pusher.daemonize)



    def test_parse_cmd_args_exist(self):
        app_description = "this is description"
        parameters = ['-d', '--config', '-P', app_description]
        parser = Mock()
        with patch('notification_pusher.argparse.ArgumentParser', Mock(return_value=parser)):
            notification_pusher.parse_cmd_args(parameters)
            parser.parse_args.assert_called_once_with(args=parameters)


    def test_load_configfile_success(self):
        import os
        variables = {
            'QUEUE_PORT': '33013',
            'QUEUE_SPACE': '0'
        }
        with patch('notification_pusher.exec_pyfile', Mock(return_value=variables)):
            var = notification_pusher.load_config_from_pyfile(os.path.realpath(os.path.expanduser("source/tests/test_config_ok")))

        real_config = notification_pusher.Config()
        real_config.QUEUE_PORT = variables['QUEUE_PORT']
        real_config.QUEUE_SPACE = variables['QUEUE_SPACE']
        self.assertEqual(var.QUEUE_PORT, real_config.QUEUE_PORT)
        self.assertEqual(var.QUEUE_SPACE, real_config.QUEUE_SPACE)


    def test_load_configfile_fail(self):
        import  os
        variables = {
            'QUEUE_PORT': '',
            'Wrong_attribute': '0'
        }
        with patch('notification_pusher.exec_pyfile', Mock(return_value=variables)):
            returns = notification_pusher.load_config_from_pyfile(os.path.realpath(os.path.expanduser('source/tests/test_config_bad')))
        with self.assertRaises(AttributeError):
            getattr(returns, 'Wrong_attribute')


    def test_notification_worker_success(self):
        task = Mock()
        task_queue = MagicMock()
        data = {
            "callback_url": "someurl.com",
            "id": 1
        }
        task.data = data
        task.task_id = 1
        task_ack = 'ack'
        with patch('requests.post', Mock(return_value=MagicMock(name = "response"))):
            notification_pusher.notification_worker(task,task_queue)
        task_queue.put.assert_called_once_with((task, task_ack))


    def test_notification_worker_fail(self):
        from requests import RequestException
        task_queue = MagicMock()
        task = Mock()
        data = {
            "callback_url": "someurl.com",
            "id": 1
        }
        task.data = data
        task.task_id = 1
        bury = 'bury'
        with patch('requests.post', Mock(side_effect=RequestException("Request error"))):
             notification_pusher.notification_worker(task, task_queue)
        task_queue.put.assert_called_once_with((task, bury))


    def test_stop_handler_exit_code_ok(self):
        signum = 123
        exit_code = notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum
        notification_pusher.stop_handler(signum)
        self.assertEqual(exit_code, notification_pusher.exit_code)


    def test_stop_handler_ok(self):
        signum = 123
        notification_pusher.stop_handler(signum)
        self.assertEqual(False, notification_pusher.run_application)






