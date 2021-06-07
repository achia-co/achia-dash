
import aiohttp
import json

# from chia.rpc.farmer_rpc_client import FarmerRpcClient
# from chia.rpc.full_node_rpc_client import FullNodeRpcClient
# from chia.rpc.harvester_rpc_client import HarvesterRpcClient
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16
import asyncio
import nest_asyncio
nest_asyncio.apply()

import logging
logger = logging.getLogger(__name__)

async def farmer_summary_achia(wallet_rpc_port: int,harvester_rpc_port: int, rpc_port: int, farmer_rpc_port: int) -> None:
    import chia.cmds.farm_funcs as ff
    
    try:
        amounts = await ff.get_wallets_stats(wallet_rpc_port)
    except Exception as e:
        amounts = {'error': e} 
    
    try:
        plots = await ff.get_plots(harvester_rpc_port)
    except Exception as e:
        plots = {'error': e}     
    
    try:   
        blockchain_state = await ff.get_blockchain_state(rpc_port)

    except Exception as e:
        blockchain_state =  {'error': e}   

    try: 
        farmer_running = await ff.is_farmer_running(farmer_rpc_port)
    except Exception as e:
        farmer_running =  {'error': e} 
    
    try:    
        average_block_time =  await ff.get_average_block_time(rpc_port)
    except Exception as e:
        average_block_time = {'error': e} 

    return {"farm_stat" : {"farmer_running":farmer_running, "amounts": amounts,"plot": plots},
                "blockchain_state": blockchain_state, "average_block_time" : int(average_block_time),   }




async def wallet_summary_achia(wallet_rpc_port: int, fingerprint: int, extra_params: dict):
    try:
        result = {"connected":False}
        config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
        self_hostname = config["self_hostname"]
        if wallet_rpc_port is None:
            wallet_rpc_port = config["wallet"]["rpc_port"]
        wallet_client = await WalletRpcClient.create(self_hostname, uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config)
        summaries_response = await wallet_client.get_wallets()
        config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
        address_prefix = config["network_overrides"]["config"][config["selected_network"]]["address_prefix"]
        result['connected'] = True
        height_info = await wallet_client.get_height_info()
        sync_status = await wallet_client.get_synced()
        result = {  "wallet": summaries_response,
                    "address_prefix": address_prefix,
                    'height_info':height_info,
                    'sync_status':sync_status,
                    'wallet_balances':[]}
        for summary in summaries_response:
            temp = {}
            temp['wallet_id'] = summary["id"]
            temp['wallet_balance'] = await wallet_client.get_wallet_balance(summary["id"])
            result['wallet_balances'].append(temp)
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if isinstance(e, aiohttp.ClientConnectorError):
            print(f"Connection error. Check if wallet is running at {wallet_rpc_port}")
        else:
            print(f"Exception from 'wallet' {e}")
            result = {'waller_error': e} 

    wallet_client.close()
    await wallet_client.await_closed()
    return result


