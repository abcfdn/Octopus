# -*- encoding: UTF-8 -*-

import os

from server.platforms.google.drive import GoogleDrive
import server.platforms.utils.util as util

from .constants import CONFIG_ROOT_PATH, TASK_CONFIG_ROOT_PATH


class ResourceBase:
    def __init__(self, google_creds, data_config):
        self.drive_service = GoogleDrive(google_creds)
        self.sync_to_local(data_config)

    def sync_to_local(self, data_config):
        for key, resource in data_config.items():
            if 'local' in resource:
                util.create_if_not_exist(resource['local'])
                if 'remote' in resource and key is not 'output':
                    self.drive_service.sync_folder(resource['remote'],
                                                   resource['local'])


class Task(ResourceBase):
    def __init__(self, google_creds):
        self.config = self.load_config()
        super().__init__(google_creds, self.config['data'])

    def load_common_config(self):
        common_config_file = os.path.join(CONFIG_ROOT_PATH, 'common.yaml')
        return util.load_yaml(common_config_file)

    def load_task_common_config(self):
        config_file = os.path.join(
            TASK_CONFIG_ROOT_PATH, self.app_name(), 'common.yaml')
        if os.path.isfile(config_file):
            return util.load_yaml(config_file)
        else:
            return {}

    def load_config(self):
        common_config = util.deepmerge(
            self.load_common_config(), self.load_task_common_config())
        task_config = util.load_yaml(os.path.join(
            TASK_CONFIG_ROOT_PATH,
            self.app_name(),
            '{}.yaml'.format(self.__class__.__name__)))
        return util.deepmerge(task_config, common_config)

    def app_name(self):
        raise('Not Implemented')

    def process(self, args):
        raise("Not Implemented")


class Workflow:
    def __init__(self, tasks):
        self.tasks = tasks

    def run(self, args):
        for task in self.tasks:
            task.process(args)


