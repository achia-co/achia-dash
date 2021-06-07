Version 0.1.2

![Image of achia.co](https://github.com/achia-co/achia-dash/blob/main/img/achia.png)

# ACHIA - DASH
Python скрипт для выгрузки статистики блокчейна Chia, статистики засева и фермерской статистики на доску achieve.co, чтобы вы могли контролировать свою ферму везде, где захотите. Это программное обеспечение может использоваться одновременно с любым менеджером засева участков, включая официальный GUI.
### ИСПОЛНЯЕМЫЙ ФАЙЛ - Создан для тех, у кого проблемы с использованием исходных кодов

https://github.com/achia-co/achia-dash/releases


### Если Вы хотите использовать открытый исходный код, следуйте следующим инструкциям:

### Необходимое ПО

Вам потребуется Python 3.6 -> 3.8 

Вам потребуется Microsoft Visual C++ Redistributable for Visual Studio 

[x86: vc_redist.x86.exe](https://aka.ms/vs/16/release/vc_redist.x86.exe)

[x64: vc_redist.x64.exe](https://aka.ms/vs/16/release/vc_redist.x64.exe)
 
#### Сначала скачайте и распакуйте исходный код в папку (например C:/achia-dash/achia-dash-main/ ) затем запустите CMD

```bash
cd ваш/путь/achia-dash-main/
# (например: cd C:/achia-dash/achia-dash-main/)
```
#### Установите зависимые библиотеки

```bash
python -m pip install -r requirements.txt
```

#### Отредактируйте файл achia.yaml в тойже директории в соответствии с Вашей конфигурацией

```bash
Пожалуйста, используйте текстовый редактор для редактирования achia.yaml
```

#### Затем вы просто запустите программу и следуйте инструкциям

```bash
python run.py
```

#### Чтобы остановить

```bash
Нажмите Ctrl+C несколько раз в окне CMD
```

### ВНИМАНИЕ 
**Важная информация**: Этот скрипт передаёт данные только из клиента Chia и Plot Manager'a. Никакой приватной информации (например мнемонические ключи) на сервер не передаётся. Пожалуйста, ознакомьтесь с исходными кодами перед использованием, если можете. Мы, команда achia.co стремимся быть прозрачным и безопасным пулом для всех желающих присоединться.
Ниже показан пример данных отправляемых на сервер

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
Благодарность: 
[Swar-Chia-Plot-Manager's](https://github.com/swar/Swar-Chia-Plot-Manager)
