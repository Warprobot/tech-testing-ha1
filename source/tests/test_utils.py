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
            self.assertRaises(Exception, utils.daemonize())


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
            with patch('os._exit', Mock(side_effect=None)):
                with patch('os.setsid', Mock()):
                    with patch('os.fork'), Mock(side_effect=OSError("OSError exception")):
                        self.assertRaises(Exception,utils.daemonize())


    def test_parentpid_equal_null(self):
        pid = 0
        with patch('os.fork', Mock(return_value=pid)):
            with patch('os._exit', Mock(side_effect=None)) as mock_os_exit:
                with patch('os.setsid', Mock()):
                    utils.daemonize()
                    mock_os_exit.assert_called_once_with(0)


    def test_parentpid_null_exception(self):
        with patch('os.fork', Mock(return_value=0)):
            with patch('os._exit', Mock(side_effect=None)):
                with patch('os.setsid', Mock(side_effect=OSError("OSError exception"))):
                    self.assertRaises(Exception,utils.daemonize())


    def test_parentpid_not_null(self):
        with patch('os.fork', Mock(side_effect=[0,1])):
                with patch('os._exit', Mock()) as mock_os_exit:
                    utils.daemonize()
                    mock_os_exit.assert_called_once(0)


    def test_create_pidfile(self):
        pid = 24
        m_open = mock.mock_open()
        with patch('utils.open', m_open, create=True):
            with patch('os.getpid', Mock(return_value=pid)):
                utils.create_pidfile('/file/path')
        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))


    def test_openfile_exception(self):
        with patch('utils.open', Mock(side_effect=IOError("IOError exception")), create=True):
            self.assertRaises(IOError, utils.create_pidfile('file/path'))


    def test_writefile_exception(self):
        m_open = mock.mock_open()
        with patch('utils.open', Mock(side_effect=IOError("Can't write to a file")), create=True):
            self.assertRaises(IOError, utils.create_pidfile('file/path'))
        assert m_open.write.not_called


    def test_wrong_config_filepath(self):
        self.assertRaises(IOError, utils.load_config_from_pyfile('wrong path'))


    def test_load_configfile_success(self):
        variables = {
            'key1': 'value1',
            'key2': 'value2',
        }
        with patch('exec_pyfile', Mock(return_value=variables)):
            var = utils.load_config_from_pyfile('file/path')

        real_config = utils.Config()
        real_config.key1 = variables['key1']
        real_config.key2 = variables['key2']

        self.assertEqual(var.key1, real_config.key1)
        self.assertEqual(var.key2, real_config.key2)


    def test_load_configfile_fail(self):
        variables = {
            'key': 'error',
        }
        with patch('exec_pyfile', Mock(return_value=variables)):
            returns = utils.load_config_from_pyfile('file/path')
        self.assertRaises(AttributeError, getattr(returns, 'key'))


    def test_parse_cmd_args_exist(self):
        app_description = "this is description"
        parameters = ['-d', '--config', '-P', app_description]
        parser = Mock()
        with patch('utils.argparse.ArgumentParser', Mock(return_value=parser)):
            utils.parse_cmd_args(parameters)
            parser.pars_args.assert_called_once_with(parameters)


    def test_get_tube(self):
        name = 'name'
        port = 80
        host = 'somehost'
        space = 'somespace'
        queue = mock.MagicMock()

        with patch('tarantool_queue.Queue', Mock(return_value=queue.tube(name))):
            utils.get_tube(host, port, space, name)
        queue.asser_called_once_with(host, port, space, name)


    @patch('multiprocessing.Process', Mock())
    def test_spawn_workers(self, mock_process):
        args = []
        num = 10
        utils.spawn_workers(num, "sometarget", args, 42)
        assert  mock_process.call_count == num


    @patch('multiprocessing.Process', Mock())
    def test_spawn_workers_fail(self, mock_process):
        args = []
        num = 0
        utils.spawn_workers(num, "sometarget", args, 42)
        assert  mock_process.called == False


    def test_network_status_ok(self):
        check_url = Mock()
        timeout=Mock()
        with patch('urllib2.urlopen', Mock(return_value=True)) as urllib:
            utils.check_network_status(check_url, timeout)
            urllib.assert_call_once_with(check_url, timeout)


    def test_network_status_fail(self):
        from urllib2 import URLError
        check_url = Mock()
        timeout=Mock()
        with patch('urllib2.urlopen', Mock(side_effect=URLError("UrlError Exception"))):
            self.assertRaises(URLError, utils.check_network_status(check_url, timeout))
















