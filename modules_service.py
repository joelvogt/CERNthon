#-*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
from rmodule.server import Socket_Module_Binder



import imp

from SimpleXMLRPCServer import SimpleXMLRPCServer
import socket
import pprint
import multiprocessing
import rmodule.client
import os


def networked_function(buffered=False):
    def wrapper(func):
        networked_function.functions_registry.append((func, buffered))
        return func
    return wrapper

networked_function.functions_registry = []

MODULES_BINDER_REGISTRY = [
    # XMLRPC_Node,
    Socket_Module_Binder,
    Socket_Module_Binder,
    Socket_Module_Binder
]


class Modules_Directory_Service(object):

    def __init__(self, hostname='localhost', port=9000, modules={}):
        self._next_port = port
        self._do_run = True
        self._modules = modules
        self._server = SimpleXMLRPCServer((hostname, port), allow_none=True)
        self._modules_processes = map(lambda x:{}, rmodule.client.CLIENTS)
        try:
            self._hostname = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            self._hostname = hostname
        self._server.register_instance(self)


    def import_module(self, module_name, client=0):
        def bind_module(modules_processes, module_binder_instance, module_ref):
            module = imp.load_source(module_ref['name'], module_ref['file'])
            map(lambda x: module_binder_instance(*x), module.networked_function.functions_registry)
            module.networked_function.functions_registry = []
            map(lambda x: module_binder_instance(*x), module.networked_function.functions_registry)
            module.networked_function.functions_registry = []
            module_binder_process = multiprocessing.Process(target=module_binder_instance.run, name=module_name)
            modules_processes[client][module_name] = [module_binder_process, module_binder_instance.connection_information(), os.path.getmtime(self._modules[module_name]['file'])]
            module_binder_process.start()

        if module_name not in self._modules:
            raise ImportError('Cannot find %s ' % module_name)
        if module_name not in self._modules_processes[client]:
            self._next_port += 1
            module_binder_instance = MODULES_BINDER_REGISTRY[client](self._hostname, self._next_port)
            bind_module(self._modules_processes, module_binder_instance, self._modules[module_name])
        elif os.path.getmtime(self._modules[module_name]['file']) > self._modules_processes[client][module_name][2]:
            hostname, port = self._modules_processes[client][module_name][1][:2]
            self._modules_processes[client][module_name][0].terminate()
            self._modules_processes[client][module_name][0].join()
            del self._modules_processes[client][module_name]
            module_binder_instance = MODULES_BINDER_REGISTRY[client](hostname, port)
            bind_module(self._modules_processes, module_binder_instance, self._modules[module_name])
        return self._modules_processes[client][module_name][1]

    def onStart(self):
        pprint.pprint('Modules Directory Service {0}:{1}'.format(self._hostname, self._next_port))
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            self._do_run = False