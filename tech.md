# tech.md — ядро проекта «Квіткова Примха»

**Версия ядра: v9** · 2026-08-15

## Changelog

- **v9** — нейтральные цвета раздела 13 переведены в тёплый фиолетовый под логотип: `cream` `#F8F0F7`, `ink` `#2B2429`, `muted` `#6D6069`, `line` `#E7D8E5`, `accentSoft` `#F2E4F1`. Раньше вокруг фиолетового акцента лежала тёплая бежевая гамма, и страница читалась как терракотовая с фиолетовыми кнопками. `accent` не менялся. Тени и затемнение hero пересчитаны на новый `ink`. Замеры на новом фоне: `ink` 13.55:1, `muted` 5.33:1, `accent` 5.04:1, белый на `accent` 5.63:1, `ink` на `accentSoft` 12.36:1, `accent` на `accentSoft` 4.60:1. Последняя пара и определила `accentSoft`: на полтона темнее, `#F0E0EE`, она давала 4.45:1, а чипы фильтров набраны акцентом по этой плашке.
- **v8** — фирменный цвет стал фиолетовым по логотипу. Логотип теперь картинка `static/img/logo.webp`, собранная из `static/img/main.png`: это готовый локап с названием магазина, поэтому рядом с ним в шапке, подвале и мобильной панели больше нет отдельной надписи — название живёт в `alt`. Сам знак нарисован цветом `#A95DA0`, но интерфейсным он быть не может: на кремовом фоне это 4.17:1, под белым текстом 4.41:1, оба ниже порога 4.5:1 этого же раздела 13. Поэтому `accent` — тот же тон и насыщенность, опущенные до светлоты 44%: `#944E8C`, 5.32:1 и 5.63:1. `accentSoft` перекрашен в `#F0E4EF`. Причина замены терракоты: владелец просил вести кнопки и ссылки за цветом вывески.
- **v7** — hero главной раскрыт на всю ширину экрана, текст лёг на фотографии. Причина: веер v6 стоял внутри контейнера `max-w-site` и делил экран с текстом пополам, а нужна подача во весь экран. Раздел 10 переписал абзац о hero, раздел 12 дополнил строку `hero_showcase.html`, раздел 13 назвал hero единственным исключением из правила контейнера. Текст поверх фотографии не держит 4.5:1 сам по себе, поэтому между фотографиями и текстом лежит затемнение, и заголовок на нём белый — контраст проверяется замером пикселей под текстом, а не на глаз.
- **v6** — раздел 12 получил примитив `hero_showcase.html`, раздел 10 переписал абзац о hero главной. Причина: hero был одной фотографией сбоку от текста, а нужна подача нескольких работ — веер карточек в перспективе, текст поверх ближней. Собрать это из существующих примитивов нельзя: `image_simple.html` рисует одну картинку, `card_work.html` — карточку работы со ссылкой, а писать разметку прямо в `pages/home.html` запрещает этот же раздел 12. Геометрия веера живёт классами `.hero-fan*` в `static/css/input.css`: `perspective` и `rotateY` не имеют утилит в Tailwind 3, а значения в квадратных скобках запрещены разделом 2. Наклон за курсором — Alpine-компонент `heroFan` в `static/js/app.js`, по образцу `lazyMap`. Схема БД, контракты задач, URL и раздел 12.1 не затронуты: новых идентификаторов нет, фотографии берутся из `SiteSettings.hero_image` и `Occasion.cover`.
- **v5** — магазин называется «Квіткова Примха», проект переименован. Название не переводится: на `/ru/` оно то же, что на вывеске. Сид перестал угадывать имя и адрес — `SiteSettings` получает название, адрес (вул. Дворецька, 125, Рівне) и обе ссылки Google Maps, а фолбэк названия в `locale/` совпадает с вывеской. Причина: сайт представлялся условной «Квітковою майстернею», а карта не показывалась нигде — `map_embed_url` и `map_directions_url` оставались пустыми, хотя блок карты на главной и в контактах ждал их с самого начала. Контракты разделов 4.7, 10 и 12 не менялись.
- **v4** — `empty_state.html` получил параметр `level`. Причина: на страницах, где пустое состояние занимает всю страницу (`/dyakuyemo/`, `404`, `410`), заголовок обязан быть первого уровня, а примитив рисовал только `h2`, и эти страницы уходили вовсе без `h1` вопреки разделу 12 FRONTEND.md и чек-листу раздела 15.
- **v3** — правки по разделу 17 `FRONTEND.md`. Раздел 13 получил `fontFamily`, `fontSize`, `spacing.section`/`section-lg`, `maxWidth.content`, `maxHeight.drawer`, `width.filters`, `ringOffsetColor`; `muted` и `accent` затемнены до `#6E675F` и `#9E4E3F` ради порога контраста 4.5:1. Раздел 12: параметр `priority` у `picture.html`, закрытый перечень `tone`, `cookie_banner.html` перенесён в `layout/`, добавлен подраздел 12.1 с контрактами DOM. Раздел 3: `layout/orders_paused.html`, `partials/gallery_cards.html`, `pages/kitchen_sink.html`. Раздел 4.3: `occasion` в зарезервированных именах. Раздел 9: `/hx/gallery/` принимает `occasion`, адрес после HTMX-фильтрации ставится заголовком `HX-Push-Url` с сервера. Раздел 16: бюджет 60 КБ gzip на CSS и JS, ориентир INP.
- **v2** — ревизия по итогам сквозной проверки. Существенное: задачи Celery получили явные имена, отправка в Telegram вынесена из транзакции; `Review` получил поля уведомления и антиспама; оригиналы изображений переехали в непубличное хранилище; рендишены генерируются только для фото работ; добавлены `tr_html`, cookie-согласие, эндпоинты `/hx/lead/`, `/hx/review/`, `/hx/favorites/`, `/healthz/`, код 410 для архива; сортировка галереи задана точными ключами; masonry заменён на сетку с фиксированной пропорцией; `PostCategory` и `season_hint` удалены; зафиксированы часовой пояс, кэш галереи, лимит избранного, поведение при лимитах.
- **v1** — первичная фиксация.

> Этот файл — единственный источник истины. Любая сессия читает его первым и подчиняется дословно.
> Контракты (модели, поля, слаги, payload задач, формат URL, набор компонентов) не выдумываются.
> Не хватает контракта — блок `CONTRACT GAP`, апдейт этого файла, бамп версии. Порядок в разделе 21.
> Файл меняется только append-only. Каждое изменение контракта бампает версию и дописывает строку в changelog.

---

## 1. Проект

**Что делает.** Сайт-витрина цветочной мастерской. Владелец публикует свои работы (букеты, композиции, оформление залов) с фотографиями. Клиент листает галерею, фильтрует по поводу, типу изделия и цвету, находит подходящую работу и связывается по телефону, в Viber или Telegram. Продажа происходит вне сайта, в разговоре.

**Для кого.** Клиенты одного города, ищут флориста под конкретное событие. Основной трафик — мобильные устройства и переходы из Instagram.

**Цель.** Максимум обращений (звонок, сообщение в мессенджер, заявка с формы) на посетителя.

**Не-цели v1.** Нет корзины, онлайн-оплаты, личных кабинетов клиентов, складского учёта, доставки в другие города, вариантов размера у работы, пакетного импорта архива фотографий.

**Ключевые ограничения.**

- Наполняет сайт один человек, не технический. Админка обязана быть быстрой и понятной, добавление работы с телефона — не более минуты. Работы добавляются вручную по одной, пакетный импорт не требуется.
- Цены на сайте не показываются в v1, но модель данных для цен закладывается сразу и включается галочкой без изменения кода. Фильтра по бюджету и сортировки по цене в v1 нет.
- Языки: украинский (основной) и русский.
- Разработчик один, он же лид. Ревью самого себя механическое, по чек-листу.

**Решение по поводам.** Повод — это **раздел каталога**, а не фильтр в query. Он живёт в пути URL, потому что должен индексироваться как отдельная посадочная страница. В панели фильтров повод присутствует первым блоком, но его пункты — обычные ссылки на `/galereya/<slug>/`, а не чекбоксы.

**Решение по защите изображений.** Водяной знак — мера от перепубликации в чужих аккаунтах, не защита от скачивания. Оригиналы недоступны публично, но рендишен с водяным знаком скачать можно, и это принимается.

---

## 2. Стек

| Слой | Технология | Назначение |
|---|---|---|
| Язык | Python 3.12 | |
| Фреймворк | Django 5.x | Сервер, ORM, админка, i18n |
| БД | PostgreSQL 16 | Данные. Файлы изображений в БД **не** хранятся |
| Кэш, брокер, счётчики | Redis 7 | Celery broker/backend, кэш, rate limiting, счётчики просмотров |
| Очередь | Celery 5 + Celery beat | Уведомления, генерация превью, периодические задачи |
| Валидация и конфиг | pydantic 2 + pydantic-settings | Конфиг из env, payload задач Celery, DTO внешних клиентов |
| Шаблоны | Django templates | Серверный рендер, полный SEO |
| Интерактив | HTMX 2 + Alpine.js 3 | Фильтры без перезагрузки, панели, лайтбокс |
| Стили | Tailwind CSS 3, **standalone CLI** (бинарник в образе) | Без `django-tailwind`, без Node в рантайме |
| Изображения | Pillow, pillow-avif-plugin, **pillow-heif** | Рендишены AVIF/WebP, чтение HEIC с айфона, водяной знак |
| Файлы | Django `STORAGES` + django-storages | Диск VPS в v1, S3 сменой конфига |
| Админка | django-unfold + django-admin-sortable2 | Современная тема, работает с телефона, сортировка перетаскиванием |
| Телефоны | django-phonenumber-field | Валидация формата |
| Разметка контента | django-tinymce + bleach | Текстовые страницы и блог для нетехнического владельца |
| Тесты | pytest, pytest-django, pytest-cov, hypothesis, playwright | |
| Качество | ruff (lint + format), mypy + django-stubs | |
| Контейнеры | Docker, Docker Compose | |
| Прод | nginx, gunicorn, Cloudflare | |
| CI/CD | GitHub Actions | Гейт на PR, деплой на мёрдж в main |

