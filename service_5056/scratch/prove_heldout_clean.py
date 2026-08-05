"""Доказательство, что ground_truth held-out варианта не участвует в расчёте.

Чтение кода — слабое доказательство: файл могли открыть в неочевидном месте.
Здесь проверка опытом. Берём фотографии v13, кладём под другим именем и БЕЗ
ground_truth.ls, прогоняем тот же конвейер (те же скрипты, что дёргает веб) и
сравниваем экспорт с обычным прогоном v13 побайтово.

Совпал байт-в-байт => записанная программа оператора на результат не влияет никак,
и прогон через веб — честная слепая проверка.
"""
import os
import sys
import json
import shutil
import filecmp
import subprocess

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
import lsgeom   # noqa: E402

SRC = "v13"
TMP = "_blind13"
SESS = "blind_check"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

src_dir = os.path.join(BASE, 'input', 'archive', SRC)
tmp_dir = os.path.join(BASE, 'input', 'archive', TMP)
sess_dir = os.path.join(BASE, 'results', SESS)

try:
    # 1. только снимки, никакого ground_truth.ls
    if os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    for f in ('back.png', 'left.png', 'top.png'):
        shutil.copy2(os.path.join(src_dir, f), os.path.join(tmp_dir, f))
    print(f"подготовлено {TMP}: {sorted(os.listdir(tmp_dir))}")
    assert not any(f.endswith('.ls') for f in os.listdir(tmp_dir)), "ls просочился"

    # 2. прогон тем же конвейером, что дёргает веб
    os.makedirs(sess_dir, exist_ok=True)
    shutil.copy(os.path.join(BASE, 'results', f'audit_{SRC}', 'step02_result.json'), sess_dir)
    json.dump({"variant": TMP}, open(os.path.join(sess_dir, 'config.json'), 'w',
                                     encoding='utf-8'))
    for step in ('step03_segment_monochrome', 'step04_fit_3d_pose',
                 'step05_visualize_export'):
        r = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', f'{step}.py'),
                            '--session', SESS], cwd=BASE, capture_output=True, text=True)
        print(f"  {step}: {'ok' if r.returncode == 0 else 'ОШИБКА'}")
        if r.returncode != 0:
            print(r.stdout[-800:], r.stderr[-800:])
            sys.exit(1)

    # 3. сравнение
    a = lsgeom.export_path(sess_dir)
    b = lsgeom.export_path(os.path.join(BASE, 'results', f'audit_{SRC}'))
    same = filecmp.cmp(a, b, shallow=False)
    s4a = json.load(open(os.path.join(sess_dir, 'step04_result.json'), encoding='utf-8'))
    s4b = json.load(open(os.path.join(BASE, 'results', f'audit_{SRC}',
                                      'step04_result.json'), encoding='utf-8'))
    print()
    print(f"сосед выбран:  вслепую {s4a['selected_neighbors']} "
          f"(дист {s4a['nearest_distance']}) | обычно {s4b['selected_neighbors']} "
          f"(дист {s4b['nearest_distance']})")
    print(f"поза:          вслепую {[round(v,3) for v in s4a['delta_rel_to_etalon'].values()]}")
    print(f"               обычно  {[round(v,3) for v in s4b['delta_rel_to_etalon'].values()]}")
    print()
    print("=" * 70)
    if same:
        print("ЭКСПОРТ СОВПАЛ БАЙТ-В-БАЙТ.")
        print("ground_truth.ls варианта на расчёт не влияет — проверка честно слепая.")
    else:
        print("ЭКСПОРТЫ РАЗЛИЧАЮТСЯ — где-то ground_truth всё же используется!")
        sys.exit(1)
    print("=" * 70)
finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)
    shutil.rmtree(sess_dir, ignore_errors=True)
    print(f"\nвременные {TMP} и сессия {SESS} удалены")
