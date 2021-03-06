# -*- coding:utf-8 -*-

from walkabout.helpers.configlib import ModuleConfig, ConfigParameters


__author__ = u'Joël Vogt'
import imp
from SimpleXMLRPCServer import SimpleXMLRPCServer
import socket
from multiprocessing.dummy import Process
import os


class ModulesDirectory(object):
    def __init__(self, hostname, port, modules, modules_dir):
        self._do_run = True
        self._server = SimpleXMLRPCServer((hostname, port))  # , allow_none=True)
        try:
            hostname = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            hostname = hostname
        self._connection_config = ModuleConfig(hostname, port)
        self._modules = modules
        self._modules_dir = './' + modules_dir
        self._modules_processes = {}
        self._server.register_instance(self)

    def bind_module(self, modules_process, module_binder_instance, module_ref):
        module = imp.load_source(module_ref['name'], os.path.join(self._modules_dir, module_ref['file']))
        for x in module.networked_function.functions_registry:
            module_binder_instance(*x)
        module.networked_function.functions_registry = []
        module_binder_process = Process(target=module_binder_instance.run, name=module_ref['name'])
        modules_process[module_ref['name']] = dict(module_process=module_binder_process,
                                                   module_instance=module_binder_instance,
                                                   last_modified=os.path.getmtime(
                                                       os.path.join(self._modules_dir,
                                                                    self._modules[module_ref['name']]['file'])))
        module_binder_process.start()

    def import_module(self, module_name, client_id, config):
        config = ConfigParameters(**config)
        if client_id not in self._modules_processes:
            self._modules_processes[client_id] = {}

        if module_name not in self._modules:
            raise ImportError('Cannot find %s' % module_name)
        if module_name not in self._modules_processes[client_id]:
            module_binder_instance = self._connection_config.server_factory(config[module_name])
            self.bind_module(self._modules_processes[client_id], module_binder_instance, self._modules[module_name])
        elif os.path.getmtime(
                os.path.join(self._modules_dir, self._modules[module_name]['file'])) > \
                self._modules_processes[client_id][module_name]['last_modified']:
            self._modules_processes[client_id][module_name]['module_process'].terminate()
            self._modules_processes[client_id][module_name]['module_process'].join()
            del self._modules_processes[client_id][module_name]
            module_binder_instance = self._connection_config.server_factory(config[module_name])
            self.bind_module(self._modules_processes[client_id], module_binder_instance, self._modules[module_name])
        return self._connection_config.client_configuration(
            self._modules_processes[client_id][module_name]['module_instance'])

    def on_start(self):
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            self._do_run = False