Репозиторий — GitHub, ветка `main` защищена.

### Явные запреты стека

- Бинарные изображения в PostgreSQL — запрещено. В БД только путь и метаданные.
- Прямая работа с файловой системой через `open()` в коде приложения — запрещено. Только storage-объекты и `FieldFile`.
- Инлайн-JS в шаблонах, кроме атрибутов Alpine (`x-data`, `@click`) и HTMX (`hx-*`).
- Самописный UI там, где есть примитив из раздела 12.
- Произвольные значения Tailwind (`text-[13px]`, `max-w-[1280px]`) в шаблонах — только токены из раздела 13.

---

## 3. Структура папок

```
flowers/
├── CLAUDE.md
├── tech.md
├── DEV.md
├── compose.yaml                  # dev
├── compose.prod.yaml
├── Dockerfile
├── .env.example
├── pyproject.toml
├── tailwind.config.js
├── config/
│   ├── settings_schema.py        # pydantic-settings, единственная точка чтения env
│   ├── settings.py
│   ├── storages.py               # public_storage, private_storage
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── core/
│   │   ├── models.py             # SiteSettings, StaticPage, HowToStep
│   │   ├── admin.py
│   │   ├── views.py              # home, contacts, static_page, thanks, healthz, kitchen_sink
│   │   ├── navigation.py         # пункты меню данными
│   │   ├── context_processors.py
│   │   ├── contracts.py          # EmptyPayload
│   │   ├── exceptions.py         # TransientError
│   │   ├── tasks.py              # expire_banner
│   │   ├── services/
│   │   │   ├── images.py         # одноразовое сжатие простых изображений
│   │   │   └── sanitize.py       # bleach
│   │   ├── templatetags/
│   │   │   └── project.py        # tr, tr_html, rendition
│   │   ├── sitemaps.py
│   │   └── tests/
│   ├── catalog/
│   │   ├── models.py             # Occasion, TagGroup, Tag, Work, WorkImage, WorkImageRendition
│   │   ├── admin.py
│   │   ├── views.py              # gallery, hx_gallery, work_detail, favorites, hx_favorites, search
│   │   ├── filters.py            # разбор и нормализация query
│   │   ├── seo.py                # robots_directive, canonical
│   │   ├── cache.py              # версионный ключ галереи
│   │   ├── services/
│   │   │   ├── images.py         # рендишены и водяной знак, PRESETS_VERSION
│   │   │   ├── similar.py
│   │   │   └── views_counter.py
│   │   ├── contracts.py
│   │   ├── tasks.py
│   │   └── tests/
│   ├── leads/
│   │   ├── models.py
│   │   ├── forms.py
│   │   ├── views.py              # hx_lead
│   │   ├── contracts.py
│   │   ├── tasks.py
│   │   ├── services/
│   │   │   ├── ratelimit.py
│   │   │   └── antispam.py
│   │   └── tests/
│   ├── reviews/
│   └── blog/
├── clients/
│   ├── base.py                   # протоколы
│   ├── dto.py                    # pydantic DTO
│   ├── telegram.py
│   ├── turnstile.py
│   ├── fakes.py
│   └── factory.py
├── templates/
│   ├── base.html
│   ├── 404.html
│   ├── 410.html
│   ├── 500.html                  # самостоятельный, без наследования base.html
│   ├── layout/                   # header, footer, banner, mobile_menu, cookie_banner
│   │                             # + orders_paused.html — полоса «не приймаємо замовлення»
│   ├── ui/                       # примитивы, раздел 12
│   ├── pages/                    # + kitchen_sink.html — рендер примитивов, только при DEBUG=True
│   └── partials/                 # ответы HTMX-эндпоинтов
│       ├── gallery_grid.html     # полный ответ /hx/gallery/: сетка + OOB-блоки
│       └── gallery_cards.html    # только карточки, для догрузки «Показати ще»
├── static/
│   ├── css/
│   ├── js/                       # htmx.min.js, alpine.min.js, app.js, favorites.js, analytics.js
│   └── img/
├── locale/{uk,ru}/LC_MESSAGES/
├── media/                        # dev; в проде тома: media-public, media-private
├── scripts/seed.py
├── deploy/{nginx.conf,deploy.sh,README.md}
└── tests/{conftest.py,factories.py,stubs.py,e2e/}
```

**Правило именования.** Приложения — существительные во множественном числе латиницей. Слаги в URL — украинская транслитерация латиницей (`galereya`, `vesillya`, `pro-nas`). Имена в коде, комментариях и коммитах — английские.

---

## 4. Схема БД

Замороженный контракт. Поля не переименовываются и не удаляются без бампа версии ядра.

Общее для моделей с переводами: пара полей `<field>_uk` и `<field>_ru`. Украинское обязательное, русское может быть пустым — тогда показывается украинское. Доступ только через миксин раздела 11.

Общее правило для полей сортировки: везде `PositiveSmallIntegerField, default=0`.

### 4.1 `catalog.Occasion` — повод (раздел каталога, плитка на главной)

| Поле | Тип | Примечание |
|---|---|---|
| `slug` | SlugField(60), unique | В URL: `/galereya/vesillya/` |
| `name_uk`, `name_ru` | CharField(100) | |
| `description_uk`, `description_ru` | TextField, blank | SEO-текст внизу страницы раздела |
| `cover` | ImageField(upload_to='occasions/', storage=public), blank | Фото плитки |
| `order` | PositiveSmallIntegerField, default 0 | |
| `is_active` | Boolean, default True | |
| `show_on_home` | Boolean, default True | |
| `seo_title_uk/ru` | CharField(200), blank | |
| `seo_description_uk/ru` | CharField(300), blank | |
| `created_at`, `updated_at` | DateTime auto | |

Начальный набор (сид, дальше владелец добавляет сам): `podarunok`, `vesillya`, `yuvilei`, `den-narodzhennya`, `korporatyv`, `traurni`, `oformlennya-zaly`.

Meta: `ordering = ['order', 'id']`; indexes: `(is_active, order)`.

### 4.2 `catalog.TagGroup` — группа фильтров

| Поле | Тип | Примечание |
|---|---|---|
| `slug` | SlugField(40), unique | Совпадает с именем query-параметра |
| `name_uk`, `name_ru` | CharField(100) | |
| `filter_kind` | CharField choices: `checkbox`, `color_swatch` | |
| `order` | PositiveSmallIntegerField, default 0 | |
| `is_active` | Boolean, default True | |

Набор групп v1: `type` (тип виробу), `color` (колір, `color_swatch`), `flower` (квіти), `season` (сезон). Новая группа — изменение контракта, бамп версии.

### 4.3 `catalog.Tag` — значение фильтра

| Поле | Тип | Примечание |
|---|---|---|
| `group` | FK → TagGroup, related_name='tags', PROTECT | |
| `slug` | SlugField(60), unique **глобально** | Значение query-параметра |
| `name_uk`, `name_ru` | CharField(100) | |
| `color_hex` | CharField(7), blank | Только для группы `color` |
| `order` | PositiveSmallIntegerField, default 0 | |
| `is_active` | Boolean, default True | |

Глобальная уникальность слага обязательна: по слагу однозначно определяется группа.

Валидация в `clean()`:

- у группы `color_swatch` поле `color_hex` обязательно, у остальных пустое;
- слаг тега не совпадает ни с одним `TagGroup.slug` и ни с одним зарезервированным именем параметра: `sort`, `page`, `q`, `a`, `occasion`.

`occasion` зарезервирован, хотя на публичном URL повод живёт в пути: этим именем форма фильтров передаёт слаг текущего раздела в `/hx/gallery/` (раздел 9).

### 4.4 `catalog.Work` — работа

| Поле | Тип | Примечание |
|---|---|---|
| `article` | PositiveIntegerField, unique, editable=False | Номер работы из последовательности `work_article_seq`, старт 100. Не переиспользуется и не меняется никогда |
| `slug` | SlugField(200), unique, editable=False | `<article>-<translit(title_uk)[:180]>`; при пустом заголовке `<article>`. **Вычисляется один раз при первом сохранении и далее не меняется** — ссылки не должны ломаться |
| `title_uk`, `title_ru` | CharField(200), blank | Необязательно |
| `description_uk`, `description_ru` | TextField, blank | 1–2 предложения |
| `composition_uk`, `composition_ru` | CharField(300), blank | «троянди, евкаліпт, гіпсофіла» |
| `size_text_uk`, `size_text_ru` | CharField(100), blank | «висота 45 см» |
| `occasions` | M2M → Occasion, related_name='works', blank | |
| `tags` | M2M → Tag, related_name='works', blank | |
| `price_from`, `price_to` | Decimal(10,2), null | |
| `currency` | CharField(3), default `UAH` | Зарезервировано, в UI v1 не используется |
| `price_visible` | Boolean, default False | |
| `price_note_uk`, `price_note_ru` | CharField(200), blank | |
| `cost` | Decimal(10,2), null | Закупка. **Только админка. В шаблоны не передаётся никогда** |
| `status` | CharField choices: `draft`, `published`, `archived`, default `draft` | Удаления нет |
| `is_pinned` | Boolean, default False | |
| `order` | PositiveSmallIntegerField, default 0 | |
| `views_count` | PositiveIntegerField, default 0 | Сливается из Redis раз в 5 минут |
| `published_at` | DateTime, null | Ставится при первом переходе в `published` |
| `seo_title_uk/ru`, `seo_description_uk/ru` | CharField, blank | |
| `created_at`, `updated_at` | DateTime auto | |

