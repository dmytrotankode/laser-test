"""Шаг 3: прогнать v21..v25 через работающий веб-сервис.

Дёргаются ровно те HTTP-эндпоинты, которые вызывает страница по кнопкам, поэтому
это тот же путь, каким пользуется оператор, а не обходная дорожка: v20 прогнан
руками через интерфейс, остальные - здесь, чтобы не кликать пятикратно.

Ничего не подбирается и не настраивается. Сессии создаются штатно, .LS пишется
штатным step05 вместе с его проверкой валидности.
"""
import sys
import time
import json
import urllib.request

BASEURL = 'http://127.0.0.1:5056'
VARIANTS = ['v21', 'v22', 'v23', 'v24', 'v25']
STEPS = [1, 2, 3, 4, 5]
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def get(path):
    with urllib.request.urlopen(BASEURL + path, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))


sessions = {}
for var in VARIANTS:
    s = get(f'/api/start_session?variant={var}')['session_id']
    sessions[var] = s
    print(f'\n=== {var}  сессия {s}')
    for n in STEPS:
        get(f'/api/step0{n}?session_id={s}&action=start')
        for _ in range(600):
            time.sleep(1)
            st = get(f'/api/step0{n}?session_id={s}')
            if st['status'] == 'done':
                break
            if st['status'] == 'error':
                print(f'  шаг {n}: ОШИБКА {st["message"][:300]}')
                sys.exit(1)
        else:
            print(f'  шаг {n}: не дождались')
            sys.exit(1)
        if n == 4:
            d = st['data']
            print(f'  опора {d["etalon"]}, дистанция {d["nearest_distance"]}, '
                  f'вне диапазона {d["out_of_range"]}')
            print(f'  поправка {d["delta_rel_to_etalon"]}')
        if n == 5:
            print(f'  записан {st["data"].get("current_ls_file")}')

json.dump(sessions, open(__file__.replace('s6_run.py', 's6_sessions.json'), 'w'),
          indent=1)
print('\nсессии:', json.dumps(sessions, indent=1))
