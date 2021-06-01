# -*- coding: utf-8 -*-
import yaml
import os
import psutil
import logging
from datetime import datetime, timedelta
from plot_lib.library.utilities.jobs import load_jobs
from plot_lib.library.utilities.log import analyze_log_dates, check_log_progress
from plot_lib.library.utilities.processes import  get_running_plots
import plot_lib.library.parse.configuration as config 
import plot_lib.library.utilities.print as print
from plot_lib.library.utilities.processes  import  identify_drive, get_system_drives

class plot_manager:
    def __init__(self):             
        print.pretty_print_table = self._pretty_print_table
        config._get_config = self._new_get_config
        self.yaml_file =""
    def _new_get_config(self):
        f = open(self.yaml_file, 'r')
        config = yaml.load(stream=f, Loader=yaml.Loader)
        f.close()
        return config
    
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

    
    def get_dict_achia(self, jobs, running_work, analysis, drives):
        # Job Table
        try:
            summary = {}
            job_data = print.get_job_data(jobs=jobs, running_work=running_work)
            job_data_print = print.pretty_print_job_data(job_data)
            if job_data:
                summary['Plot Jobs'] = job_data_print
    
            drive_data = print.get_drive_data(drives, running_work, job_data)
            temp = []
            for drive in drive_data:
                if drive.get('#') is not None:
                    drive.pop('#')
                if drive.get('%') is not None: 
                    drive['percent']=drive['%']
                    drive.pop('%')
                temp.append(drive)
            summary['drive_info'] = temp
            manager_processes = print.get_manager_processes()
            status = f'{"Running" if manager_processes else "Stopped"}'
            if status:
                summary['Plot_Manager_Status'] = status
    
            cpu =  f'{psutil.cpu_percent()}%'
            if cpu:
                summary['CPU Usage'] = cpu
    
            ram_usage = psutil.virtual_memory()
            summary['RAM Usage'] = f'{print.pretty_print_bytes(ram_usage.used, "gb")}/{print.pretty_print_bytes(ram_usage.total, "gb", 2, "GiB")}'
    
    
            summary['Plots Completed Yesterday'] = analysis["summary"].get(datetime.now().date() - timedelta(days=1), 0)
            summary['Plots Completed Today'] = analysis["summary"].get(datetime.now().date(), 0)
        except Exception as e:
             logging.error(e)
             summary = {"error" : str(e)}
        return summary
    
    def get_info_achia(self):
        
        # try:
        log_directory, config_jobs = config.get_config_info()
        analysis = {'files': {}}
        system_drives = get_system_drives()
        drives = {'temp': [], 'temp2': [], 'dest': []}
        jobs_config_load = load_jobs(config_jobs)
        for job in jobs_config_load:
            directories = {
                'dest': job.destination_directory,
                'temp': job.temporary_directory,
                'temp2': job.temporary2_directory,
            }
        for key, directory_list in directories.items():
            if directory_list is None:
                continue
            if not isinstance(directory_list, list):
                directory_list = [directory_list]
            for directory in directory_list:
                drive = identify_drive(file_path=directory, drives=system_drives)
                if drive in drives[key]:
                    continue
                drives[key].append(drive)
    
        running_work = {}
        analysis = analyze_log_dates(log_directory=log_directory, analysis=analysis)
        jobs, running_work = get_running_plots(jobs=jobs_config_load, running_work=running_work)
        check_log_progress(jobs=jobs, running_work=running_work)
        summary = self.get_dict_achia(jobs=jobs_config_load, running_work=running_work, analysis=analysis, drives=drives)
        
        # except Exception as e:
        #     summary = {"error" : str(e)}
        return summary