Meta:

- `ordering = ['-is_pinned', 'order', F('published_at').desc(nulls_last=True), '-id']`
- indexes: `(status, published_at)`, `(status, is_pinned, order)`
- constraint `price_range_valid`: `price_to IS NULL OR price_from IS NULL OR price_to >= price_from`

Менеджеры: `objects` (все), `published` (`status='published'`, `published_at <= now`).

**Публикация без фотографий запрещена.** Проверка живёт в админке (`WorkImageInline.clean()` формсета и `WorkAdmin.save_related`), где изображения уже известны. В `Work.clean()` эту проверку **не** делать: инлайны сохраняются после родителя, и `clean()` всегда видел бы ноль фотографий.

**Цены.** Показ цены = `SiteSettings.prices_enabled AND work.price_visible AND price_from is not None`. Пока флаг выключен, цена не рендерится нигде. Фильтра по бюджету и сортировки по цене в v1 нет ни при каком значении флага.

### 4.5 `catalog.WorkImage` — фотография работы

| Поле | Тип | Примечание |
|---|---|---|
| `work` | FK → Work, related_name='images', CASCADE | |
| `image` | ImageField(upload_to='works/%Y/%m/', **storage=private_storage**, width_field='width', height_field='height') | Оригинал. Публично не раздаётся |
| `width`, `height` | PositiveIntegerField | |
| `alt_uk`, `alt_ru` | CharField(200), blank | Пусто — генерируется из заголовка работы и повода |
| `order` | PositiveSmallIntegerField, default 0 | Сортировка перетаскиванием |
| `is_main` | Boolean, default False | Ровно одна на работу |
| `renditions_ready` | Boolean, default False | |
| `renditions_version` | CharField(64), blank | Хеш сохранённого файла плюс версия пресетов |
| `created_at` | DateTime auto | |

Constraint: `UniqueConstraint(fields=['work'], condition=Q(is_main=True), name='one_main_image_per_work')`.

Правила:

- Первая загруженная фотография работы автоматически становится главной.
- При удалении главной фотографии главной становится первая по `order` среди оставшихся.
- У опубликованной работы минимум одна фотография (проверка в админке, см. 4.4).
- Верхнего лимита нет, рекомендованные 3–6 ракурсов.

### 4.6 `catalog.WorkImageRendition` — производное изображение

| Поле | Тип | Примечание |
|---|---|---|
| `source` | FK → WorkImage, related_name='renditions', CASCADE | |
| `preset` | CharField choices: `thumb`, `card`, `large`, `og` | |
| `image_format` | CharField choices: `avif`, `webp`, `jpeg` | |
| `file` | ImageField(upload_to=`renditions/%Y/%m/`, storage=public_storage) | Имя файла: `{source_id}_{preset}_{renditions_version}.{ext}` |
| `width`, `height`, `bytes` | PositiveIntegerField | |

Constraint: `UniqueConstraint(fields=['source', 'preset', 'image_format'])`.

| Пресет | Размер | Использование |
|---|---|---|
| `thumb` | 400px по длинной стороне | Сетка на мобильном, похожие работы |
| `card` | 800px | Сетка на ПК |
| `large` | 1600px | Лайтбокс, карточка работы |
| `og` | 1200×630, crop по центру | Превью ссылки в мессенджерах |

Форматы: `avif` (основной) и `webp` (фолбэк) для всех пресетов; дополнительно `jpeg` только для `og`, потому что часть мессенджеров не понимает avif и webp в превью.

Водяной знак накладывается **только на рендишены**, оригинал остаётся чистым и непубличным.

**Имя файла обязано содержать `renditions_version`.** Иначе после перегенерации Cloudflare год отдаёт старую картинку из-за `immutable` в заголовках кэша.

### 4.7 `core.SiteSettings` — настройки сайта, singleton (pk=1)

- **Контакты:** `phone_primary` (PhoneNumberField), `phone_secondary`, `email`, `viber_url`, `telegram_url`, `instagram_url`, `facebook_url` (blank)
- **Адрес:** `address_uk/ru`, `landmark_uk/ru`, `parking_uk/ru`, `map_embed_url` (URLField 500), `map_directions_url` (URLField 500)
- **Режим работы:** `working_hours_uk/ru` (TextField)
- **Приём заказов:** `accepting_orders` (Boolean, default True), `not_accepting_message_uk/ru` (CharField 300)
- **Баннер:** `banner_enabled` (Boolean), `banner_text_uk/ru` (CharField 300), `banner_url` (blank), `banner_until` (DateTime, null)
- **Цены:** `prices_enabled` (Boolean, default False)
- **Водяной знак:** `watermark_image` (ImageField, blank, PNG с прозрачностью), `watermark_opacity` (Float 0..1, default 0.35), `watermark_position` (choices `bottom_right`, `bottom_left`, `center`), `watermark_scale` (Float, доля ширины, default 0.18)
- **SEO и аналитика:** `og_default_image`, `analytics_ga_id` (CharField, blank), `site_name_uk/ru`
- **Главная:** `hero_title_uk/ru`, `hero_subtitle_uk/ru`, `hero_image`

Правила:

- `save()` жёстко ставит `pk=1`, `delete()` запрещён, в админке скрыты кнопки добавления и удаления.
- Читается только через `SiteSettings.load()` — кэш в Redis, ключ `site_settings:v1`, TTL 3600, инвалидация в `post_save`. **Недоступный Redis не ломает сайт: читается напрямую из базы.**
- В шаблоны попадает контекст-процессором `core.context_processors.site_settings`.
- Баннер показывается при `banner_enabled AND (banner_until is null OR banner_until > now)`.

### 4.8 `core.StaticPage`

`slug` (unique), `title_uk/ru`, `body_uk/ru` (HTML из tinymce, санитизируется bleach при сохранении), `seo_title_uk/ru`, `seo_description_uk/ru`, `is_published`, `updated_at`.

Фиксированные слаги из сида: `pro-nas`, `dostavka-i-oplata`, `faq`, `polityka-konfidentsiynosti`.

Разрешённые теги bleach: `p, br, strong, em, u, ul, ol, li, h2, h3, h4, a, img, blockquote, table, thead, tbody, tr, th, td, hr`. Атрибуты: `href`, `title`, `target`, `rel`, `src`, `alt`, `width`, `height`. Протоколы: `http`, `https`, `mailto`, `tel`.

### 4.9 `core.HowToStep`

`order`, `title_uk/ru`, `text_uk/ru`, `icon` (имя иконки из спрайта), `is_active`.

### 4.10 `reviews.Review`

| Поле | Тип | Примечание |
|---|---|---|
| `author_name` | CharField(100) | |
| `text_uk`, `text_ru` | TextField, blank | Минимум одно заполнено, проверяется в `clean()` |
| `rating` | PositiveSmallIntegerField, null | |
| `photo` | ImageField(storage=public), blank | |
| `work` | FK → Work, null, SET_NULL | |
| `source` | CharField choices: `admin`, `site` | |
| `status` | CharField choices: `pending`, `published`, `rejected`, default `pending` | С сайта — `pending`, из админки — сразу `published` |
| `contact_phone` | PhoneNumberField, blank | Публично не показывается |
| `is_featured` | Boolean, default False | Показ на главной |
| `consent` | Boolean | Согласие на обработку данных, для `source='site'` обязательно True |
| `ip_hash` | CharField(64), blank | |
| `user_agent` | CharField(300), blank | Обрезается при сохранении |
| `notified_at` | DateTime, null | Основа идемпотентности уведомления |
| `notify_attempts` | PositiveSmallIntegerField, default 0 | |
| `created_at` | DateTime auto | |
| `published_at` | DateTime, null | Ставится при первом переходе в `published` |

Constraint `review_rating_range`: `rating IS NULL OR rating BETWEEN 1 AND 5`.

Публично отдаются только `status='published'`.

### 4.11 `blog.Post`

`slug` (unique), `title_uk/ru`, `excerpt_uk/ru` (CharField 300), `body_uk/ru` (HTML tinymce + bleach), `cover` (ImageField, storage=public), `related_works` (M2M → Work, blank), `status` (`draft`/`published`), `published_at` (null), `views_count` (PositiveIntegerField, default 0), `seo_title_uk/ru`, `seo_description_uk/ru`, `created_at`, `updated_at`.

Категорий у блога в v1 нет.

### 4.12 `leads.Lead`

| Поле | Тип | Примечание |
|---|---|---|
| `name` | CharField(100) | |
| `phone` | PhoneNumberField, region `UA` | |
| `preferred_contact` | CharField choices: `phone`, `viber`, `telegram`, default `phone` | |
| `event_date` | DateField, null | |
| `budget_text` | CharField(50), blank | Свободный текст |
| `comment` | CharField(1000), blank | |
| `work` | FK → Work, null, SET_NULL | |
| `work_article` | PositiveIntegerField, null | Снимок номера |
| `favorites_articles` | JSONField, default list | Номера из избранного, максимум 50 |
| `status` | CharField choices: `new`, `in_progress`, `done`, `spam`, default `new` | |
| `source_url` | URLField(500), blank | |
| `ip_hash` | CharField(64) | `sha256(ip + соль)`. Сырой IP не хранится |
| `user_agent` | CharField(300), blank | Обрезается при сохранении |
| `consent` | Boolean | Обязательно True |
| `notified_at` | DateTime, null | |
| `notify_attempts` | PositiveSmallIntegerField, default 0 | |
| `created_at` | DateTime auto, index | |

