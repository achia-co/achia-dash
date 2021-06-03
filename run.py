
import argparse
import os, sys
import asyncio
import logging
import logging.handlers
import datetime as dt

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--debug',    default=False,     help='Enable debug')
args = parser.parse_args()

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(message)s")
handler.setFormatter(formatter)
if logger.handlers:
    for hnd in logger.handlers:
        logger.removeHandler(hnd)
logger.addHandler(handler)
logger.info("Starting achia service node....")



logging.debug('Start of program')

def get_config():
    file_name = 'achia.yaml'
    config = {} 
    try:
        f = open(file_name, 'r')
        config = yaml.load(stream=f, Loader=yaml.Loader)
        f.close() 
    except:
        pass
    return config


import json
import yaml
import requests
        
config = get_config()
if(config['MACHINE_ID']=="xxxxxxx"):
    input("You haven't changed the Machine ID or possibly the Token, please edit the achia.yaml file before use")
    sys.exit()
post_plot_url = 'https://dash.achia.co/machines/' + config['MACHINE_ID'] + '/receive_plotsdraw_data/'
post_stat_url = 'https://dash.achia.co/machines/' + config['MACHINE_ID'] + '/receive_data/'

# post_plot_url = 'https://localhost:9000/machines/' + config['MACHINE_ID'] + '/receive_plotsdraw_data/'
# post_stat_url = 'https://localhost:9000/machines/' + config['MACHINE_ID'] + '/receive_data/'


headers = {'Authorization' : config['TOKEN'],'Content-type': 'application/json', 'Accept': 'text/plain'}


# sys.path.append(config['swar_plot_manager_path'])
from plot_lib.plotman import plot_manager 

from chia_lib.chia_export import chia_report

def run():

    pm = plot_manager()
    plot_report_intance = pm.get_info_achia()
    chia_report_intance = chia_report()        
    r_plot = requests.post(post_plot_url, json=json.dumps(plot_report_intance), headers=headers)
    r_chia = requests.post(post_stat_url, json=json.dumps(chia_report_intance), headers=headers)
    

    if r_chia.status_code == 200:
        logging.info("Sending chia block chain status -- Data was sent successfully")
    else:
          logging.error("Sending chia block chain status -- Server replied with error:")
          print(r_chia.content)
          if chia_report_intance.get('error',None) is not None:
              logging.error("Getting chia blockchain status has error:")
              print(chia_report_intance['error'])

    if r_plot.status_code == 200:
        logging.info("Sending plotting status -- Data was sent successfully")
    else:
          logging.error("Sending plotting status -- Server replied with error:")
          print(r_plot.content)
          if plot_report_intance.get('error',None) is not None:
              logging.error("Getting plotting status has error:")
              print(plot_report_intance['error'])
    
    return {"plot_report": plot_report_intance, "chia_report":chia_report_intance, 'r_plot': r_plot, "r_chia":r_chia}

async def worker():
    logger.info('Start worker')
    while True:
        run()
        await asyncio.sleep(60)
        continue
        

def main():
    asyncio.ensure_future(worker())
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        logging.error(asyncio.gather(*asyncio.Task.all_tasks()).cancel())
        logging.error(e)
        loop.stop()
        loop.run_forever()
    finally:
        loop.close()

if __name__ == '__main__':
    input("Press enter to continue...")
    run_summary = run()            
    main()

