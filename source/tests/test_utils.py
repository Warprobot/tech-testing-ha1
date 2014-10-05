from lib import utils
import unittest
import mock
from mock import patch, Mock

class UtilsTestCase(unittest.TestCase):

    def test_parent_daemonize_successful(self):
        pid = 24
        with patch('os.fork', Mock(return_value=pid)):
            with patch('os._exit', Mock()) as mock_os_exit:
                utils.daemonize()
            mock_os_exit.assert_called_once_with(0)


    def test_parent_daemonize_exception(self):
        with patch('os.fork', Mock(side_effect=OSError("OSError exception"))):
            self.assertRaises(Exception, utils.daemonize)


    def test_daemonize_child_successful(self):
        pid = 24
        with patch('os.fork', Mock(return_value=0)):
            with patch('os._exit', Mock(side_effect=None)) as mock_os_exit:
                with patch('os.setsid', Mock()):
                     with patch('os.fork', Mock(return_value=pid)):
                         utils.daemonize()
                mock_os_exit.assert_called_once(0)


    def test_daemonize_child_exception(self):
        with patch('os.fork', Mock(return_value=0)):
            with patch('os._exit', Mock()):
                with patch('os.setsid', Mock()):
                    with patch('os.fork', Mock(side_effect=OSError("OSError exception"))):
                        self.assertRaises(Exception,utils.daemonize)


    def test_parentpid_equal_null(self):
        pid = 0
        with patch('os.fork', Mock(return_value=pid)):
            with patch('os._exit', Mock()) as mock_os_exit:
                with patch('os.setsid', Mock()):
                    utils.daemonize()
                    assert mock_os_exit.not_called


    def test_parentpid_null_exception(self):
        with patch('os.fork', Mock(return_value=0)):
            with patch('os._exit', Mock(side_effect=None)):
                with patch('os.setsid', Mock(side_effect=OSError("OSError exception"))):
                    self.assertRaises(Exception,utils.daemonize)


    def test_parentpid_not_null(self):
        with patch('os.fork', Mock(side_effect=[0,1])):
                with patch('os._exit', Mock()) as mock_os_exit:
                    utils.daemonize()
                    mock_os_exit.assert_called_once(0)


    def test_create_pidfile(self):
        pid = 24
        m_open = mock.mock_open()
        with patch('lib.utils.open', m_open, create=True):
            with patch('os.getpid', Mock(return_value=pid)):
                utils.create_pidfile('/file/path')
        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))


    def test_writefile_exception(self):
        pid = 24
        patch('os.getpid', Mock(return_value=pid))
        with patch('lib.utils.open', Mock(side_effect=IOError("Can't write to a file")), create=True) as m_open:
            with self.assertRaises(IOError):
                 utils.create_pidfile('file/path')
        assert m_open.write.not_called


    def test_wrong_config_filepath(self):
        with self.assertRaises(IOError): utils.load_config_from_pyfile('wrong/path')


    def test_load_configfile_success(self):
        import os
        variables = {
            'QUEUE_PORT': '33013',
            'QUEUE_SPACE': '0'
        }
        with patch('lib.utils.exec_pyfile', Mock(return_value=variables)):
            var = utils.load_config_from_pyfile(os.path.realpath(os.path.expanduser("source/tests/test_config_ok")))

        real_config = utils.Config()
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
        with patch('lib.utils.exec_pyfile', Mock(return_value=variables)):
            returns = utils.load_config_from_pyfile(os.path.realpath(os.path.expanduser('source/tests/test_config_bad')))
        with self.assertRaises(AttributeError):
            getattr(returns, 'Wrong_attribute')


    def test_parse_cmd_args_exist(self):
        app_description = "this is description"
        parameters = ['-d', '--config', '-P', app_description]
        parser = Mock()
        with patch('lib.utils.argparse.ArgumentParser', Mock(return_value=parser)):
            utils.parse_cmd_args(parameters)
            parser.parse_args.assert_called_once_with(args=parameters)


    def test_get_tube(self):
        name = 'name'
        port = 80
        host = 'somehost'
        space = 123
        queue = mock.MagicMock()

        with patch('tarantool_queue.Queue', Mock(return_value=queue.tube(name))):
            utils.get_tube(host, port, space, name)
        queue.asser_called_once_with(host, port, space, name)


    def test_spawn_workers(self):
        args = []
        num = 10
        with patch('lib.utils.Process', Mock()) as mock_process:
            utils.spawn_workers(num, "target", args, num)
            self.assertTrue(mock_process.called)
            self.assertEqual(mock_process.call_count, num)


    def test_spawn_workers_fail(self):
        args = []
        num = 0
        with patch('lib.utils.Process', Mock()) as mock_process:
            utils.spawn_workers(num, "target", args, num)
            self.assertFalse(mock_process.called)


    def test_network_status_ok(self):
        check_url = Mock()
        timeout = 0
        with patch('urllib2.urlopen', Mock(return_value=True)) as urllib:
            utils.check_network_status(check_url, timeout)
            urllib.assert_call_once_with(check_url, timeout)


    def test_network_status_fail(self):
        check_url = Mock()
        timeout = 123
        with patch('urllib2.urlopen', Mock(side_effect=ValueError("network status fail"))):
            self.assertFalse(utils.check_network_status(check_url, timeout))





