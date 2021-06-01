import pathlib
import os
import yaml


from plot_lib.library.utilities.exceptions import InvalidYAMLConfigException


def _get_config():
    directory = pathlib.Path().resolve()
    file_name = 'config.yaml'
    file_path = os.path.join(directory, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Unable to find the config.yaml file. Expected location: {file_path}")
    f = open(file_path, 'r')
    config = yaml.load(stream=f, Loader=yaml.Loader)
    f.close()
    return config


def _get_log_settings(config):
    if 'log' not in config:
        raise InvalidYAMLConfigException('Failed to find the log parameter in the YAML.')
    log = config['log']
    expected_parameters = ['folder_path']
    _check_parameters(parameter=log, expected_parameters=expected_parameters, parameter_type='log')
    return log['folder_path']


def _get_jobs(config):
    if 'jobs' not in config:
        raise InvalidYAMLConfigException('Failed to find the jobs parameter in the YAML.')
    return config['jobs']



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
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    jobs = _get_jobs(config=config)

    return log_directory, jobs