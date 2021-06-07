
import asyncio
import logging
import logging.handlers
import logging
import os
import json
import yaml
import requests

from plot_lib.plotman import plot_manager 
from chia_lib.chia_export import chia_report
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# if logger.handlers:
#     print(logger.handlers)
#     for hnd in logger.handlers:
#         logger.removeHandler(hnd)


# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)    
# formatter = logging.Formatter("%(asctime)s - %(message)s")
# handler.setFormatter(formatter)
# logger.addHandler(handler)


# parser = argparse.ArgumentParser(description='Process some integers.')
# parser.add_argument('--debug',    default=False,     help='Enable debug')
# args = parser.parse_args()


# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)

# formatter = logging.Formatter("%(asctime)s - %(message)s")
# handler.setFormatter(formatter)
# if logger.handlers:
#     print(logger.handlers)
#     for hnd in logger.handlers:
#         logger.removeHandler(hnd)
# logger.addHandler(handler)

# logger.info("Starting achia service node....")
logger.debug('Start of program')



class achia_logger:
    def get_config_from_yaml(self, gui=False):
        
        file_name = 'achia.yaml'
        config = {} 
        try:
            f = open(file_name, 'r')
            config = yaml.load(stream=f, Loader=yaml.Loader)
            f.close() 
        except:
            pass
        if config.get("TOKEN",None) is None:
            config["TOKEN"] = input("No TOKEN saved, please enter: ")
        if config.get("MACHINE_ID",None) is None:
            config["MACHINE_ID"] = input("No Machine ID saved, please enter: ")
        if 'PLOTTING_LOGS_PATH' not in config:
            config["PLOTTING_LOGS_PATH"] = input("The directory of chia plotting logs was not saved, please enter: ")
        if not os.path.exists(config["PLOTTING_LOGS_PATH"]):
            os.makedirs(config["PLOTTING_LOGS_PATH"])
        with open(file_name, 'w') as outfile:
            yaml.dump(config, outfile, default_flow_style=False)
        self.config = config
        self.set_value()
        
        return config
    
    def set_value(self):
        self.post_plot_url = 'https://dash.achia.co/machines/' + self.config['MACHINE_ID'] + '/receive_plotsdraw_data/'
        self.post_stat_url = 'https://dash.achia.co/machines/' + self.config['MACHINE_ID'] + '/receive_data/'
        self.headers = {'Authorization' : self.config['TOKEN'],'Content-type': 'application/json', 'Accept': 'text/plain'}
       
    
    def run(self):
        report = {}
        pm = plot_manager()
        pm.log_directory=self.config["PLOTTING_LOGS_PATH"]
        plot_report_intance = pm.get_info_achia()
        chia_report_intance = chia_report()
        report["plot_report"] = plot_report_intance
        logging.debug(plot_report_intance)
        report["chia_report"] = chia_report_intance   
        logging.debug(chia_report_intance)
        if chia_report_intance.get('error',None) is not None:
            logging.error("Getting chia blockchain status has error:")
            logging.error(chia_report_intance['error'])
            
        else:
            r_chia = requests.post(self.post_stat_url, json=json.dumps(chia_report_intance), headers=self.headers)
            report["r_chia"] = r_chia
            if r_chia.status_code == 200:
                logging.info("Sending chia block chain status -- Data was sent successfully")
            else:
                logging.error("Sending chia block chain status -- Server replied with error:")
                logging.error(r_chia.content)
        
        if plot_report_intance.get('error',None) is not None:
            logging.error("Getting plotting status has error:")
            logging.error(plot_report_intance['error'])
        else:  
            r_plot = requests.post(self.post_plot_url, json=json.dumps(plot_report_intance), headers=self.headers)
            report["r_plot"] = r_plot
            if r_plot.status_code == 200:
                logging.info("Sending plotting status -- Data was sent successfully")
            else:
                logging.error("Sending plotting status -- Server replied with error:")
                logging.error(r_plot.content)          
        return report
    
    async def worker(self):
        logging.info('Start worker')
        while True:
            self.run()
            await asyncio.sleep(60)
            continue
            
    
    def achia_loop(self):
        asyncio.ensure_future(self.worker())
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
    chia_logger = achia_logger()
    chia_logger.get_config_from_yaml()
    input("Press enter to continue...")
    run_summary = chia_logger.run()
    chia_logger.achia_loop()