Meta: `ordering = ['-created_at']`; index `(status, created_at)`.

Заявки не удаляются автоматически.

---

## 5. Миграции и последовательность артикулов

- Миграции генерируются из моделей, просматриваются построчно и коммитятся **отдельным коммитом** `chore(<app>): add migration for <что>`.
- CI-гейт содержит `makemigrations --check --dry-run`. Расхождение — красный билд.
- В деплое миграции применяются отдельным шагом до перезапуска приложения.
- Последовательность артикулов создаётся миграцией:

```sql
CREATE SEQUENCE IF NOT EXISTS work_article_seq START WITH 100 INCREMENT BY 1;
```

`Work.save()` при первом сохранении берёт `nextval('work_article_seq')`. Номер не возвращается при откате транзакции — это штатное поведение последовательности и здесь оно желаемое.

---

## 6. Конфигурация: pydantic-settings

`config/settings_schema.py` — единственное место чтения переменных окружения. `os.environ` и `os.getenv` в остальном коде запрещены.

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # core
    secret_key: SecretStr
    debug: bool = False
    allowed_hosts: list[str] = ["localhost"]
    site_url: AnyHttpUrl
    time_zone: str = "Europe/Kyiv"
    use_tz: bool = True

    # db / redis / celery
    database_url: PostgresDsn
    redis_url: RedisDsn
    celery_broker_url: RedisDsn
    celery_result_backend: RedisDsn

    # telegram
    telegram_bot_token: SecretStr | None = None
    telegram_chat_id: str | None = None
    telegram_enabled: bool = False       # False → фейковый клиент

    # turnstile
    turnstile_site_key: str | None = None
    turnstile_secret_key: SecretStr | None = None
    turnstile_enabled: bool = False      # False → верификатор пропускает всё

    # antispam
    lead_rate_per_ip_hour: int = 5
    lead_rate_global_day: int = 20
    review_rate_per_ip_hour: int = 2
    review_rate_global_day: int = 20
    form_min_fill_seconds: int = 3
    ip_hash_salt: SecretStr

    # media
    media_backend: Literal["local", "s3"] = "local"
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_access_key: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def split_hosts(cls, v):
        # pydantic-settings ждёт JSON для list[str]; принимаем и строку с запятыми
        if isinstance(v, str):
            return [h.strip() for h in v.split(",") if h.strip()]
        return v
```

`settings.py` импортирует `settings = Settings()` и раскладывает по переменным Django. Ошибка валидации на старте роняет процесс.

`.env.example` содержит все ключи с безопасными значениями. Проект обязан подниматься командой `cp .env.example .env && docker compose up` без реальных секретов: Telegram и Turnstile выключены, работают фейки. `IP_HASH_SALT` в примере — заглушка; замена на уникальное значение входит в чек-лист перед запуском.

### Хранилища

```python
STORAGES = {
    "default": {...},   # public:  /srv/media-public,  раздаётся nginx
    "private": {...},   # private: /srv/media-private, nginx не раздаёт
    "staticfiles": {...},
}
```

`WorkImage.image` использует `private`. Всё остальное — `default`.

---

## 7. Внешние клиенты: интерфейс, реальный, фейк

`clients/base.py` — протоколы. Выбор реализации в `clients/factory.py` по флагам конфига.

```python
class TelegramClient(Protocol):
    def send_message(self, payload: TelegramMessage) -> TelegramSendResult: ...

class TurnstileVerifier(Protocol):
    def verify(self, token: str, remote_ip: str | None) -> TurnstileResult: ...
```

`clients/dto.py`:

```python
class TelegramMessage(BaseModel):
    chat_id: str
    text: str = Field(max_length=4096)
    parse_mode: Literal["HTML"] = "HTML"
    disable_web_page_preview: bool = True

class TelegramSendResult(BaseModel):
    ok: bool
    message_id: int | None = None
    error: str | None = None

class TurnstileResult(BaseModel):
    success: bool
    error_codes: list[str] = []
```

`FakeTelegramClient` складывает сообщения в список и **валидирует вход той же pydantic-моделью**: если код шлёт мусор, фейк падает. Режимы `fail_with(status)` и `timeout()` для проверки пути ошибки.

Реальный клиент: таймаут 10 секунд, сетевые ошибки и коды 5xx поднимают `core.exceptions.TransientError`, коды 4xx — обычное исключение без ретраев.

Разработка идёт против фейков с первого дня. Реальный токен бота не блокирует ни одну задачу.

---

## 8. Контракты Celery

Правила для всех задач:

1. **Явное имя.** `@shared_task(name="catalog.generate_renditions", bind=True, ...)`. Автогенерируемое имя содержало бы префикс `apps.` и разошлось бы с расписанием beat.
2. Задача принимает **один именованный аргумент `payload: dict`** и первым делом парсит его в pydantic-модель из `contracts.py`. Вызов: `task.apply_async(kwargs={"payload": {...}})`. Позиционные аргументы и передача объектов моделей запрещены.
3. Каждая задача **идемпотентна**: повторный запуск с тем же payload даёт ровно один эффект.
4. Ретраи: `autoretry_for=(TransientError,)`, `retry_backoff=True`, `retry_backoff_max=600`, `max_retries=5`, `retry_jitter=True`. Ошибка валидации payload не транзиентная и не ретраится.
5. Очереди: `default` (уведомления) и `media` (обработка изображений).
6. Постановка задачи только через `transaction.on_commit`.

### 8.1 `leads.notify_new_lead` — очередь `default`

```python
class LeadNotificationPayload(BaseModel):
    lead_id: int = Field(gt=0)
```

**Три фазы, сетевой вызов вне транзакции:**

1. Транзакция №1: `select_for_update()` по заявке. Если `notified_at` не пуст или `status == 'spam'` — выход. Иначе `notify_attempts += 1`, коммит.
2. Вне транзакции: отправка сообщения.
3. Транзакция №2: `notified_at = now()`.

Держать сетевой вызов с таймаутом 10 секунд внутри блокировки строки нельзя: это и долгая блокировка, и риск дубля при откате.

Текст сообщения: имя, телефон **отдельной строкой в `<code>`** (Telegram не поддерживает схему `tel:` в ссылках, тапом по `<code>` номер копируется), предпочтительный канал, дата события, бюджет, номер работы, номера из избранного, комментарий, ссылка на заявку в админке.

### 8.2 `catalog.generate_renditions` — очередь `media`

```python
class RenditionsPayload(BaseModel):
    work_image_id: int = Field(gt=0)
    force: bool = False
```

Идемпотентность: `renditions_version = sha256(сохранённый файл)[:32] + ":" + PRESETS_VERSION`. Совпадает с сохранённым значением, `renditions_ready` True и `force` False — выход без работы. Иначе старые рендишены удаляются вместе с файлами, генерируются новые, ставится новая версия.

`PRESETS_VERSION` — константа в `catalog/services/images.py`. Изменили пресеты или водяной знак — бампнули константу.

### 8.3 `catalog.flush_view_counters` — периодическая, каждые 5 минут

Payload — `core.contracts.EmptyPayload`. Забирает ключи `views:work:*` и `views:post:*` через `GETDEL`, применяет `F('views_count') + n` пачкой. Идемпотентна по построению.

### 8.4 `catalog.regenerate_all_renditions` — ручная, очередь `media`

```python
class RegenerateAllPayload(BaseModel):
    force: bool = False
    work_id: int | None = None
```

Раскидывает `generate_renditions`. Кнопка в админке после смены водяного знака.

### 8.5 `core.expire_banner` — периодическая, раз в час

Payload — `EmptyPayload`. Снимает `banner_enabled` у единственной записи `SiteSettings`, если `banner_until` в прошлом. Рендер и так проверяет дату; задача нужна, чтобы владелец видел в админке актуальное состояние галочки. Идемпотентна.

### 8.6 `reviews.notify_new_review` — очередь `default`

```python
class ReviewNotificationPayload(BaseModel):
    review_id: int = Field(gt=0)
