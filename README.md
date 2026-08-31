# Сайт продажи серверов

Минималистичный лендинг на Flask: каталог тарифов, форма заявки, защищённая
паролем админка со списком заявок (SQLite).

## Запуск локально

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python generate_admin_hash.py   # придумайте пароль, скопируйте хэш
copy .env.example .env          # впишите SECRET_KEY и ADMIN_PASSWORD_HASH

python run.py
```

Откройте http://127.0.0.1:5000 — каталог тарифов и форма заявки.
Админка: http://127.0.0.1:5000/admin/login.

`SECRET_KEY` — любая длинная случайная строка (например,
`python -c "import secrets; print(secrets.token_hex(32))"`).

## Что редактировать под себя

- Тарифы и цены — таблица `servers` в `app/db.py` (переменная `SEED_SERVERS`),
  либо руками в файле `instance/shop.sqlite3`.
- Тексты на главной — `app/templates/index.html`.
- Цвета/стили — `app/static/css/style.css`.

## Деплой на Render.com

1. Залейте этот проект в свой репозиторий на GitHub.
2. На render.com: **New → Web Service**, подключите репозиторий.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn run:app` (уже указано в `Procfile`, Render подхватит сам)
5. В разделе Environment добавьте переменные:
   - `SECRET_KEY` — `python -c "import secrets; print(secrets.token_hex(32))"`
   - `ADMIN_PASSWORD_HASH` — вывод `python generate_admin_hash.py`
6. Deploy. Render выдаст публичный адрес вида `https://your-app.onrender.com`.

**Важно про базу данных:** на бесплатном плане Render диск не постоянный —
при каждом передеплое или перезапуске сервиса файл `instance/shop.sqlite3`
(и заявки в нём) обнуляется. Для лендинга на старте это не критично, но
если заявки должны накапливаться надёжно — потребуется platform disk
(платный план) или переезд на управляемую БД (например, бесплатный
Postgres от Render). Скажите, когда это станет актуально — подключим.

Когда появится нагрузка или понадобится автоматизация — переезд на свой
VPS (gunicorn + nginx) не потребует переписывать приложение.