def process_data_achia(payload):

    if payload["farm_stat"].get("error",None) is not None:
        print("Farmer is not running. Error:")
        print(payload["farm_stat"]["error"])
    else:
        plots = None
        if payload["farm_stat"]['farmer_running']:
            plot_number = 0
            plots_space_string = ""
            if payload["farm_stat"]["plot"] is not None:
                payload["farm_stat"]["plot_number"]=len(payload["farm_stat"]["plot"]["plots"])
                total_plot_size = 0
                plots = payload["farm_stat"]["plot"]
                if plots is not None:
                    plot_number = len(payload["farm_stat"]["plot"]["plots"])
                    total_plot_size = sum(map(lambda x: x["file_size"], plots["plots"]))
                    plots_space_human_readable = total_plot_size / 1024 ** 3
                    if plots_space_human_readable >= 1024 ** 2:
                        plots_space_human_readable = plots_space_human_readable / (1024 ** 2)
                        plots_space_string = f"{plots_space_human_readable:.3f} PiB"
                    elif plots_space_human_readable >= 1024:
                        plots_space_human_readable = plots_space_human_readable / 1024
                        plots_space_string = f"{plots_space_human_readable:.3f} TiB"
                    else:
                        plots_space_string = f"{plots_space_human_readable:.3f} GiB"
                else:
                    plot_number = 0
                    plots_space_string = ("Unknown")
                
            payload["farm_stat"].pop('plot', None)
            payload["farm_stat"]["plot_number"] = plot_number
            payload["farm_stat"]["plots_space_string"] = plots_space_string

    
        if payload.get("blockchain_state",None) is not None:
            if payload["blockchain_state"].get("error",None) is not None:
                print("Fullnode is not running. Error:")
                print(payload["blockchain_state"]["error"])
            else:
                blockchain_state = payload["blockchain_state"]
                if blockchain_state is not None:
                    network_space_human_readable = blockchain_state["space"] / 1024 ** 4
                    if network_space_human_readable >= 1024**2:
                        network_space_human_readable = network_space_human_readable / 1024**2
                        network_space_string = f"{network_space_human_readable:.3f} EiB"  
                    elif network_space_human_readable >= 1024:
                        network_space_human_readable = network_space_human_readable / 1024
                        network_space_string = f"{network_space_human_readable:.3f} PiB"    
                    else:
                        network_space_string = f"{network_space_human_readable:.3f} TiB"
                        
                else:
                    network_space_string = "Unknown"
                minutes = -1
                if blockchain_state is not None and plots is not None:
                    proportion = total_plot_size / blockchain_state["space"] if blockchain_state["space"] else -1
                    minutes = int((payload["average_block_time"] / 60) / proportion) if proportion else -1
                payload["blockchain_state"]["space"] = 0
                payload['blockchain_state'].pop('peak', None)
                if payload["farm_stat"].get("error",None) is None:
                    if payload["farm_stat"]['farmer_running']:
                        payload["farm_stat"]["network_space_string"] = network_space_string
                        payload["farm_stat"]["estimated_time_to_win_in_minutes"] = minutes

    return payload



# print(type(data))
# url="https://localhost:9000/machines/6c96136/receive_data/"
# r = requests.post(url, json=data,headers=headers,verify=False)
# print(r.text)
# def rearrange_json(importjason):
    
def excuteconvert(listkeycheck,oldata,new_lv1_json,listwallet=None):
	if listwallet==None:
		for key in oldata:
				data=oldata[key]
				if type(data) == dict:
					new_lv1_json[key]= {}
				elif key=="wallet_balances":
					continue
				elif type(data) == list:
					new_lv1_json[key]= []
				else:
					new_lv1_json[key]=data
		for key in listkeycheck:
				if(key=="wallet_ballances"):
					new_lv1_json[key]=[]
				if key not in new_lv1_json:
					if type(listkeycheck[key])==int:
						new_lv1_json[key]=0
					if type(listkeycheck[key])==str:
						new_lv1_json[key]="No infomation"
					if type(listkeycheck[key])==bool:
						new_lv1_json[key]=False
					if type(listkeycheck[key])==dict:
						new_lv1_json[key]={}
					if type(listkeycheck[key])==list:
						new_lv1_json[key]=[]
	else:
		pass
	return new_lv1_json		