```

Три фазы через `notified_at` и `notify_attempts`, как в 8.1.

### 8.7 `core.ping` — демо-задача

Payload — `EmptyPayload`. Пишет строку в лог. Существует, чтобы проверить работоспособность очереди в скелете. **Удаляется после стадии 0.**

### Расписание beat

```python
beat_schedule = {
    "flush-view-counters": {
        "task": "catalog.flush_view_counters",
        "schedule": 300.0,
        "kwargs": {"payload": {}},
    },
    "expire-banner": {
        "task": "core.expire_banner",
        "schedule": 3600.0,
        "kwargs": {"payload": {}},
    },
}
```

---

## 9. URL-карта и контракт фильтрации

`i18n_patterns(..., prefix_default_language=False)`. Украинский без префикса, русский с `/ru/`.

| URL | Метод | View | Индексация |
|---|---|---|---|
| `/` | GET | home | index |
| `/galereya/` | GET | gallery | index |
| `/galereya/<occasion_slug>/` | GET | gallery | index |
| `/robota/<slug>/` | GET | work_detail | index |
| `/obrane/` | GET | favorites | noindex |
| `/poshuk/` | GET | search | noindex |
| `/vidhuky/` | GET | review_list | index |
| `/kontakty/` | GET | contacts | index |
| `/pro-nas/`, `/dostavka-i-oplata/`, `/faq/`, `/polityka-konfidentsiynosti/` | GET | static_page | index |
| `/blog/` | GET | post_list | index |
| `/blog/<slug>/` | GET | post_detail | index |
| `/dyakuyemo/` | GET | thanks | noindex |
| `/hx/gallery/` | GET | фрагмент сетки. Дополнительно принимает параметр `occasion` со слагом раздела | noindex |
| `/hx/favorites/` | POST | фрагмент карточек по списку номеров из браузера | noindex |
| `/hx/lead/` | POST | приём заявки | noindex |
| `/hx/review/` | POST | приём отзыва | noindex |
| `/admin/upload-image/` | POST | загрузка картинок из tinymce, только для staff | noindex |
| `/healthz/` | GET | healthcheck | noindex |
| `/kitchen-sink/` | GET | только при `DEBUG=True` | noindex |
| `/sitemap.xml`, `/robots.txt` | GET | | |

### Коды ответа

| Ситуация | Код |
|---|---|
| Работа опубликована | 200 |
| Работа в архиве | **410**, шаблон `410.html` |
| Работа в черновике или не существует | 404 |
| Повод не существует или неактивен | 404 |
| Неизвестный query-параметр или неизвестный слаг тега | 200, параметр молча отброшен |

Архив отдаёт 410, а не 404, потому что страница могла быть проиндексирована и 410 быстрее убирает её из выдачи.

### Контракт query-параметров галереи

- Имя параметра = `TagGroup.slug`, значение = `Tag.slug`. Несколько значений — повтор параметра: `?color=bilyi&color=rozhevyi`.
- Внутри группы — **ИЛИ**, между группами — **И**.
- Повод передаётся только через путь: `/galereya/vesillya/?type=buket`.
- `sort`: `new` (по умолчанию) или `popular`. Значение вне набора игнорируется.
- `page` — целое от 1.
- Неизвестные параметры и слаги отбрасываются молча.
- Canonical нормализуется: группы по `TagGroup.order`, значения внутри группы по алфавиту слага.
- `occasion` — **только для `/hx/gallery/`**. Эндпоинт HTMX один на все разделы, поэтому форма фильтров передаёт слаг текущего раздела скрытым полем. На публичном адресе повод остаётся частью пути и в query не появляется никогда. Имя зарезервировано в 4.3.

### Точные ключи сортировки

| `sort` | `order_by` |
|---|---|
| `new` | `('-is_pinned', F('published_at').desc(nulls_last=True), '-id')` |
| `popular` | `('-is_pinned', '-views_count', '-id')` |

`-id` в конце обязателен: без него при равных `views_count` (а он у большинства работ нулевой) Postgres вернёт нестабильный порядок и «Показати ще» будет дублировать и терять карточки.

### Правила индексации

Функция `catalog.seo.robots_directive(occasion, tags, sort, page) -> tuple[str, str]` возвращает пару «директива robots, canonical».

Правила применяются сверху вниз, первое сработавшее определяет `noindex`; canonical берётся от самого сильного сработавшего правила:

| Условие | robots | canonical |
|---|---|---|
| `sort == 'popular'` | `noindex, follow` | тот же URL без `sort` |
| Два и больше активных тегов | `noindex, follow` | базовая страница раздела (повод без тегов) |
| Ровно один активный тег | `index, follow` | нормализованный URL с этим тегом и `page` |
| Тегов нет | `index, follow` | URL раздела с `page` |

`page > 1` не влияет на `index`/`noindex`, но всегда входит в canonical; дополнительно ставятся `rel=prev` и `rel=next`.

Примеры:

- `/galereya/?type=a&color=b&page=2` → `noindex, follow`, canonical `/galereya/`
- `/galereya/vesillya/?type=a&sort=popular` → `noindex, follow`, canonical `/galereya/vesillya/?type=a`

`hreflang` на каждой публичной странице: `uk`, `ru`, `x-default` на украинскую версию.

### История браузера и «Показати ще»

`hx-push-url` обновляет адрес при смене фильтров и при подгрузке следующей страницы (меняется только `page`). Кнопка «назад» возвращает состояние с соответствующей страницей; догруженные поверх блоки не восстанавливаются, страница рендерится сервером заново.

**Адрес ставит сервер.** Обновление строки адреса выполняется заголовком ответа `HX-Push-Url` с готовым публичным нормализованным URL (`/galereya/vesillya/?color=bilyi&type=buket`), собранным по правилам канонизации этого раздела. Атрибут `hx-push-url="true"` на запросах к `/hx/gallery/` **не используется**: он записал бы в адресную строку служебный эндпоинт, закрытый в `robots.txt` и не отдающий страницу целиком. Нормализация — серверная логика и на клиенте не воспроизводится.

---

## 10. Структура страниц

### Шапка (на всех страницах)

Липкая, при скролле уменьшается по высоте.

Слева логотип-ссылка на главную. По центру на ПК: Галерея · Про нас · Доставка і оплата · Відгуки · Блог · Контакти. Справа: переключатель UA/RU, номер телефона крупно ссылкой `tel:`, иконки Instagram, Viber, Telegram.

**Мобильная версия.** Пункты меню скрыты за кнопкой с тремя горизонтальными полосками справа в шапке — по нажатию выезжает панель на весь экран с пунктами меню, переключателем языка, поиском по номеру и контактами. В шапке всегда видны логотип, иконка телефона и кнопка меню. Отдельной плавающей кнопки звонка внизу экрана **нет**.

Пункты меню — данные в `core/navigation.py`, не разметка.

### Праздничный баннер

Полоса над шапкой при `banner_enabled` и не истёкшей дате. Закрывается крестиком. Факт закрытия хранится в `localStorage` под ключом `banner_dismissed`, значение — хеш от `banner_text_uk + banner_until`. Смена текста или даты возвращает баннер.

### Режим «не приймаємо замовлення»

При `accepting_orders = False` под баннером показывается полоса с `not_accepting_message`. Неактивными становятся кнопки «Замовити схожу», «Залишити заявку» и «Передзвоніть мені». **Ссылки `tel:`, Viber и Telegram остаются активными всегда** — это единственный канал продаж, отключать его нельзя ни при каких настройках.

### Cookie-баннер

Показывается при первом визите внизу экрана: короткий текст, ссылка на политику конфиденциальности, кнопки «Прийняти» и «Тільки необхідні». Выбор хранится в `localStorage` под ключом `cookie_consent:v1`. Аналитика подключается только при выборе «Прийняти».

### Главная

1. **Hero** — полоса фотографий во всю ширину экрана, текст лежит на ней: заголовок, подзаголовок, кнопки «Дивитись галерею» и «Зателефонувати». Рисуется примитивом `hero_showcase.html`. Первая панель — `SiteSettings.hero_image`, за ней до двух обложек поводов, панели слегка развёрнуты в перспективе и перекрывают друг друга без просветов; первая грузится с `fetchpriority="high"`, остальные ленивые. На мобильном остаётся одна панель, текст лежит на ней так же. Между фотографиями и текстом — затемнение, текст белый; фотографии сквозь него видны. Полоса фотографий декоративна: она скрыта от скринридера, весь смысл несут заголовок и подзаголовок.
2. **Плитки поводов** — все `Occasion` с `show_on_home`, ведут на `/galereya/<slug>/`.
3. **Свіжі роботи** — 12 последних опубликованных, кнопка «Всі роботи».
4. **Як замовити** — шаги из `HowToStep`.
5. **Відгуки** — 3 отзыва с `is_featured`, ссылка на все.
6. **З блогу** — 3 последних поста.
7. **Контакти** — адрес, часы, телефон, карта, соцсети, кнопка на профиль Instagram.

Пустой блок (нет отзывов, нет постов) не рендерится вовсе.

### Галерея

- Панель фильтров: на ПК колонкой слева, липкая; на мобильном — кнопка «Фільтри» с числом активных, панель выезжает снизу на 90% высоты, применение кнопкой «Показати N робіт».
- **Первый блок панели — поводы.** Пункты рендерятся ссылками на `/galereya/<slug>/`, не чекбоксами: повод живёт в пути, а не в query.
- Дальше блоки групп тегов из `TagGroup` в порядке `order`.
- Активные фильтры — чипы с крестиком над сеткой, рядом «Очистити все».
- Счётчик «Знайдено 47 робіт».
- Сортировка: «Новинки» и «Популярні».
- **Сетка равных карточек**, изображение с `aspect-ratio: 4/5` и `object-fit: cover`. 2 колонки на мобильном, 3 на планшете, 4 на ПК. Masonry не используется: CSS-колонки раскладывают элементы сверху вниз, ломая порядок и подгрузку, а фиксированная пропорция заодно даёт нулевой сдвиг вёрстки.
- «Показати ще» подгружает следующую страницу через HTMX.
- Пустой результат: «Нічого не знайдено», сброс фильтров, «Зателефонуйте, підберемо» с номером.
- Внизу страницы раздела — SEO-текст из `Occasion.description`.

### Карточка работы

- Галерея фотографий: основное фото, лента миниатюр, свайп на мобильном, лайтбокс с зумом и стрелками.
- **Номер работы** — на уровне заголовка, отображается как `№147`, кнопка «Скопіювати номер» кладёт в буфер `147` без символа номера.
- Заголовок, описание, состав, размер.
- Теги-ссылки в галерею с этим фильтром.
- Дисклеймер про сезонность отдельным блоком: «Повторимо максимально близько. Квіти можуть відрізнятися залежно від сезону та поставки».
- Кнопки: «Зателефонувати» (основная), «Написати у Viber», «Написати в Telegram», «Замовити схожу».
- Иконки «В обране» и «Поділитися» (Web Share API, фолбэк — копирование ссылки).
- «Схожі роботи»: до 8, приоритет по совпадению поводов, затем по тегам, текущая исключена.
- OG-теги с рендишеном `og` в jpeg и номером работы в заголовке.

### Обране

Список номеров хранится в `localStorage` под ключом `favorites`. Страница `/obrane/` работает в двух режимах:

- без параметров — читает список из браузера и запрашивает карточки через `POST /hx/favorites/`;
- с параметром `?a=147,152,160` — рендерится **на сервере**, ссылку можно отправить в мессенджере.

Параметр `a` — целые числа через запятую. Дубликаты, мусор, отрицательные значения и несуществующие номера отбрасываются молча. **Список ограничен 50 номерами**, лишние игнорируются.

Кнопки: «Надіслати заявку по цих роботах» и «Скопіювати посилання на добірку».

### Пошук

`/poshuk/?q=...`:

1. Если из строки извлекается число (устойчиво к `#`, `№`, пробелам, ведущим нулям) и работа с таким артикулом опубликована — редирект 302 на её карточку.
2. Иначе `icontains` по `title_uk`, `title_ru`, `composition_uk`, `composition_ru` с `.distinct()`. Теги в текстовом поиске не участвуют.
3. Ничего не найдено — пустое состояние с кнопкой в галерею, код 200, не 404.

