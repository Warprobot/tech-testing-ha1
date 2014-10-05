# coding: utf-8
import argparse
from multiprocessing import Process
import os
import socket
import urllib2

from tarantool_queue import tarantool_queue


def daemonize():
    """
    Демонизирует текущий процесс.
    :rtype : object
    """
    try:
        pid = os.fork()
    except OSError as exc:
        raise Exception("%s [%d]" % (exc.strerror, exc.errno))

    if pid == 0:
        os.setsid() #call setsid создает сеанс и устанавливает идентификатор
                    #Возвращает идентификатор сеанса вызывающего процесса.
        try:
            pid = os.fork()
        except OSError as exc:
            raise Exception("%s [%d]" % (exc.strerror, exc.errno))

        if pid > 0:
            os._exit(0)
    else:
        os._exit(0)


def create_pidfile(pidfile_path):
    pid = str(os.getpid())
    with open(pidfile_path, 'w') as f: #with instead try ... finally
        f.write(pid)


def exec_pyfile(filepath):
    variables = {}
    execfile(filepath, variables) #исполняет последовательно команды из файла на диске
    return variables

def load_config_from_pyfile(filepath):
    """
    Создает Config объект из py файла и загружает в него настройки.

    Используются только camel-case переменные.

    :param filepath: путь до py файла с настройками
    :type filepath: basestring

    :rtype: Config
    """
    cfg = Config()
    variables = exec_pyfile(filepath)
    for key, value in variables.iteritems():
        if key.isupper(): #Возвращает 1, если все символы в исходной строке находятся в верхнем регистре (прописные), иначе 0
            setattr(cfg, key, value)

    return cfg


def parse_cmd_args(args, app_description=''):
    """
    Разбирает аргументы командной строки.

    :param args: список аргументов
    :type args: list

    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description=app_description
    )
    parser.add_argument(
        '-c',
        '--config',
        dest='config',
        required=True,
        help='Path to configuration file.'
    )
    parser.add_argument(
        '-d',
        '--daemon',
        dest='daemon',
        action='store_true',
        help='Daemonize process.'
    )
    parser.add_argument(
        '-P',
        '--pid',
        dest='pidfile',
        help='Path to pidfile.'
    )

    return parser.parse_args(args=args)


def get_tube(host, port, space, name):
    queue = tarantool_queue.Queue(
        host=host, port=port, space=space
    )
    return queue.tube(name)


class Config(object):
    """
    Класс для хранения настроек приложения.
    """
    pass


def spawn_workers(num, target, args, parent_pid):
    for _ in xrange(num):
        p = Process(target=target, args=args, kwargs={'parent_pid': parent_pid})
        p.daemon = True
        p.start()


def check_network_status(check_url, timeout):
    try:
        urllib2.urlopen(
            url=check_url,
            timeout=timeout,
        )
        return True
    except (urllib2.URLError, socket.error, ValueError):
        return False
