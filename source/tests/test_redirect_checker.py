import unittest
import mock
from source.lib.utils import Config
from source import redirect_checker

class TestChildren:
    child = mock.Mock()

    def __init__(self, length):
        self.children = [self.child] * length

    def __len__(self):
        return len(self.children)

    def __call__(self):
        return self.children

    def __iter__(self):
        return iter(self.children)


def stop_loop(self):
            redirect_checker.run_checker = False


class RedirectCheckerTestCase(unittest.TestCase):
    def test_main_loop_dfs(self):
        """
        try to go deeper
        """
        pid = 42
        config = Config()
        config.SLEEP = 1
        config.CHECK_URL = 'url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 50
        mock_spawn_workers = mock.Mock()
        mock_check_network_status = mock.Mock(return_value=True)

        children = TestChildren(1)
        count = config.WORKER_POOL_SIZE - len(children())
        mock_sleep = mock.Mock(side_effect=stop_loop)
        with mock.patch('source.redirect_checker.check_network_status', mock_check_network_status),\
             mock.patch('os.getpid', mock.Mock(return_value=pid)),\
             mock.patch('source.redirect_checker.spawn_workers', mock_spawn_workers),\
             mock.patch('source.redirect_checker.active_children', children),\
             mock.patch('source.redirect_checker.sleep', mock_sleep):
                            redirect_checker.main_loop(config)
        assert mock_spawn_workers.call_args[1]['num'] == count
        assert mock_spawn_workers.call_args[1]['parent_pid'] == pid
        redirect_checker.run_checker = True

    def test_main_loop_no_workers(self):
        pid = 42
        config = Config()
        config.SLEEP = 8
        config.CHECK_URL = 'url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 2
        active_children = TestChildren(2)
        mock_spawn_workers = mock.Mock()
        mock_check_network_status = mock.Mock(return_value=True)
        mock_sleep = mock.Mock(side_effect=stop_loop)
        with mock.patch('source.redirect_checker.check_network_status', mock_check_network_status),\
             mock.patch('os.getpid', mock.Mock(return_value=pid)),\
             mock.patch('source.redirect_checker.active_children', active_children),\
             mock.patch('source.redirect_checker.spawn_workers', mock_spawn_workers),\
             mock.patch('source.redirect_checker.sleep', mock_sleep):
            redirect_checker.main_loop(config)
            self.assertEqual(mock_spawn_workers.call_count, 0)
            mock_sleep.assert_called_once_with(config.SLEEP)
            redirect_checker.run_checker = True

    def test_main_loop_network_status_is_not_fine(self):
        pid = 42
        config = Config()
        config.SLEEP = 8
        config.CHECK_URL = 'url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 2
        mock_spawn_workers = mock.Mock()
        mock_check_network_status = mock.Mock(return_value=False)
        test_active_children = mock.Mock()
        mock_sleep = mock.Mock(side_effect=stop_loop)
        with mock.patch('source.redirect_checker.check_network_status', mock_check_network_status),\
             mock.patch('os.getpid', mock.Mock(return_value=pid)),\
             mock.patch('source.redirect_checker.active_children', mock.Mock(return_value=[test_active_children])),\
             mock.patch('source.redirect_checker.sleep', mock_sleep):
            redirect_checker.main_loop(config)
            self.assertEqual(mock_spawn_workers.call_count, 0)
            test_active_children.terminate.assert_called_once()
            mock_sleep.assert_called_once_with(config.SLEEP)
            redirect_checker.run_checker = True

    def test_main_daemon_pidfile(self):
        """
        DFS ;-)
        """
        args = mock.MagicMock()
        config = Config()
        config.LOGGING = mock.Mock()
        config.EXIT_CODE = 0
        with mock.patch('source.redirect_checker.daemonize', mock.Mock()) as daemonize:
            with mock.patch('source.redirect_checker.parse_cmd_args', mock.Mock()):
                with mock.patch('source.redirect_checker.dictConfig', mock.Mock()):
                    with mock.patch('source.redirect_checker.main_loop', mock.Mock()):
                        with mock.patch('source.redirect_checker.load_config_from_pyfile',
                                        mock.Mock(return_value=config)):
                            with mock.patch('source.redirect_checker.os.path.realpath',
                                        mock.Mock()):
                                with mock.patch('source.redirect_checker.os.path.expanduser',
                                        mock.Mock()):
                                    with mock.patch('source.redirect_checker.create_pidfile', mock.Mock()) as create_pid:
                                        daemonize.assert_called()
                                        create_pid.assert_called()
                                        self.assertEqual(config.EXIT_CODE, redirect_checker.main(args))

    def test_main_no_daemon_no_pidfile(self):
        """
        main without deamon or pidfile
        """
        args = mock.MagicMock()
        args.daemon = False
        args.pidfile = False
        config = Config()
        config.LOGGING = mock.Mock()
        config.EXIT_CODE = 0
        with mock.patch('source.redirect_checker.parse_cmd_args', mock.MagicMock(return_value=args)):
            with mock.patch('source.redirect_checker.daemonize', mock.Mock()) as daemonize:
                with mock.patch('source.redirect_checker.dictConfig', mock.Mock()):
                    with mock.patch('source.redirect_checker.main_loop', mock.Mock()):
                        with mock.patch('source.redirect_checker.load_config_from_pyfile',
                                        mock.Mock(return_value=config)):
                            with mock.patch('source.redirect_checker.os.path.realpath',
                                        mock.Mock()):
                                with mock.patch('source.redirect_checker.os.path.expanduser',
                                        mock.Mock()):
                                    with mock.patch('source.redirect_checker.create_pidfile', mock.Mock()) as create_pid:
                                        self.assertFalse(daemonize.called)
                                        self.assertFalse(create_pid.called)
                                        self.assertEqual(config.EXIT_CODE, redirect_checker.main(args))