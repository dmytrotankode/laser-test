"""Выгрузить .LS на все размеченные варианты за один проход.

По одному вызову на вариант получается вдесятеро дольше: каждый процесс заново
подбирает отступы ICP. Здесь кэш общий на весь прогон.
"""
import sys
import numpy as np
import export_ls as X

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VARIANTS = ['v1', 'v3', 'v4', 'v5', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12',
            'v14', 'v15', 'v16', 'v6', 'v13', 'v20', 'v21', 'v24', 'v25']

for v in VARIANTS:
    try:
        X.export(v)
    except Exception as e:
        print(f'{v}: не вышло — {e}')
    print(flush=True)