Черновики и архив не находятся.

### Контакти

Адрес, ориентир, парковка, карта iframe с `loading="lazy"`, кнопка «Прокласти маршрут», телефоны, часы работы, мессенджеры, ссылка на Instagram, форма заявки, микроразметка `LocalBusiness`.

### Форма заявки

Два входа: «Передзвоніть мені» (имя и телефон) и «Залишити заявку» (полная форма). Обе создают `Lead`.

Поля полной формы: имя, телефон, удобный канал связи, дата мероприятия, ориентир по бюджету, комментарий, чекбокс согласия со ссылкой на политику. Скрытые: номер работы, номера из избранного, подписанная метка времени, поле-ловушка, токен Turnstile.

**Механика отправки.** Форма постится на `/hx/lead/` через HTMX. При ошибках валидации возвращается фрагмент формы с подсветкой полей. При успехе ответ содержит заголовок `HX-Redirect: /dyakuyemo/`, браузер переходит на страницу благодарности. При отключённом JavaScript форма работает обычным POST с ответом 302 на тот же адрес. Страница `/dyakuyemo/` существует всегда и служит точкой отсчёта конверсии.

### Відгуки

Список опубликованных. Кнопка «Залишити відгук» открывает форму: имя, текст, оценка, фото, телефон для связи, согласие. Отправка на `/hx/review/`, механика та же. Отзыв попадает в `pending` и не виден до подтверждения владельцем.

### Страницы ошибок

- `404.html` — заголовок, текст, кнопка «До галереї», строка поиска по номеру.
- `410.html` — «Ця робота більше не доступна», кнопка в галерею, блок похожих работ.
- `500.html` — **самостоятельный шаблон**, не наследует `base.html`, не использует контекст-процессоры, стили инлайном. Должен рендериться при недоступной базе.

---

## 11. Мультиязычность

- Языки: `uk` (по умолчанию) и `ru`. `LANGUAGE_CODE = "uk"`.
- Интерфейс — штатный `gettext`: `{% trans %}`, `{% blocktrans %}`, `gettext_lazy`. Файлы в `locale/`.
- Контент — пары полей в моделях. Библиотека `modeltranslation` не используется: неявная магия с миграциями для одного разработчика лишний источник сюрпризов.
- Доступ только через миксин и фильтры:

```python
class TranslatedMixin:
    def tr(self, field: str) -> str:
        lang = get_language() or "uk"
        return getattr(self, f"{field}_{lang}", "") or getattr(self, f"{field}_uk", "") or ""
```

- `{{ obj|tr:"title" }}` — экранируемый текст. Используется везде по умолчанию.
- `{{ obj|tr_html:"body" }}` — возвращает `mark_safe`. Применяется **только** к полям, которые санитизируются bleach при сохранении: `StaticPage.body_uk/ru`, `Post.body_uk/ru`. Список закрытый, расширение — изменение контракта.
- Обращение к `work.title_uk` напрямую в шаблоне запрещено: русская версия молча покажет украинский текст и никто не заметит.
- Переключатель языка сохраняет текущий путь и все query-параметры.
- Множественные числа — через `{% blocktrans count %}`, не конкатенацией.

---

## 12. UI-примитивы

Собираются в скелете **до** начала фич, лежат в `templates/ui/` (исключение — `cookie_banner.html`, см. строку таблицы), подключаются через `{% include %}`.

| Файл | Параметры |
|---|---|
| `button.html` | `variant` (`primary`/`secondary`/`ghost`/`danger`), `size`, `href` или `type`, `label`, `icon`, `full_width`, `disabled`, `attrs` |
| `icon_button.html` | `icon`, `label` (aria-label), `href`, `variant` |
| `chip.html` | `label`, `href`, `removable`, `remove_url`, `color_hex` |
| `badge.html` | `label`, `tone` |
| `card_work.html` | `work`, `show_price`, `lazy`, `sizes` |
| `card_post.html` | `post` |
| `card_review.html` | `review`, `compact` |
| `picture.html` | `image` (WorkImage), `preset`, `sizes`, `lazy`, `alt`, `priority`. Рендерит `<picture>` с avif и webp, `width`/`height`. Пока `renditions_ready` False — рендерит `skeleton.html`, **не оригинал**. `priority=True` даёт `loading="eager"` и `fetchpriority="high"` и ставится только у hero и первых четырёх карточек первой страницы галереи |
| `image_simple.html` | `field` (любой ImageField, кроме WorkImage), `alt`, `lazy`, `sizes`. Для обложек, hero, фото отзывов |
| `input.html` | `name`, `label`, `type`, `value`, `error`, `required`, `hint`, `autocomplete` |
| `textarea.html` | те же плюс `rows`, `maxlength` |
| `select.html` | `name`, `label`, `options`, `value`, `error` |
| `checkbox.html` | `name`, `label`, `checked`, `error` |
| `color_swatch.html` | `tag`, `checked` |
| `filter_group.html` | `group`, `active_slugs` |
| `drawer.html` | `id`, `title`, `position`, слот. Alpine, блокировка скролла фона, Esc, клик вне |
| `modal.html` | `id`, `title`, слот |
| `lightbox.html` | `images`, `start_index` |
| `pagination.html` | `page_obj`, `base_url` |
| `load_more.html` | `next_url`, `label` |
| `hero_showcase.html` | `images` (1–3 изображения, первое — передняя панель; лишние игнорируются), `title`, `subtitle`, `body_template` (шаблон с кнопками, рендерится под подзаголовком). Полоса фотографий во всю ширину экрана, панели развёрнуты в перспективе, поверх — затемнение и белый текст, выровненный по контейнеру `max-w-site`. Первая картинка `priority`, остальные ленивые; на мобильном рисуется только первая. Полоса несёт `aria-hidden` |
| `section_heading.html` | `title`, `subtitle`, `link_url`, `link_label` |
| `empty_state.html` | `title`, `text`, `action_label`, `action_url`, `level` (`2` по умолчанию; `1` там, где пустое состояние занимает страницу целиком — `/dyakuyemo/`, `404`, `410`, иначе такая страница остаётся вовсе без `h1`) |
| `alert.html` | `tone`, `text` |
| `breadcrumbs.html` | `items`, плюс микроразметка BreadcrumbList |
| `phone_link.html` | `phone`, `variant`. Ссылка `tel:` с событием аналитики |
| `social_icons.html` | `size` |
| `map_embed.html` | `src`, `title` |
| `skeleton.html` | `kind`, `count`, `ratio` |
| `cookie_banner.html` | без параметров. **Лежит в `templates/layout/`**, а не в `ui/`: это часть каркаса страницы, а не переиспользуемый примитив. На `/kitchen-sink/` присутствует наравне с остальными |

**Перечень значений `tone`** для `alert.html` и `badge.html` закрытый: `info`, `success`, `warning`, `danger`. Значения `error` в палитре раздела 13 нет, вместо него `danger`.

Роут `/kitchen-sink/` (только при `DEBUG=True`) рендерит все примитивы во всех состояниях. Для примитивов, принимающих модели, используются стабы из `tests/stubs.py` — kitchen-sink не должен зависеть от наличия данных в базе.

### 12.1 Контракты DOM

Идентификаторы и `data`-атрибуты, на которые опираются HTMX и JavaScript, — такая же часть контракта, как имена полей моделей. Список **закрытый**, новый идентификатор — изменение контракта и бамп версии ядра.

| Идентификатор | Где живёт | Зачем |
|---|---|---|
| `#gallery-grid` | галерея | цель swap сетки, приёмник карточек при догрузке |
| `#gallery-count` | галерея | «Знайдено 47 робіт», OOB-блок |
| `#gallery-chips` | галерея | активные фильтры чипами, OOB-блок |
| `#gallery-filters` | галерея | панель фильтров, OOB-блок |
| `#filters-count` | галерея | число на мобильной кнопке «Фільтри», OOB-блок |
| `#load-more` | галерея | кнопка догрузки, подменяет сама себя через `outerHTML` |
| `#favorites-grid` | `/obrane/` | цель ответа `/hx/favorites/` |
| `#favorites-count` | шапка | счётчик избранного |
| `#lead-form` | формы заявки | цель ответа `/hx/lead/` при ошибках валидации |
| `#review-form` | форма отзыва | цель ответа `/hx/review/` при ошибках валидации |
| `data-favorite="<article>"` | карточка работы | кнопка избранного, связь с номером работы |

Панель фильтров обязана обновляться вместе с сеткой: иначе снятие фильтра чипом не снимет галочку в панели, и следующая отправка формы вернёт только что убранный фильтр.

---

## 13. Дизайн-токены

