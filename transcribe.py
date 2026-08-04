"""Транскрибация видео-ответов с производства (Whisper API).

Ключ НЕ хранится в этом файле. Скрипт читает его из переменной окружения
OPENAI_API_KEY. Запуск:

    setx OPENAI_API_KEY "sk-..."          # один раз, потом перезапустить терминал
    python transcribe.py video1.MOV video2.MOV

Или разово, без сохранения в системе:

    OPENAI_API_KEY="sk-..." python transcribe.py video1.MOV video2.MOV

Язык по умолчанию — украинский (речь на производстве украинская, местами
с русскими вкраплениями). Переопределяется флагом:

    python transcribe.py --lang ru video1.MOV
    python transcribe.py --lang auto video1.MOV   # отдать определение Whisper

Результат: рядом с каждым видео появится <имя>.txt — обычный текст с таймкодами.
Аудио извлекается локально через ffmpeg в mono 16 кГц (это в разы меньше файл,
чем видео, и укладывается в лимит 25 МБ на запрос).
"""
import os
import sys
import json
import shutil
import subprocess
import urllib.request

API = "https://api.openai.com/v1/audio/transcriptions"
MODEL = "whisper-1"
LIMIT_MB = 24
DEFAULT_LANG = "uk"

# Подсказка задаёт Whisper и язык, и терминологию цеха — без неё он сваливается
# в русский и коверкает «шолом», «сопло», «подача».
PROMPT_UK = ("Розмова на виробництві про лазерний робот Fanuc: шолом, сопло, "
             "дистанція від сопла до шолома, програма різання, точка, "
             "швидкість подачі, координати верстата, позиція.")


def extract_audio(video, out_mp3):
    """Достаём дорожку и сразу жмём: моно, 16 кГц, 32 kbps — речи хватает с запасом."""
    cmd = ["ffmpeg", "-y", "-i", video, "-vn",
           "-ac", "1", "-ar", "16000", "-b:a", "32k", out_mp3]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out_mp3):
        raise RuntimeError(f"ffmpeg не смог обработать {video}:\n{r.stderr[-800:]}")
    mb = os.path.getsize(out_mp3) / 1e6
    print(f"  аудио: {mb:.1f} МБ")
    if mb > LIMIT_MB:
        raise RuntimeError(f"файл {mb:.1f} МБ больше лимита {LIMIT_MB} МБ — "
                           f"нужно резать на части")
    return out_mp3


def transcribe(mp3, key, language=DEFAULT_LANG):
    boundary = "----transcribe-boundary-9f2c"
    parts = []

    def field(name, value):
        parts.append(f"--{boundary}\r\n"
                     f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                     f"{value}\r\n".encode())

    field("model", MODEL)
    if language != "auto":               # "auto" — не слать поле, пусть определяет сам
        field("language", language)
    if language in ("uk", "auto"):
        field("prompt", PROMPT_UK)
    field("response_format", "verbose_json")
    field("timestamp_granularities[]", "segment")

    with open(mp3, "rb") as f:
        audio = f.read()
    parts.append(f"--{boundary}\r\n"
                 f'Content-Disposition: form-data; name="file"; '
                 f'filename="{os.path.basename(mp3)}"\r\n'
                 f"Content-Type: audio/mpeg\r\n\r\n".encode())
    parts.append(audio)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(API, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    })
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("Не задан OPENAI_API_KEY. См. комментарий вверху файла.")
    if not shutil.which("ffmpeg"):
        sys.exit("Не найден ffmpeg.")
    args = sys.argv[1:]
    lang = DEFAULT_LANG
    if "--lang" in args:
        i = args.index("--lang")
        if i + 1 >= len(args):
            sys.exit("--lang без значения (например: --lang uk)")
        lang = args[i + 1]
        del args[i:i + 2]
    videos = args
    if not videos:
        sys.exit("Укажи файлы: python transcribe.py video1.MOV video2.MOV")
    print(f"язык: {lang}")

    for v in videos:
        if not os.path.exists(v):
            print(f"{v}: файла нет, пропускаю")
            continue
        print(f"{v}:")
        mp3 = os.path.splitext(v)[0] + ".transcribe.mp3"
        try:
            extract_audio(v, mp3)
            data = transcribe(mp3, key, lang)
        finally:
            if os.path.exists(mp3):
                os.remove(mp3)

        out = os.path.splitext(v)[0] + ".txt"
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"# {os.path.basename(v)}\n\n")
            for s in data.get("segments", []):
                m0, s0 = divmod(int(s["start"]), 60)
                f.write(f"[{m0:02d}:{s0:02d}] {s['text'].strip()}\n")
            if not data.get("segments"):
                f.write(data.get("text", ""))
        print(f"  готово -> {out}")


if __name__ == "__main__":
    main()
