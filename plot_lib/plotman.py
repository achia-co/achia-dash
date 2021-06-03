# -*- coding: utf-8 -*-
import psutil
from datetime import datetime, timedelta
from plot_lib.library.log import analyze_log_dates, check_log_progress
from plot_lib.library.processes import  get_running_plots
import plot_lib.library.configuration as config 
import plot_lib.library.print as plot_print
from plot_lib.library.processes  import  get_system_drives
import os
from psutil._common import bytes2human


def list_disk_usage(monitored_drives):
    disk_usage = []
    for part in psutil.disk_partitions(all=False):
            temp = {}
        # if str(part.device).format('%-17s') in monitored_drives:
            if os.name == 'nt':
                if 'cdrom' in part.opts or part.fstype == '':
                    # skip cd-rom drives with no disk in it; they may raise
                    # ENOENT, pop-up a Windows GUI error for a non-ready
                    # partition or just hang.
                    continue
            usage = psutil.disk_usage(part.mountpoint)
            
            temp["drive"] = '%-17s' % part.device
            temp["used"] = '%8s' % (bytes2human(usage.used))
            temp["total"] = '%8s' % (bytes2human(usage.total))
            temp["percent"] = '%5s%%' % (int(usage.percent))
            # disk_usage["fstype"] = str(part.fstype).format('%9s')
            temp["mount"] = '%s' % (part.mountpoint)
            disk_usage.append(temp)
    return disk_usage
        
        
class plot_manager:
    def __init__(self):             
        plot_print.pretty_print_table = self._pretty_print_table

    
    def _pretty_print_table(self,rows):
        table_data = []
        fields = []
        table_data = []
        for i, cell in enumerate(rows[0]):
            fields.append(cell)  
        for i,row in enumerate(rows):
            if i == 0:
                continue
            datum = {}
            for i, cell in enumerate(row):
                datum[fields[i]] = cell
            if datum:
                table_data.append(datum)
        return table_data
    
    def get_info_achia(self):
        summary={}
        try:
         
            log_directory, monitored_drives = config.get_config_info()
            summary['drive_info'] = list_disk_usage(monitored_drives)
   
            analysis = {'files': {}}
            analysis = analyze_log_dates(log_directory=log_directory, analysis=analysis)

            running_work = get_running_plots()

            check_log_progress(running_work)
            job_data = plot_print.get_job_data(running_work)
            job_data_print = plot_print.pretty_print_job_data(job_data)
            if job_data:
                    summary['Plot Jobs'] = job_data_print
            status = f'{"Running" if job_data else "Stopped"}'
            if status:
                summary['Plot_Manager_Status'] = status
    
            cpu =  f'{psutil.cpu_percent()}%'
            if cpu:
                summary['CPU Usage'] = cpu
            ram_usage = psutil.virtual_memory()
            summary['RAM Usage'] = f'{plot_print.pretty_print_bytes(ram_usage.used, "gb")}/{plot_print.pretty_print_bytes(ram_usage.total, "gb", 2, "GiB")}'
            summary['Plots Completed Yesterday'] = analysis["summary"].get(datetime.now().date() - timedelta(days=1), 0)
            summary['Plots Completed Today'] = analysis["summary"].get(datetime.now().date(), 0)
        except Exception as e:
            summary = {"error" : str(e)}
        return summary