Задаются в `tailwind.config.js` в `theme.extend`. Произвольные значения в шаблонах запрещены.

```js
colors: {
  cream:      '#F8F0F7',  // фон страницы. v9: тёплый фиолетовый вместо бежевого
  ink:        '#2B2429',  // основной текст
  muted:      '#6D6069',  // вторичный текст. v3: затемнён с #7A736C
  line:       '#E7D8E5',  // границы
  accent:     '#944E8C',  // фиолетовый логотипа: кнопки, ссылки, активные фильтры. v8: затемнён с #A95DA0 ради 4.5:1
  accentSoft: '#F2E4F1',
  leaf:       '#5E7355',
  success:    '#4B7A52',
  danger:     '#A6413A',
},
maxWidth: { site: '1280px', content: '68ch' },
aspectRatio: { card: '4 / 5' },

fontFamily: {
  display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
  sans:    ['Manrope', 'system-ui', 'sans-serif'],
},
fontSize: {
  'xs':   ['0.75rem',  { lineHeight: '1.1rem'  }],  // подписи, счётчики
  'sm':   ['0.875rem', { lineHeight: '1.35rem' }],  // вторичный текст, чипы
  'base': ['1rem',     { lineHeight: '1.6rem'  }],  // основной текст
  'lg':   ['1.125rem', { lineHeight: '1.75rem' }],  // лид-абзац
  'h3':   ['1.375rem', { lineHeight: '1.8rem'  }],
  'h2':   ['1.75rem',  { lineHeight: '2.1rem'  }],
  'h1':   ['2.25rem',  { lineHeight: '2.5rem'  }],  // мобильный
  'hero': ['3rem',     { lineHeight: '3.2rem'  }],  // hero от md
},
spacing:   { 'section': '3rem', 'section-lg': '5rem' },
maxHeight: { 'drawer': '90vh' },
width:     { 'filters': '260px' },
ringOffsetColor: { DEFAULT: '#F8F0F7' },  // cream, иначе белый ободок фокуса на кремовом фоне
```

- **Шрифты.** Заголовки — `Cormorant Garamond`, текст — `Manrope`. Оба обязаны содержать `ї`, `є`, `ґ`, `і`. Подключение локальными `woff2`, `font-display: swap`, без сторонних CDN.
- **Скругления:** `sm 4px`, `md 8px`, `lg 16px`, `full`.
- **Тени:** `card` и `overlay`. Больше двух уровней не вводить.
- **Сетка:** контейнер `max-w-site`, боковые отступы 16px на мобильном, 32px от `md`. Единственное исключение — hero главной: его фотографии идут от края до края экрана, но текст на них выровнен по тому же контейнеру.
- **Брейкпоинты** — дефолтные Tailwind. Проектирование начинается с 360px.
- **Анимации:** 150–250 мс, `ease-out`, уважать `prefers-reduced-motion`.
- **Доступность:** контраст не ниже 4.5:1, зона нажатия от 44×44px, видимый фокус, `aria-label` у каждой иконки-кнопки.

**Затемнение `muted` и `accent`.** Исходные `#7A736C` и `#B25C4B` давали на фоне `cream` около 4.4:1 и не проходили порог 4.5:1, заявленный этим же разделом; v3 заменила их на `#6E675F` и `#9E4E3F`. В v8 акцент переехал на фиолетовый логотипа и прошёл ту же процедуру: знак нарисован `#A95DA0` (4.17:1 на `cream`), в палитру взят затемнённый до 44% светлоты `#944E8C` (5.32:1). Проверяются инструментом три пары на фоне `cream`: `ink`, `muted`, `accent`, и отдельно белый текст на `accent` — кнопки набраны им.

**Логотип.** `static/img/logo-mark.webp` — короткий знак: название магазина с розой, вырезанное из исходника `static/img/main.png` (318×96). Слоган и фигура в знак не входят: на высоте шапки слоган нечитаем, а фигура только съедает ширину. Показывается 28px на мобильном, 32px от `md`, 48px в подвале. Рядом название текстом не дублируется, оно живёт в `alt`. Знак сохраняет собственный `#A95DA0` и не перекрашивается в `accent`: это авторская работа, а не иконка.

**Типографика.**

- Ровно один `h1` на странице. На мобильном `text-h1`; `text-hero` — только hero главной от `md`.
- Заголовки — `font-display` вес 600, текст — `font-sans` вес 400.
- Ширина колонки основного текста — `max-w-content`.
- Межстрочный интервал живёт в токенах шкалы `fontSize` и отдельными `leading-*` не переопределяется.
- Вертикальный ритм: секции разделяются `py-section md:py-section-lg`; отступ ставится сверху у следующего элемента, `mb-*` у последнего элемента блока не ставится.
- Фокус: `focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2`, цвет отступа кольца — токен `ringOffsetColor`.

---

## 14. Изображения и хранилище

**Правило.** В базе — путь и метаданные. Файлы — через storage-объекты. Прямых обращений к файловой системе нет.

### 14.1 Фотографии работ

1. Загрузка в админке. Валидация: форматы `jpeg`, `png`, `webp`, `heic` (HEIC читается через `pillow-heif`, это формат по умолчанию на айфоне); размер до 25 МБ; минимальная сторона 800px.
2. **Оригинал пересохраняется:** применяется EXIF-ориентация, все метаданные удаляются целиком (включая GPS — координаты дома владельца публиковать нельзя), формат приводится к исходному. Хеш для `renditions_version` считается от **сохранённого** файла.
3. Оригинал кладётся в `private_storage`. Публично он недоступен.
4. `post_save` через `transaction.on_commit` ставит `generate_renditions` в очередь `media`.
5. Задача создаёт рендишены по пресетам 4.6, накладывает водяной знак, ставит `renditions_ready`.
6. `ui/picture.html` рендерит `<picture>` c avif и webp, `srcset` по ширинам, `width`/`height` и `loading="lazy"` — кроме hero и первых четырёх карточек, им `loading="eager"` и `fetchpriority="high"`. Пока рендишены не готовы, показывается скелетон.

### 14.2 Остальные изображения

Обложки постов, плитки поводов, hero, фото отзывов, картинки внутри текстов. **Рендишены для них не генерируются.** Файл сжимается один раз при загрузке сервисом `core/services/images.py`: длинная сторона до 1600px, конвертация в webp, метаданные вырезаются. Рендерятся примитивом `image_simple.html`.

Причина: пайплайн рендишенов привязан к `WorkImage` и оправдан только там, где изображений тысячи и они выводятся сеткой.

### 14.3 Хранилище и кэш

- v1: два тома, `media-public` и `media-private`. Публичный раздаёт nginx с `Cache-Control: public, max-age=31536000, immutable`. Приватный nginx не раздаёт вовсе.
- Заголовок `immutable` безопасен только потому, что имя файла рендишена содержит `renditions_version` (см. 4.6). Без этого перегенерация не долетала бы до пользователей год.
- Переезд на S3 — смена `media_backend` и ключей в `.env`, код не меняется.
- Бэкапы: `pg_dump` ежедневно с ротацией; медиа — `restic` или `rclone` ежедневно. Восстановление проверяется вручную один раз после запуска, результат записывается в `deploy/README.md`.

### 14.4 Кэш фрагментов галереи

- Ключ: `gallery:{ver}:{lang}:{sha1(нормализованный query + occasion)}:{page}`, TTL 300 секунд.
- `{ver}` — целое из Redis по ключу `gallery:ver`, инкрементируется в `post_save` и `post_delete` для `Work`, `WorkImage`, `Tag`, `Occasion`. Смена версии обесценивает весь кэш разом, без обхода ключей по префиксу.
- Кэш только для анонимных GET-запросов сетки. Админ-превью не кэшируется.
- Недоступный Redis — рендер напрямую, без ошибки.

---

## 15. Антиспам и лимиты

Четыре слоя, одинаково на форме заявки и форме отзыва.

1. **Поле-ловушка.** Скрытое стилями поле `website` (не `type=hidden`). Заполнено — ответ как при успехе (`HX-Redirect` на `/dyakuyemo/`), запись **не создаётся**. Боту не сообщается об отклонении.
2. **Минимальное время заполнения.** Скрытое поле с подписанной меткой времени (`django.core.signing`). Отправка быстрее `form_min_fill_seconds` или битая подпись — отклонение так же тихо.
3. **Rate limit на Redis.** Ключи строятся от UTC:

| Форма | Ключ по IP | Лимит | Глобальный ключ | Лимит |
|---|---|---|---|---|
| Заявка | `lead:ip:{ip_hash}:{YYYYMMDDHH}` | `lead_rate_per_ip_hour` (5) | `lead:global:{YYYYMMDD}` | `lead_rate_global_day` (20) |
| Отзыв | `review:ip:{ip_hash}:{YYYYMMDDHH}` | `review_rate_per_ip_hour` (2) | `review:global:{YYYYMMDD}` | `review_rate_global_day` (20) |

Окно фиксированное календарное, не скользящее: на границе часа возможны две серии подряд, и это приемлемо.

**При любом превышении запись сохраняется со статусом `spam`, уведомление не отправляется.** Пользователю показывается «Ви вже надіслали заявку. Зателефонуйте, будь ласка» с номером телефона. Терять реальные обращения из-за срабатывания лимита нельзя ни при каких условиях.

4. **Cloudflare Turnstile.** Невидимая проверка. При `turnstile_enabled=False` верификатор пропускает всё — локальная разработка не требует ключей.

Дополнительно: **Redis недоступен — форма продолжает работать**, лимит считается пройденным, в лог пишется предупреждение.

IP хранится только как `sha256(ip + ip_hash_salt)`.

---

## 16. SEO и аналитика