def rearrange_json(importjason) -> dict():
	newjson = {}
	keycheck_farmstat={
      "farmer_running":True,
      "farmed_amount":0,
      "farmer_reward_amount":0,
      "fee_amount":0,
      "last_height_farmed":0,
      "pool_reward_amount":0,
      "plot_number":0,
      "plots_space_string":"",
      "network_space_string":"",
      "estimated_time_to_win_in_minutes":0
   }
	keycheck_fullnode={"difficulty":0,
      "genesis_challenge_initialized":True,
      "mempool_size":0,
      "space":0,
      "sub_slot_iters":0,
      "sync":{
         "sync_mode":False,
         "sync_progress_height":0,
         "sync_tip_height":0,
         "synced":False
      }
      }
	keycheck_walletsumanry={
      "address_prefix":"",
      "height_info":0,
      "sync_status":False,
      "wallet_ballances":[
         {
            "wallet_id":0,
            "name":"Chia Wallet",
            "type":0,
            "balance":{
               "confirmed_wallet_balance":0,
               "max_send_amount":0,
               "pending_change":0,
               "spendable_balance":0,
               "unconfirmed_wallet_balance":0
            }
         }
      ]
   }
	try:
		farm_stat=importjason["farm_stat"]
	except Exception as es:
		farm_stat=None
	try:
		full_node=importjason["blockchain_state"]
	except Exception as es:
		full_node=None
	try:
		average_block_time=importjason["average_block_time"]
	except Exception as es:
		average_block_time=0
	try:
		wallet_summary=importjason["wallet_summary"]
	except Exception as e:
		wallet_summary=None
	try:
		wallet=importjason["wallet"]
	except Exception as e:
		wallet=None
	if farm_stat:
		# print(farm_stat)
		newjson["farm_stat"]={}
		newjson["farm_stat"]=excuteconvert(listkeycheck=keycheck_farmstat,oldata=farm_stat,new_lv1_json=newjson["farm_stat"])
	
	if full_node:
		newjson["blockchain_state"]={}
		newjson["blockchain_state"]= excuteconvert(listkeycheck=keycheck_fullnode,oldata=full_node,new_lv1_json=newjson["blockchain_state"])

		try:
			oldata=full_node["sync"]
		except Exception as es:
			oldata=None

		if oldata is not None:
			newjson["blockchain_state"]["sync"]=excuteconvert(listkeycheck=keycheck_fullnode["sync"],oldata=oldata,new_lv1_json=newjson["blockchain_state"]["sync"])
	
		
	if average_block_time:
		newjson["average_block_time"]=average_block_time
	else:
		newjson["average_block_time"]=0
	if wallet_summary:
		newjson["wallet_summary"]={}
		newjson["wallet_summary"]=excuteconvert(listkeycheck=keycheck_walletsumanry,oldata=wallet_summary,new_lv1_json=newjson["wallet_summary"])
		try:
			listwallet=wallet_summary["wallet"]
		except Exception as es:
			listwallet=None
		try:
			balances=wallet_summary["wallet_balances"]
		except Exception as es:
			balances=None
		if listwallet and balances is not None: # balance  va wallet deu co 
			for wallet in listwallet:
				for balance in balances:
					if wallet["id"]==balance["wallet_id"]:
						try :
							balance["name"]=wallet["name"] # balance   ko co
						except Exception as e:	
							balance["name"]="No infomation"
						try :
							balance["type"]=wallet["type"]
						except Exception as e:	
							balance["type"]=0
						try :
							balance['balance']=balance['wallet_balance'] # balance   ko co
							del balance['wallet_balance']
						except Exception as e:
							balance['balance']={}

						
						newjson["wallet_summary"]["wallet_ballances"].append(balance)
		else:
			if balances is not None: # balance  co nhung wallet khong co
				for balance in balances:
					balance["name"]="No infomation"
					balance["type"]=0
					try :
						balance['balance']=balance['wallet_balance']  # balance   ko co
					except Exception as e:
						balance['balance']={}
					newjson["wallet_summary"]["wallet_ballances"].append(balance)
					# load blance or default
		
		for i in range(0,len(newjson["wallet_summary"]['wallet_ballances'])):
			newjson["wallet_summary"]['wallet_ballances'][i]['balance']=excuteconvert(listkeycheck=keycheck_walletsumanry['wallet_ballances'][0]['balance'],
				oldata=newjson["wallet_summary"]['wallet_ballances'][i]['balance'],new_lv1_json={}
				)
	return newjson 
		

    
def chia_report():
    payload = asyncio.run(farmer_summary_achia(None,None,None,None))
    payload = process_data_achia(payload)
    logger.debug(payload)
    temp = asyncio.run(wallet_summary_achia(None, None, {}))
    payload["wallet_summary"] = temp
    return rearrange_json(payload)
    