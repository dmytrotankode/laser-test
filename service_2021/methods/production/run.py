"""Метод "виробничий" (Метод 1) - тонка CLI-обгортка навколо вже існуючого
pipeline/generate.py, ЗАРАДИ ОДНОРІДНОСТІ: щоб цей метод запускався і
відповідав ТОЧНО так само, як майбутні зовнішні методи (окремий процес,
--variant/--in/--out), а не викликався напряму як єдиний виняток - саме
так просив користувач ("хочу щоб наш метод теж подібним чином працював").

pipeline/generate.py САМ не чіпається - ця обгортка лише читає аргументи й
викликає generate.generate(), як і раніше робив app.py.

Контракт (той самий для БУДЬ-ЯКОГО методу, зовнішнього чи цього):
    python run.py --variant <ім'я> --in <папка з фото/калібруванням, може
                  бути порожньою для методів, що працюють через архів,
                  як цей) --out <куди покласти готовий .LS>
    Код виходу 0 = успіх, .LS реально лежить за шляхом --out.
    Ненульовий код виходу + текст помилки в stderr = провал.

variant тут - це ім'я в archive/<variant>/ (generate() сам звідти читає
фото), --in ігнорується: виробничий метод залежить від ВСЬОГО архіву
(підбір найближчого сусіда), не лише від файлів одного набору - на
відміну від самодостатніх методів, яким --in і потрібен.
"""
import argparse
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SERVICE_ROOT = os.path.abspath(os.path.join(BASE, '..', '..'))
sys.path.insert(0, SERVICE_ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variant', required=True)
    ap.add_argument('--in', dest='in_dir', default=None)
    ap.add_argument('--out', required=True)
    ap.add_argument('--recipe', default='production_2026-08-27')
    args = ap.parse_args()

    from pipeline import generate as gen
    ls_path, report = gen.generate(args.variant, args.recipe)
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    shutil.copyfile(ls_path, args.out)
    if report:
        print(f'report: {report}', file=sys.stderr)
    print(args.out)


if __name__ == '__main__':
    main()
