import logging
import psutil

from copy import deepcopy
from datetime import datetime, timedelta

from plot_lib.library.utilities.exceptions import InvalidConfigurationSetting
from plot_lib.library.utilities.processes import identify_drive, is_windows, start_process
from plot_lib.library.utilities.objects import Job, Work
from plot_lib.library.utilities.log import get_log_file_name


def has_active_jobs_and_work(jobs):
    for job in jobs:
        if job.total_kicked_off < job.max_plots:
            return True
    return False


def get_target_directories(job, drives_free_space):
    job_offset = job.total_completed + job.total_running

    if job.skip_full_destinations:
        logging.debug('Checking for full destinations.')
        job = check_valid_destinations(job, drives_free_space)
    destination_directory = job.destination_directory
    temporary_directory = job.temporary_directory
    temporary2_directory = job.temporary2_directory

    if not destination_directory:
        return None, None, None, job

    if isinstance(job.destination_directory, list):
        destination_directory = job.destination_directory[job_offset % len(job.destination_directory)]
    if isinstance(job.temporary_directory, list):
        temporary_directory = job.temporary_directory[job_offset % len(job.temporary_directory)]
    if isinstance(job.temporary2_directory, list):
        temporary2_directory = job.temporary2_directory[job_offset % len(job.temporary2_directory)]

    return destination_directory, temporary_directory, temporary2_directory, job


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


def monitor_jobs_to_start(jobs, running_work, max_concurrent, max_for_phase_1, next_job_work, chia_location,
                          log_directory, next_log_check, minimum_minutes_between_jobs, system_drives):
    drives_free_space = {}
    for job in jobs:
        directories = [job.destination_directory]
        if isinstance(job.destination_directory, list):
            directories = job.destination_directory
        for directory in directories:
            drive = identify_drive(file_path=directory, drives=system_drives)
            if drive in drives_free_space:
                continue
            try:
                free_space = psutil.disk_usage(drive).free
            except:
                logging.exception(f"Failed to get disk_usage of drive {drive}.")
                # I need to do this because if Manager fails, I don't want it to break.
                free_space = None
            drives_free_space[drive] = free_space

    logging.debug(f'Free space before checking active jobs: {drives_free_space}')
    for pid, work in running_work.items():
        drive = work.destination_drive
        if drive not in drives_free_space or drives_free_space[drive] is None:
            continue
        work_size = determine_job_size(work.k_size)
        drives_free_space[drive] -= work_size
        logging.debug(drive)
    logging.debug(f'Free space after checking active jobs: {drives_free_space}')

    total_phase_1_count = 0
    for pid in running_work.keys():
        if running_work[pid].current_phase > 1:
            continue
        total_phase_1_count += 1

    for i, job in enumerate(jobs):
        logging.debug(f'Checking to queue work for job: {job.name}')
        if len(running_work.values()) >= max_concurrent:
            logging.debug(f'Global concurrent limit met, skipping. Running plots: {len(running_work.values())}, '
                         f'Max global concurrent limit: {max_concurrent}')
            continue
        if total_phase_1_count >= max_for_phase_1:
            logging.debug(f'Global max for phase 1 limit has been met, skipping. Count: {total_phase_1_count}, '
                         f'Setting Max: {max_for_phase_1}')
            continue
        phase_1_count = 0
        for pid in job.running_work:
            if running_work[pid].current_phase > 1:
                continue
            phase_1_count += 1
        logging.debug(f'Total jobs in phase 1: {phase_1_count}')
        if job.max_for_phase_1 and phase_1_count >= job.max_for_phase_1:
            logging.debug(f'Job max for phase 1 met, skipping. Max: {job.max_for_phase_1}')
            continue
        if job.total_kicked_off >= job.max_plots:
            logging.debug(f'Job\'s total kicked off greater than or equal to max plots, skipping. Total Kicked Off: '
                         f'{job.total_kicked_off}, Max Plots: {job.max_plots}')
            continue
        if job.name in next_job_work and next_job_work[job.name] > datetime.now():
            logging.debug(f'Waiting for job stagger, skipping. Next allowable time: {next_job_work[job.name]}')
            continue
        discount_running = 0
        if job.concurrency_start_early_phase is not None:
            for pid in job.running_work:
                work = running_work[pid]
                try:
                    start_early_date = work.phase_dates[job.concurrency_start_early_phase - 1]
                except (KeyError, AttributeError):
                    start_early_date = work.datetime_start

                if work.current_phase < job.concurrency_start_early_phase:
                    continue
                if datetime.now() <= (start_early_date + timedelta(minutes=job.concurrency_start_early_phase_delay)):
                    continue
                discount_running += 1
        if (job.total_running - discount_running) >= job.max_concurrent:
            logging.debug(f'Job\'s max concurrent limit has been met, skipping. Max concurrent minus start_early: '
                         f'{job.total_running - discount_running}, Max concurrent: {job.max_concurrent}')
            continue
        if job.total_running >= job.max_concurrent_with_start_early:
            logging.debug(f'Job\'s max concurrnet limit with start early has been met, skipping. Max: {job.max_concurrent_with_start_early}')
            continue
        if job.stagger_minutes:
            next_job_work[job.name] = datetime.now() + timedelta(minutes=job.stagger_minutes)
            logging.debug(f'Calculating new job stagger time. Next stagger kickoff: {next_job_work[job.name]}')
        if minimum_minutes_between_jobs:
            logging.debug(f'Setting a minimum stagger for all jobs. {minimum_minutes_between_jobs}')
            minimum_stagger = datetime.now() + timedelta(minutes=minimum_minutes_between_jobs)
            for j in jobs:
                if next_job_work[j.name] > minimum_stagger:
                    logging.debug(f'Skipping stagger for {j.name}. Stagger is larger than minimum_minutes_between_jobs. '
                                 f'Min: {minimum_stagger}, Current: {next_job_work[j.name]}')
                    continue
                logging.debug(f'Setting a new stagger for {j.name}. minimum_minutes_between_jobs is larger than assigned '
                             f'stagger. Min: {minimum_stagger}, Current: {next_job_work[j.name]}')
                next_job_work[j.name] = minimum_stagger

        job, work = start_work(
            job=job,
            chia_location=chia_location,
            log_directory=log_directory,
            drives_free_space=drives_free_space,
        )
        jobs[i] = deepcopy(job)
        if work is None:
            continue
        total_phase_1_count += 1
        next_log_check = datetime.now()
        running_work[work.pid] = work

    return jobs, running_work, next_job_work, next_log_check