- Уникальные `<title>` и `<meta description>` на каждой странице, с фолбэком по типу страницы.
- Canonical и `robots` строго по таблице раздела 9.
- `hreflang`: `uk`, `ru`, `x-default`.
- OG и Twitter Card на всех публичных страницах. Для работы — рендишен `og` в jpeg, абсолютный URL, номер работы в заголовке.
- Микроразметка JSON-LD:
  - `LocalBusiness` на главной и контактах: адрес, телефон, часы работы. `AggregateRating` вкладывается в него, считается по опубликованным отзывам с непустым `rating`, выводится только при пяти и более таких отзывах.
  - `BreadcrumbList` на внутренних страницах.
  - На карточке работы, **пока `prices_enabled=False`**, выводятся `ImageObject` и `BreadcrumbList`. `Product` не выводится: Google требует у него `offers` с ценой, а разметка без цены даёт предупреждение.
  - `Article` в блоге.
- `sitemap.xml` через `django.contrib.sitemaps`: главная, разделы поводов, опубликованные работы, статические страницы, посты. Обе языковые версии. Черновики и архив не попадают.
- `robots.txt` закрывает только `/hx/` и `/admin/`. Страницы `/obrane/`, `/poshuk/`, `/dyakuyemo/` закрываются мета-тегом `noindex`: запрет обхода в `robots.txt` помешал бы краулеру прочитать этот тег. Правила дублируются для `/ru/`-путей.
- Целевые показатели: LCP до 2.5 с на 4G, CLS до 0.1, INP до 200 мс (ориентир). Достигается фиксированной пропорцией карточек, размерами в разметке, локальными шрифтами и отсутствием сторонних скриптов.
- **Бюджет веса: CSS плюс JS на главной не больше 60 КБ gzip.** Считается по собранному `app.css`, `htmx.min.js`, `alpine.min.js` и собственным скриптам. Превышение — повод удалять, а не оптимизировать по мелочи.
- **Аналитика:** Google Analytics 4. Подключается только если заполнен `analytics_ga_id` **и** пользователь выбрал «Прийняти» в cookie-баннере. События: `phone_click`, `viber_click`, `telegram_click`, `lead_submit`, `favorite_add`, `filter_apply`; конверсия на `/dyakuyemo/`. Meta Pixel не подключается: реклама не планируется.

---

## 17. Стратегия тестов

Тесты привязаны к слайсу и PR. Слайс мёрджится только с тестами.

**Главное правило: тесты выводятся из критериев приёмки задачи, а не из написанного кода.** Соблазн написать тест, повторяющий реализацию вместе с её багами, здесь основной риск. Тест кодирует контракт из этого файла.

Обязательные типы:

1. **Контрактные на стыках.** Payload каждой задачи Celery валидируется pydantic-моделью. Фейковый клиент валидирует то, что ему передали, и падает на несоответствии.
2. **Идемпотентность каждой задачи Celery.** Запустить дважды с одним payload — ровно один эффект.
3. **Путь ошибки.** Фейк возвращает 500 и таймаут: ретрай, `notified_at` пуст, `notify_attempts` растёт, запись не теряется.
4. **Property-based (hypothesis) на чистой логике.** Обязательно для: нормализации query-параметров (двойная нормализация равна одинарной, неизвестные параметры не влияют, порядок не влияет), `robots_directive`, разбора параметра `a` избранного, извлечения артикула из строки поиска, генерации слага, нормализации телефона.
5. **View-тесты** на коды ответа (включая 410 для архива), canonical, robots-мету, отсутствие `cost` и цены в HTML.
6. **E2E Playwright:** фильтрация галереи с проверкой адреса и кнопки «назад»; отправка заявки с карточки работы; добавление в избранное и открытие ссылки на подборку в чистом контексте браузера.

Инструменты: `pytest-django`, фабрики `factory_boy` в `tests/factories.py`, стабы моделей в `tests/stubs.py`. Задачи Celery вызываются напрямую, чтобы проверять тело задачи, а не работу брокера. Покрытие не цель, но падение ниже 70% по `apps/` — красный гейт.

Не тестируются: вёрстка попиксельно, admin-классы Django, сторонние библиотеки, гарантии Postgres.

---

## 18. Владение инфраструктурой

- **Миграции** — из моделей, отдельным коммитом, применяются отдельным шагом деплоя.
- **Сид-скрипт** `scripts/seed.py` — один источник фикстур для разработки, тестов и демонстрации. Идемпотентен (`update_or_create` по слагу). Наполняется **инкрементально**: каждый слайс, добавляющий модель, дописывает её в сид. К концу стадии 3 сид содержит: `SiteSettings`, 7 поводов, 4 группы тегов с наполнением, 3 шага «Як замовити», 4 статические страницы, 30 работ с изображениями-заглушками, 5 отзывов, 3 поста.
- **Конфиг** — только через `Settings`, `.env.example` всегда актуален.
- **Общие файлы:** `tech.md`, `config/`, `templates/base.html`, `templates/layout/`, `templates/ui/`, `tailwind.config.js`, `clients/`. Правка — отдельным коммитом с явной причиной, а если это контракт — с бампом версии ядра.

---

## 19. Конвенции кода, коммитов и PR

**Язык.** Код, имена, комментарии, коммиты, PR — только английский. Пользовательские тексты — украинский и русский через `gettext`.

**Коммиты.** Conventional Commits: `type(scope): summary`.

- `type` из закрытого набора: `feat`, `fix`, `test`, `refactor`, `chore`, `docs`.
- `scope` — приложение или область: `catalog`, `leads`, `core`, `ui`, `deploy`, `ci`.
- `summary` — императив, со строчной, без точки, до 50 символов.
- Тело — только чтобы объяснить *почему*.

Примеры: `feat(catalog): add tag filtering to gallery view`, `fix(leads): keep lead when redis is unavailable`.

**Коммиты пишутся по ходу работы, маленькими логическими шагами.** Миграции — всегда отдельным коммитом.

**PR.** Один слайс — один PR. Тело отвечает: что делает слайс, какие контракты затрагивает, чем покрыт тестами.

**Комментарии в коде.** Кратко, объясняют причину решения, а не пересказывают код. Закомментированный код в PR не остаётся.

**Python.** `ruff`, длина строки 100. Аннотации типов обязательны в сервисах, задачах, клиентах. `mypy` со `django-stubs` строго для `apps/*/services/`, `apps/*/contracts.py`, `apps/*/filters.py`, `apps/*/seo.py`, `clients/`.

**Django.** Толстые сервисы, тонкие вью. Бизнес-логика в `services/`. Запросы к БД из шаблонов запрещены, связи подтягиваются `select_related` и `prefetch_related`. Каждая страница списка укладывается в фиксированное число запросов, проверяется `assertNumQueries`.

---

## 20. Definition of Done одной задачи

- [ ] `ruff check` и `ruff format --check` чистые
- [ ] `mypy` чистый на зонах строгой проверки
- [ ] `makemigrations --check --dry-run` без расхождений, миграция вынесена отдельным коммитом и прочитана глазами
- [ ] тесты написаны из критериев приёмки и зелёные
- [ ] для каждой затронутой задачи Celery есть тест идемпотентности
- [ ] на стыке слайса есть контрактный тест
- [ ] нет N+1: страница покрыта `assertNumQueries`
- [ ] использованы примитивы раздела 12, самописного UI нет
- [ ] проверено на 360px и 1440px
- [ ] новые строки обёрнуты в `gettext` и переведены на оба языка
- [ ] `.env.example` обновлён, если появились переменные
- [ ] контракты не выдуманы: всё используемое есть в этом файле
- [ ] коммиты по конвенции, PR описан

---

## 21. Процедура CONTRACT GAP

Нужного контракта нет в этом файле — **СТОП**. Код с выдуманным полем, задачей или URL не пишется.

```
CONTRACT GAP
Что нужно: <поле / модель / задача / URL / компонент>
Зачем: <какая задача без этого не решается>
Предлагаемая форма: <имя, тип, ограничения, значение по умолчанию>
Влияние: <какие разделы tech.md и какие слайсы затрагивает>
Временное решение: <локальная заглушка, чтобы не блокировать работу>
```

Дальше: дописать контракт в нужный раздел → бампнуть версию и changelog → коммит `docs(core): add <contract> to tech.md, bump to vN` → вернуться к задаче.

Причина жёсткости: сессия нейросети оптимизирует закрытие текущей задачи, и выдумать недостающее поле ей проще, чем остановиться. Через три таких выдумки схема расходится с документом, и починка дороже одной остановки.

---

## 22. Дорожная карта

| Стадия | Содержание | Результат |
|---|---|---|
| **0. Скелет** | Репозиторий, Docker Compose, конфиг, хранилища, Tailwind, layout, i18n, базовые модели `core`, UI-примитивы, kitchen-sink, клиенты и фейки, Celery, сид, CI, эталонная вертикаль | Чек-лист «скелет готов» зелёный, задеплоено на тестовый сервер |
| **1. Каталог и галерея** | Модели каталога, админка, рендишены и водяной знак, галерея с фильтрами, карточка работы, главная, поиск по номеру | Владелец наполняет сайт, клиент ищет |
| **2. Обращения** | Настройки сайта, баннер, режим приёма заказов, форма заявки, антиспам, Telegram, избранное, cookie-баннер и аналитика | Сайт приносит обращения |
| **3. Контент** | Текстовые страницы, контакты с картой, отзывы с модерацией, блог, страницы ошибок | Сайт полный |
| **4. Прод** | SEO-разметка, sitemap, кэш галереи, nginx, деплой, Cloudflare, бэкапы, e2e | Боевой запуск |

Детальная разбивка на задачи — в `DEV.md`.
