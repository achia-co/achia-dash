import dateparser
import logging
import os
import psutil
import re

from plot_lib.library.print import pretty_print_time



def _analyze_log_end_date(contents):
    match = re.search(r'total time = ([\d\.]+) seconds\. CPU \([\d\.]+%\) [A-Za-z]+\s([^\n]+)\n', contents, flags=re.I)
    if not match:
        return False
    total_seconds, date_raw = match.groups()
    total_seconds = pretty_print_time(int(float(total_seconds)))
    parsed_date = dateparser.parse(date_raw)
    return dict(
        total_seconds=total_seconds,
        date=parsed_date,
    )


def _get_date_summary(analysis):
    summary = analysis.get('summary', {})
    for file_path in analysis['files'].keys():
        if analysis['files'][file_path]['checked']:
            continue
        analysis['files'][file_path]['checked'] = True
        end_date = analysis['files'][file_path]['data']['date'].date()
        if end_date not in summary:
            summary[end_date] = 0
        summary[end_date] += 1
    analysis['summary'] = summary
    return analysis


def get_completed_log_files(log_directory, skip=None):
    if not skip:
        skip = []
    files = {}
    for file in os.listdir(log_directory):
        if file[-4:] not in ['.log', '.txt']:
            continue
        file_path = os.path.join(log_directory, file)
        if file_path in skip:
            continue
        f = open(file_path, 'r')
        try:
            contents = f.read()
        except UnicodeDecodeError:
            continue
        f.close()
        if 'Total time = ' not in contents:
            continue
        files[file_path] = contents
    return files


def analyze_log_dates(log_directory, analysis):
    files = get_completed_log_files(log_directory, skip=list(analysis['files'].keys()))
    for file_path, contents in files.items():
        data = _analyze_log_end_date(contents)
        if data is None:
            continue
        analysis['files'][file_path] = {'data': data, 'checked': False}
    analysis = _get_date_summary(analysis)
    return analysis


def analyze_log_times(log_directory):
    total_times = {1: 0, 2: 0, 3: 0, 4: 0}
    line_numbers = {1: [], 2: [], 3: [], 4: []}
    count = 0
    files = get_completed_log_files(log_directory)
    for file_path, contents in files.items():
        count += 1
        phase_times, phase_dates = get_phase_info(contents, pretty_print=False)
        for phase, seconds in phase_times.items():
            total_times[phase] += seconds
        splits = contents.split('Time for phase')
        phase = 0
        new_lines = 1
        for split in splits:
            phase += 1
            if phase >= 5:
                break
            new_lines += split.count('\n')
            line_numbers[phase].append(new_lines)

    for phase in range(1, 5):
        print(f'  phase{phase}_line_end: {int(round(sum(line_numbers[phase]) / len(line_numbers[phase]), 0))}')

    for phase in range(1, 5):
        print(f'  phase{phase}_weight: {round(total_times[phase] / sum(total_times.values()) * 100, 2)}')


def get_phase_info(contents,  pretty_print=True):

    phase_times = {}
    phase_dates = {}

    for phase in range(1, 5):
        match = re.search(rf'time for phase {phase} = ([\d\.]+) seconds\. CPU \([\d\.]+%\) [A-Za-z]+\s([^\n]+)\n', contents, flags=re.I)
        if match:
            seconds, date_raw = match.groups()
            seconds = float(seconds)
            phase_times[phase] = pretty_print_time(int(seconds), True) if pretty_print else seconds
            parsed_date = dateparser.parse(date_raw)
            phase_dates[phase] = parsed_date

    return phase_times, phase_dates


def get_progress(line_count):
    phase1_line_end =  801
    phase2_line_end =  834
    phase3_line_end =  2474
    phase4_line_end =  2620
    phase1_weight =  33.4
    phase2_weight =  20.43
    phase3_weight =  42.29
    phase4_weight =  3.88
    progress = 0
    if line_count > phase1_line_end:
        progress += phase1_weight
    else:
        progress += phase1_weight * (line_count / phase1_line_end)
        return progress
    if line_count > phase2_line_end:
        progress += phase2_weight
    else:
        progress += phase2_weight * ((line_count - phase1_line_end) / (phase2_line_end - phase1_line_end))
        return progress
    if line_count > phase3_line_end:
        progress += phase3_weight
    else:
        progress += phase3_weight * ((line_count - phase2_line_end) / (phase3_line_end - phase2_line_end))
        return progress
    if line_count > phase4_line_end:
        progress += phase4_weight
    else:
        progress += phase4_weight * ((line_count - phase3_line_end) / (phase4_line_end - phase3_line_end))
    return progress


def check_log_progress(running_work):
    for pid, work in list(running_work.items()):
        logging.debug(f'Checking log progress for PID: {pid}')
        if not work.log_file:
            continue
        f = open(work.log_file, 'r')
        data = f.read()
        f.close()

        line_count = (data.count('\n') + 1)

        progress = get_progress(line_count=line_count)

        phase_times, phase_dates = get_phase_info(data)
        current_phase = 1
        if phase_times:
            current_phase = max(phase_times.keys()) + 1
        work.phase_times = phase_times
        work.phase_dates = phase_dates
        work.current_phase = current_phase
        work.progress = f'{progress:.2f}%'
        # del running_work[pid]
