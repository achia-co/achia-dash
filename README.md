Version 0.2

![Image of achia.co](https://github.com/achia-co/achia-dash/blob/main/img/achia.png)

# ACHIA - DASH
A python code to upload Chia blockchain stats, plotting stats and computer stats to achia.co dashboard so you can monitor you rig everywhere you want. This software can be used in concurrently with any plotting manager including the GUI.

### EXECUTABLE FILE - This is created for who have trouble using the source code

The latest -> https://github.com/achia-co/achia-dash/releases/download/v0.2/achia-dash.v.0.2.7z


### If you want to use the open source code, please use the steps below:

### Requirements

You will need Python 3.6 -> 3.8 

You will need Microsoft Visual C++ Redistributable for Visual Studio 

[x86: vc_redist.x86.exe](https://aka.ms/vs/16/release/vc_redist.x86.exe)

[x64: vc_redist.x64.exe](https://aka.ms/vs/16/release/vc_redist.x64.exe)
 
#### First you download the code and extract to a folder (e.g C:/achia-dash/achia-dash-main/ ) then we open CMD

```bash
cd to/your/achia-dash-main/path
# (Example: cd C:/achia-dash/achia-dash-main/)
```
#### Install required packages

```bash
python -m pip install -r requirements.txt
```

#### You need to modify the achia.yaml in the same folder to suit your configuration

```bash
Please use a note editor to edit achia.yaml
```

#### Then you just start the program and follow the instructions

```bash
python run.py
```

#### To stop

```bash
Please Ctrl+C multiple times in the CMD line
```

### WARNING 
**Important Note**: This script will just push the data from Chia and 's plot manager to achia, no sensitive information (e.g mnemonic keys, etc) is pushed to the server. Please review the code before using if you can. At achia.co, we aim to be a transparent and safe pool for everyone to join.

An example data being pushed to the server is shown below

```bash

chia_report =
{'farm_stat': {'farmer_running': True,
  'amounts': {},
  'plot_number': 219,
  'plots_space_string': '21.677 TiB',
  'network_space_string': '14101.122 PiB',
  'estimated_time_to_win_in_minutes': 199833,
  'farmed_amount': 0,
  'farmer_reward_amount': 0,
  'fee_amount': 0,
  'last_height_farmed': 0,
  'pool_reward_amount': 0},
 'blockchain_state': {'difficulty': 932,
  'genesis_challenge_initialized': True,
  'mempool_size': 51,
  'space': 0,
  'sub_slot_iters': 116391936,
  'sync': {'sync_mode': False,
   'sync_progress_height': 0,
   'sync_tip_height': 0,
   'synced': True}},
 'average_block_time': 18,
 'wallet_summary': {'wallet': [],
  'address_prefix': 'xch',
  'height_info': 354437,
  'sync_status': True,
  'wallet_ballances': [{'wallet_id': 1,
    'name': 'Chia Wallet',
    'type': 0,
    'balance': {'confirmed_wallet_balance': 1900000000000,
     'max_send_amount': 1900000000000,
     'pending_change': 0,
     'pending_coin_removal_count': 0,
     'spendable_balance': 1900000000000,
     'unconfirmed_wallet_balance': 1900000000000,
     'unspent_coin_count': 1,
     'wallet_id': 1}}]}}


plot_report =
{'Plot Jobs': [{'num': '1',
   'job': 'crucial',
   'k': '32',
   'plot_id': '9cb1cbc',
   'pid': '9208',
   'start': '2021-05-29 20:10:17',
   'elapsed_time': '05:31:07',
   'phase': '3',
   'phase_times': '03:23 / 01:19',
   'progress': '62.91%',
   'temp_size': '201 GiB'},
],
 'drive_info': [{'type': 't/-',
   'drive': 'C:',
   'used': '0.40TiB',
   'total': '0.45TiB',
   'temp': '1',
   'dest': '',
   'percent': '88.9%'},
],
 'Plot_Manager_Status': 'Running',
 'CPU Usage': '57.9%',
 'RAM Usage': '22.14/31.93GiB',
 'Plots Completed Yesterday': 0,
 'Plots Completed Today': 0}
```

#### 
Credit to: 
[Swar-Chia-Plot-Manager's](https://github.com/swar/Swar-Chia-Plot-Manager)