def start_work(job, chia_location, log_directory, drives_free_space):
    logging.debug(f'Starting new plot for job: {job.name}')
    nice_val = job.unix_process_priority
    if is_windows():
        nice_val = job.windows_process_priority

    now = datetime.now()
    log_file_path = get_log_file_name(log_directory, job, now)
    logging.debug(f'Job log file path: {log_file_path}')
    destination_directory, temporary_directory, temporary2_directory, job = \
        get_target_directories(job, drives_free_space=drives_free_space)
    if not destination_directory:
        return job, None

    logging.debug(f'Job temporary directory: {temporary_directory}')
    logging.debug(f'Job destination directory: {destination_directory}')

    work = deepcopy(Work())
    work.job = job
    work.log_file = log_file_path
    work.datetime_start = now
    work.work_id = job.current_work_id

    job.current_work_id += 1

    if job.temporary2_destination_sync:
        logging.debug(f'Job temporary2 and destination sync')
        temporary2_directory = destination_directory
    logging.debug(f'Job temporary2 directory: {temporary2_directory}')

    plot_command = plots.create(
        chia_location=chia_location,
        farmer_public_key=job.farmer_public_key,
        pool_public_key=job.pool_public_key,
        size=job.size,
        memory_buffer=job.memory_buffer,
        temporary_directory=temporary_directory,
        temporary2_directory=temporary2_directory,
        destination_directory=destination_directory,
        threads=job.threads,
        buckets=job.buckets,
        bitfield=job.bitfield,
        exclude_final_directory=job.exclude_final_directory,
    )
    logging.debug(f'Starting with plot command: {plot_command}')

    log_file = open(log_file_path, 'a')
    logging.debug(f'Starting process')
    process = start_process(args=plot_command, log_file=log_file)
    pid = process.pid
    logging.debug(f'Started process: {pid}')

    logging.debug(f'Setting priority level: {nice_val}')
    psutil.Process(pid).nice(nice_val)
    logging.debug(f'Set priority level')
    if job.enable_cpu_affinity:
        logging.debug(f'Setting process cpu affinity: {job.cpu_affinity}')
        psutil.Process(pid).cpu_affinity(job.cpu_affinity)
        logging.debug(f'Set process cpu affinity')

    work.pid = pid
    job.total_running += 1
    job.total_kicked_off += 1
    job.running_work = job.running_work + [pid]
    logging.debug(f'Job total running: {job.total_running}')
    logging.debug(f'Job running: {job.running_work}')

    return job, work
