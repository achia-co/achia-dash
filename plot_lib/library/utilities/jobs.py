import logging
import psutil

from copy import deepcopy

from plot_lib.library.utilities.exceptions import InvalidConfigurationSetting
from plot_lib.library.utilities.processes import identify_drive
from plot_lib.library.utilities.objects import Job





def check_valid_destinations(job, drives_free_space):
    job_size = determine_job_size(job.size)
    drives = list(drives_free_space.keys())
    destination_directories = job.destination_directory
    if not isinstance(destination_directories, list):
        destination_directories = [destination_directories]

    valid_destinations = []
    for directory in destination_directories:
        drive = identify_drive(file_path=directory, drives=drives)
        logging.debug(f'Drive "{drive}" has {drives_free_space[drive]} free space.')
        if drives_free_space[drive] is None or drives_free_space[drive] >= job_size:
            valid_destinations.append(directory)
            continue
        logging.error(f'Drive "{drive}" does not have enough space. This directory will be skipped.')

    if not valid_destinations:
        job.max_plots = 0
        logging.error(f'Job "{job.name}" has no more destination directories with enough space for more work.')
    job.destination_directory = valid_destinations

    return job

        
def load_jobs(config_jobs):
    jobs = []
    checked_job_names = []
    checked_temporary_directories = []
    for info in config_jobs:
        job = deepcopy(Job())
        job.total_running = 0
        job.name = info['name']
        if job.name in checked_job_names:
            raise InvalidConfigurationSetting(f'Found the same job name for multiple jobs. Job names should be unique. '
                                              f'Duplicate: {job.name}')
        checked_job_names.append(info['name'])
        temporary_directory = info['temporary_directory']
        if not isinstance(temporary_directory, list):
            temporary_directory = [temporary_directory]
        for directory in temporary_directory:
            if directory not in checked_temporary_directories:
                checked_temporary_directories.append(directory)
                continue
            raise InvalidConfigurationSetting(f'You cannot use the same temporary directory for more than one job: '
                                              f'{directory}')
        job.temporary_directory = temporary_directory
        job.destination_directory = info['destination_directory']
        jobs.append(job)
    return jobs


def determine_job_size(k_size):
    try:
        k_size = int(k_size)
    except ValueError:
        return 0
    base_k_size = 32
    size = 109000000000
    if k_size < base_k_size:
        # Why 2.058? Just some quick math.
        size /= pow(2.058, base_k_size-k_size)
    if k_size > base_k_size:
        # Why 2.06? Just some quick math from my current plots.
        size *= pow(2.06, k_size-base_k_size)
    return size

