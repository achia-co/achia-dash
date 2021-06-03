import logging
import os
import platform
import psutil
import re

from copy import deepcopy
from datetime import datetime

class Work:
    work_id = None
    job = None
    pid = None
    plot_id = None
    log_file = None

    temporary_drive = None
    temporary2_drive = None
    destination_drive = None

    current_phase = 1

    datetime_start = None
    datetime_end = None

    phase_times = {}
    total_run_time = None

    completed = False

    progress = 0
    temp_file_size = 0
    k_size = None



def _contains_in_list(string, lst, case_insensitive=False):
    if case_insensitive:
        string = string.lower()
    for item in lst:
        if case_insensitive:
            item = item.lower()
        if string not in item:
            continue
        return True
    return False


def get_manager_processes():
    processes = []
    for process in psutil.process_iter():
        try:
            if not re.search(r'^pythonw?(?:\d+\.\d+|\d+)?(?:\.exe)?$', process.name(), flags=re.I):
                continue
            if not _contains_in_list('python', process.cmdline(), case_insensitive=True) or \
                    not _contains_in_list('stateless-manager.py', process.cmdline()):
                continue
            processes.append(process)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes


def is_windows():
    return platform.system() == 'Windows'


def get_chia_executable_name():
    return f'chia{".exe" if is_windows() else ""}'


def get_plot_k_size(commands):
    try:
        k_index = commands.index('-k') + 1
    except ValueError:
        return None
    return commands[k_index]


def get_plot_directories(commands):
    flag = 0
    temporary_directory = None
    destination_directory = None
    temporary2_directory = None
    try:
        temporary_index = commands.index('-t') + 1
        destination_index = commands.index('-d') + 1
        flag = 1
    except ValueError:
        pass
    
    if flag == 0:
        for item in commands:
                 if '-t' in item:
                     temporary_directory = item[2:]
                 if '-d' in item:
                     destination_directory = item[2:]
    else:
        temporary_directory = commands[temporary_index]
        destination_directory = commands[destination_index]
    # try:
    #     temporary2_index = commands.index('-2') + 1
    # except ValueError:
    #     temporary2_index = None
    # if temporary2_index:
    #     temporary2_directory = commands[temporary2_index]
    return temporary_directory, temporary2_directory, destination_directory




def get_system_drives():
    drives = []
    for disk in psutil.disk_partitions(all=True):
        drive = disk.mountpoint
        if is_windows():
            drive = os.path.splitdrive(drive)[0]
        drives.append(drive)
    drives.sort(reverse=True)
    return drives


def identify_drive(file_path, drives):
    if not file_path:
        return None
    for drive in drives:
        if drive not in file_path:
            continue
        return drive
    return None


def get_plot_id(file_path=None, contents=None):
    if not contents:
        f = open(file_path, 'r')
        contents = f.read()
        f.close()
    match = re.search(rf'^ID: (.*?)$', contents, flags=re.M)
    if match:
        return match.groups()[0]
    return None

def get_plot_drives(commands, drives=None):
    if not drives:
        drives = get_system_drives()
    temporary_directory, temporary2_directory, destination_directory = get_plot_directories(commands=commands)
    temporary_drive = identify_drive(file_path=temporary_directory, drives=drives)
    destination_drive = identify_drive(file_path=destination_directory, drives=drives)
    temporary2_drive = None
    if temporary2_directory:
        temporary2_drive = identify_drive(file_path=temporary2_directory, drives=drives)
    return temporary_drive, temporary2_drive, destination_drive

def get_temp_size(plot_id, temporary_directories):
    if not plot_id:
        return 0
    temp_size = 0
    directories = []
    for dir in temporary_directories:
        if dir:
            directories += [os.path.join(dir, file) for file in os.listdir(dir) if file]
        for file_path in directories:
            if plot_id not in file_path:
                continue
            try:
                temp_size += os.path.getsize(file_path)
            except FileNotFoundError:
                pass
    return temp_size


def get_running_plots():
    chia_processes = []
    running_work = {}
    logging.debug(f'Getting running plots')
    chia_executable_name = get_chia_executable_name()
    for process in psutil.process_iter():
        try:
            if chia_executable_name not in process.name() and 'python' not in process.name().lower():
                continue
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
        try:
            if 'plots' not in process.cmdline() or 'create' not in process.cmdline():
                continue
        except (psutil.ZombieProcess, psutil.NoSuchProcess):
            continue
        if process.parent():
            try:
                parent_commands = process.parent().cmdline()
                if 'plots' in parent_commands and 'create' in parent_commands:
                    continue
                  
            except (psutil.AccessDenied, psutil.ZombieProcess):
                pass
        logging.debug(f'Found chia plotting process: {process.pid}')
        # print(process.cmdline()) 
        datetime_start = datetime.fromtimestamp(process.create_time())
        chia_processes.append([datetime_start, process])
    chia_processes.sort(key=lambda x: (x[0]))

    for datetime_start, process in chia_processes:
        logging.debug(f'Finding log file for process: {process.pid}')
        log_file_path = None
        commands = []
        try:
            commands = process.cmdline()
            for file in process.open_files():
                if '.mui' == file.path[-4:]:
                    continue
                if file.path[-4:] not in ['.log', '.txt']:
                    continue
                if file.path[-9:] == 'debug.log':
                    continue
                log_file_path = file.path
                logging.debug(f'Found log file: {log_file_path}')
                break
        except (psutil.AccessDenied, RuntimeError):
            logging.debug(f'Failed to find log file: {process.pid}')
        except psutil.NoSuchProcess:
            continue
        logging.debug(f'Finding associated job')
        plot_id = None
        if log_file_path:
            plot_id = get_plot_id(file_path=log_file_path)
        
        k_size = get_plot_k_size(commands=commands)
        work = deepcopy(Work())
        work.temporary_drive, work.temporary2_drive, work.destination_drive = get_plot_drives(commands=commands)
        temp_file_size = get_temp_size(plot_id=plot_id, temporary_directories={work.temporary_drive})
        work.temporary_directory, work.temporary2_directory, work.destination_directory = get_plot_directories(commands=commands)
        work.log_file = log_file_path
        work.datetime_start = datetime_start
        work.pid = process.pid
        work.plot_id = plot_id
        work.work_id = str(work.temporary_drive) + ' to ' + work.destination_drive
        work.temp_file_size = temp_file_size
        work.k_size = k_size
        running_work[work.pid] = work
        
    logging.debug(f'Finished finding running plots')
    return running_work

