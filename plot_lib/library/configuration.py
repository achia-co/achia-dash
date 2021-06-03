import pathlib
import os
import yaml

class InvalidYAMLConfigException(Exception):
    pass

def _get_config():
    directory = pathlib.Path().resolve()
    file_name = 'achia.yaml'
    file_path = os.path.join(directory, file_name)
    file_path = file_name
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Unable to find the config.yaml file. Expected location: {file_path}")
    f = open(file_path, 'r')
    config = yaml.load(stream=f, Loader=yaml.Loader)
    f.close()
    return config


def _get_log_settings(config):
    if 'log_folder_path' not in config:
        raise InvalidYAMLConfigException('Failed to find the log_folder_path parameter in the YAML.')
    return config.get('log_folder_path', 'log_folder_path')

def _get_monitored_drives_settings(config):
    if 'monitored_drives' not in config:
        # raise InvalidYAMLConfigException('Failed to find monitored_drives parameter in the YAML.')
        return config.get('monitored_drives', 'log_folder_path')


def _check_parameters(parameter, expected_parameters, parameter_type):
    failed_checks = []
    checks = expected_parameters
    for check in checks:
        if check in parameter:
            continue
        failed_checks.append(check)
    if failed_checks:
        raise InvalidYAMLConfigException(f'Failed to find the following {parameter_type} parameters: '
                                         f'{", ".join(failed_checks)}')


def get_config_info():
    config = _get_config()
    log_directory = _get_log_settings(config=config)
    monitored_drives = _get_monitored_drives_settings(config=config)
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    return log_directory, monitored_drives

