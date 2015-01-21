#-*- coding:utf-8 -*-
from rmodule.client import SocketServerProxy, CLIENTS

__author__ = u'Joël Vogt'
import xmlrpclib, sys


def import_module(module_name, directory_service_hostname='127.0.0.1', port=9000):
    modules_directory_service = xmlrpclib.ServerProxy('http://%s:%d' % (directory_service_hostname, port), allow_none=True)
    module_server_hostname, port, buffer_size, methods = \
        modules_directory_service.import_module(
            module_name,
            CLIENTS.index(sys.subversion[0])
        )
    return SocketServerProxy(module_server_hostname, port, buffer_size, **methods)