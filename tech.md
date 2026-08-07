# tech.md — ядро проекта «Квіти» (интернет-магазин цветов, 2 точки)

**Версия ядра: v2**

## Changelog

- `v2` — «Витрина сегодня» на ежедневных фото заменена на **живую камеру** в торговом зале + **галерею работ с фильтрами** без ежедневной обязаловки. Удалены `ShowcaseItem` и задача `showcase.rollover_showcase`. Добавлены: приложение `live` (`LiveStream`, `StreamSnapshot`, абстракция `StreamProvider` + фейк), приложение `gallery` (`GalleryItem`, `GalleryTag`), эндпоинты `/api/v1/live/` и `/api/v1/gallery/`, задачи `live.grab_stream_snapshot`, `live.check_stream_health`, `gallery.generate_image_renditions`, раздел §10.8 «Приватность видеосъёмки».
- `v1` — первичная фиксация: стек, схема БД, контракты HTTP и Celery, платёжная абстракция, правила кода и безопасности, тест-доктрина, дорожная карта. Включает `common.AuditLog`, поля согласия и ретеншна в `Order`, задачи `orders.anonymize_old_orders` и `common.ping`.

> Источник истины. Все сессии подчиняются этому файлу дословно. Контракты (модели, поля, эндпоинты, payload задач, статусы) здесь заморожены. Разработчик их не выдумывает. Не хватает контракта — выдай блок `CONTRACT GAP` (формат в `DEV.md`), код с выдуманным типом не пиши.
> Файл меняется только append-only, каждое изменение контракта бампает версию и дописывает строку в changelog.

---

## 1. Проект

Интернет-магазин цветов с двумя физическими точками. Аудитория — люди, которые покупают букет за 5–15 минут с телефона, часто в подарок другому человеку, часто в панике («забыл про день рождения»).

Цель сайта: довести до заказа без регистрации, без звонка и без страха «сколько в итоге спишут».

Три опоры продукта, из которых выводится вся архитектура:

1. **Живая камера в зале** — трансляция из торгового зала в реальном времени. Клиент видит своими глазами, что стоит в холодильнике, без посредничества фотографа и ретуши. Это сильнее любой фотогалереи и не требует от менеджера ежедневной работы: камера висит и показывает.
   Ограничения приняты сознательно: поток не индексируется поисковиками, ночью показывать нечего, цену на конкретный букет из потока не назвать. Поэтому камера **дополняется** каталогом и галереей работ с фильтрами (§4.3, §4.4), а не заменяет их.
2. **Привязка к магазину** — ассортимент на двух точках различается. Клиент выбирает точку и видит только то, что есть на этой точке. Строка «нет в наличии» не показывается никогда: недоступная позиция просто не рендерится.
3. **Честная цена доставки** — три варианта получения вместо расплывчатого «доставка обсуждается». Точную сумму такси называет менеджер до оплаты. Инвариант системы: заказ с доставкой такси нельзя перевести в оплаченный, пока менеджер не проставил `delivery_fee`.

Регион: Украина. Валюта: UAH (грн). Язык интерфейса: украинский, один язык, i18n-инфраструктура включена, но второй язык в v1 не заводится.

### 1.1. Sitemap (фиксирован)

```
Главная                                    /
├── Каталог                                /catalog/
│   ├── По поводу                          /catalog/povod/<slug>/
│   ├── По цветку                          /catalog/kvitka/<slug>/
│   ├── По цене                            /catalog/?price=0-500|500-1000|1000-
│   └── Карточка товара                    /catalog/<product-slug>/
├── Конструктор букета                     /constructor/
├── Наживо з магазину (камера)             /live/
│   └── Камера конкретной точки            /live/<store-slug>/
├── Галерея работ                          /gallery/
│   └── Фильтры по поводу/цветку/цвету     /gallery/?occasion=&flower=&color=&store=
├── Корзина                                /cart/
├── Оформление заказа                      /checkout/
├── Статус заказа                          /order/<public_id>/<access_token>/
├── Наши магазины                          /stores/
├── Оплата и получение                     /payment-delivery/
├── Отзывы                                 /reviews/
├── Контакты                               /contacts/
└── Админка                                /manage/
```

### 1.2. Формулировка блока получения (текст фиксирован, выводится из БД `DeliveryOption`)

```
Как получить букет
— Самовывоз из магазина (2 адреса) — бесплатно
— Отправка по городу на такси — оплачивается по тарифу такси в момент
  заказа, обычно 60–150 грн. Менеджер называет точную сумму до оплаты
— Особые случаи (за город, точное время, крупный заказ) — договариваемся
  с менеджером
```

Блок обязателен в трёх местах: карточка товара, шаг «Как получить» в оформлении заказа, страница `/payment-delivery/`. Один шаблон-инклюд `templates/partials/delivery_note.html`, дублировать разметку запрещено.

### 1.3. Открытка

Бесплатна всегда. Поле `card_text` в оформлении заказа. Себестоимость копеечная, конверсионный эффект высокий: человек, начавший писать поздравление, почти не бросает корзину. Цену за открытку не вводить ни в каком виде.

---

## 2. Стек (фиксирован)

| Слой | Технология | Примечание |
|---|---|---|
| Язык | Python 3.12 | |
| Фреймворк | Django 5.x, **без DRF** | Монолит с серверным рендерингом |
| Шаблоны | Django Templates | Партиалы под HTMX |
| Интерактив | HTMX 2.x + Alpine.js 3.x | Островки, не SPA |
| Стили | Tailwind CSS 3 (django-tailwind или CLI) | Токены в `tailwind.config.js` |
| Валидация и DTO | **Pydantic 2** + pydantic-settings | Границы системы, см. §6 |
| БД | PostgreSQL 16 | |
| ORM | Django ORM | Raw SQL запрещён без ADR |
| Кэш / сессии / брокер | Redis 7 | 3 логические БД: `0` cache, `1` sessions, `2` celery |
| Очередь | Celery 5 + celery-beat (django-celery-beat) | |
| Админка | Django Admin + `django-unfold` | Мобильная, менеджер работает с телефона |
| Изображения | Pillow + `django-imagekit` (или sorl-thumbnail) | Ресайз в WebP, ленивые превью |
| Видеопоток | абстракция `StreamProvider`, см. §4.3 | Источник выбирается настройкой. Опции: MediaMTX/go2rtc на VPS (RTSP→HLS/WebRTC), YouTube Live, сторонний сервис |
| Плеер | `hls.js` (нативный HLS на iOS) + `<video>` | Свой плеер, не сторонний виджет, когда провайдер это позволяет |
| Кадры из потока | `ffmpeg` (только в контейнере воркера `media`) | Снапшот для постера, OG-картинки и fallback |
| Формы | Django Forms (server-side) | Pydantic — на JSON-границах |
| Задачи по расписанию | celery-beat | |
| Веб-сервер | Gunicorn (uvicorn-worker не нужен, WSGI) | |
| Реверс-прокси | Caddy | Авто-TLS |
| Статика/медиа | WhiteNoise (статика) + S3-совместимое хранилище (медиа) | Локально — FileSystemStorage |
| Контейнеризация | Docker + docker compose | |
| Безопасность | `django-axes`, `django-otp`, `django-ratelimit`, `django-csp`, `bleach` | брутфорс, 2FA, лимиты, CSP, санитайз HTML |
| Тесты | pytest, pytest-django, factory-boy, hypothesis, freezegun, Playwright | |
| Линт/типы | ruff (lint+format), mypy strict, bandit, pip-audit | |
| CI | GitHub Actions | |
| Мониторинг | Sentry, `django-health-check` на `/healthz/` | |

Запрещено вводить в проект: DRF, GraphQL, любой SPA-фреймворк, Celery-альтернативы, вторая ORM, jQuery. Это изменение стека — только через `CONTRACT GAP` и бамп версии ядра.

---

## 3. Архитектура

### 3.1. Слои (жёстко)

```
HTTP-слой        views / forms / htmx-партиалы / json-эндпоинты
   ↓ вызывает только use-case, никогда не ORM напрямую
Прикладной слой  services (use-cases): оркестрация, транзакции, публикация задач
   ↓
Доменный слой    чистые функции и dataclass/Pydantic-модели: расчёт цены,
                 машина статусов, правила доступности. Без Django-импортов.
   ↓
Слой доступа     repositories: единственное место, где живёт Django ORM
Внешний мир      clients: ABC-интерфейс + fake + real (платежи, SMS, Telegram)
```

Правила слоёв, нарушение — красное ревью:

- View не импортирует модели ORM и не пишет бизнес-логику. View: разобрал вход → позвал use-case → отрендерил.
- Доменный слой не импортирует `django.*` вообще. Он тестируется без БД и без настроек Django.
- Бизнес-логика в `Model.save()`, в сигналах и в шаблонах запрещена. Сигналы допустимы только для технических вещей (инвалидация кэша, генерация превью).
- Внешние клиенты — только через ABC. Прямой вызов `requests.post("https://...")` из сервиса запрещён.
- Транзакция открывается в use-case (`transaction.atomic`), не в репозитории и не во view.
- Задачи Celery публикуются через `transaction.on_commit`. Публикация внутри открытой транзакции запрещена — это гонка, задача стартует раньше коммита.

### 3.2. Структура папок

```
project/
├── config/
│   ├── settings/            base.py, local.py, prod.py, test.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── apps/
│   ├── common/              базовые модели, миксины, утилиты, money, phone
│   ├── stores/              магазины, часы работы, склад-остатки
│   ├── catalog/             товары, поводы, цветы, категории, изображения
│   ├── live/                живая камера: потоки, провайдеры, снапшоты
│   ├── gallery/             галерея работ с фильтрами
│   ├── constructor/         конструктор букета, расчёт цены
│   ├── cart/                корзина в сессии (Redis)
│   ├── orders/              заказ, машина статусов, оформление
│   ├── payments/            платёжная абстракция, провайдеры, вебхуки
│   ├── notifications/       Telegram/SMS менеджеру и клиенту
│   ├── reviews/             отзывы с премодерацией
│   └── pages/               статические страницы, SEO, sitemap.xml
├── templates/
│   ├── base.html
│   ├── partials/            переиспользуемые инклюды и htmx-фрагменты
│   └── ui/                  UI-примитивы (§8)
├── static/
├── tests/
│   ├── unit/                домен, без БД
│   ├── integration/         use-cases + БД + фейки
│   ├── contract/            HTTP- и Celery-контракты
│   └── e2e/                 Playwright
├── deploy/                  Dockerfile, compose, Caddyfile, systemd
└── scripts/                 seed.py, backup.sh
```

Внутри каждого приложения:

```
apps/<app>/
├── models.py            только ORM-модели и Meta
├── repositories.py      запросы к ORM, возвращают доменные объекты или QuerySet
├── services.py          use-cases
├── domain.py            чистая логика, без Django
├── schemas.py           Pydantic-модели входа/выхода
├── selectors.py         (опционально) сложные read-запросы для страниц
├── views.py
├── urls.py
├── forms.py
├── admin.py
├── tasks.py             Celery-задачи
└── tests/
```

---

## 4. Схема БД (заморожена)

Все модели наследуют `apps.common.models.BaseModel`:

```python
class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

Деньги — везде `DecimalField(max_digits=10, decimal_places=2)`, валюта UAH, хранение в гривнах с копейками. Смешивать `float` и деньги запрещено. Арифметика денег — только через `apps.common.money.Money`.

Телефон — `CharField(max_length=20)`, нормализуется до E.164 (`+380XXXXXXXXX`) на входе через `apps.common.phone.normalize_phone`. В БД хранится только нормализованный вид.

### 4.1. `stores`

**Store**

| Поле | Тип | Правила |
|---|---|---|
| `name` | CharField(120) | «Центр», «Позняки» |
| `slug` | SlugField(unique) | |
| `address` | CharField(255) | |
| `lat`, `lng` | DecimalField(9,6) null | для карты |
| `phone` | CharField(20) | E.164 |
| `work_hours` | JSONField | `{"mon": ["09:00","20:00"], ..., "sun": null}` |
| `is_active` | BooleanField(default=True) | |
| `sort_order` | PositiveSmallIntegerField(default=0) | |

**StorePhoto** — `store` FK, `image` ImageField, `sort_order`.

**StoreFlowerStock** — доступность конкретного цветка на конкретной точке. Единственный источник правды для конструктора.

| Поле | Тип | Правила |
|---|---|---|
| `store` | FK Store | |
| `flower` | FK Flower | |
| `price_per_stem` | Decimal(10,2) | цена за стебель на этой точке |
| `qty_available` | PositiveIntegerField | 0 = позиция не рендерится |
| `is_active` | BooleanField | ручной выключатель для менеджера |

`unique_together = ("store", "flower")`. Индекс `(store, is_active, qty_available)`.

### 4.2. `catalog`

**Occasion** (повод) — `name`, `slug` unique, `icon` CharField, `sort_order`, `is_active`, `seo_title`, `seo_description`, `intro_text` (TextField, для SEO-текста на странице категории).

**Flower** — `name`, `slug` unique, `color` CharField(30), `is_active`, `sort_order`, `image`. Цена не здесь: она в `StoreFlowerStock`, потому что различается по точкам.

**Addon** — зелень, упаковка, лента.

| Поле | Тип |
|---|---|
| `name` | CharField(120) |
| `slug` | SlugField unique |
| `kind` | CharField choices: `greenery` / `packaging` / `ribbon` |
| `price` | Decimal(10,2) |
| `is_active` | Boolean |
| `image` | ImageField null |

**AddonStoreAvailability** — `addon` FK, `store` FK, `is_available` Boolean. `unique_together`.

**Product** — готовый букет из каталога.

| Поле | Тип | Правила |
|---|---|---|
| `title` | CharField(200) | |
| `slug` | SlugField unique | |
| `description` | TextField | |
| `composition_text` | TextField | «15 троянд, евкаліпт, крафт» |
| `base_price` | Decimal(10,2) | |
| `old_price` | Decimal(10,2) null | для перечёркнутой цены |
| `occasions` | M2M Occasion | фильтр «по поводу» |
| `flowers` | M2M Flower | фильтр «по цветку» |
| `is_active` | Boolean | |
| `sort_order` | PositiveSmallIntegerField | |
| `seo_title`, `seo_description` | CharField null | |

Фильтр «по цене» — не таблица, а параметр запроса `?price=0-500|500-1000|1000-`, разбор в `catalog/domain.py::parse_price_band`. Границы диапазонов фиксированы в `PRICE_BANDS` в `catalog/domain.py`, менять только через бамп версии ядра.

**ProductImage** — `product` FK, `image`, `alt` CharField, `sort_order`, `is_main` Boolean.

**ProductStoreAvailability**

| Поле | Тип | Правила |
|---|---|---|
| `product` | FK Product | |
| `store` | FK Store | |
| `is_available` | Boolean | |
| `price_override` | Decimal(10,2) null | если задан — цена на этой точке |

`unique_together = ("product", "store")`. Правило рендера: товар показывается в каталоге выбранной точки только при `is_active AND is_available`. Плашка «нет в наличии» не существует в макете.

### 4.3. `live` — живая камера

Ежедневная ручная витрина отменена. Вместо неё камера в торговом зале и галерея работ (§4.4). От менеджера не требуется ничего ежедневного.

**LiveStream** — одна камера, привязанная к точке.

| Поле | Тип | Правила |
|---|---|---|
| `store` | OneToOne Store | одна камера на точку |
| `provider` | CharField(30) | `fake` / `mediamtx` / `youtube` / `external` |
| `source_ref` | CharField(255) | ключ у провайдера: имя пути MediaMTX, videoId YouTube, id камеры сервиса. **Не RTSP-строка** |
| `title` | CharField(120) | «Наживо: зал на Хрещатику» |
| `is_enabled` | Boolean default False | ручной выключатель для менеджера |
| `aspect_ratio` | CharField(8) default `16:9` | для верстки без прыжка макета |
| `has_audio` | Boolean default False | **всегда False**, см. §10.8 |
| `schedule` | JSONField | часы трансляции; вне их отдаётся постер. Дефолт — `Store.work_hours` |
| `poster` | ImageField null | последний снапшот, ставится задачей |
| `poster_taken_at` | DateTimeField null | |
| `health_status` | CharField(12) | `online` / `offline` / `unknown` |
| `health_checked_at` | DateTimeField null | |
| `offline_message` | CharField(255) blank | текст при недоступности |

Секреты камеры (RTSP-URL, логин, пароль, токен сервиса) в БД **не хранятся никогда**. Они лежат в env и известны только рестримеру. `source_ref` — публично безопасный идентификатор: его утечка не даёт доступа к камере.

**StreamSnapshot** — кадр из потока.

| Поле | Тип | Правила |
|---|---|---|
| `stream` | FK LiveStream CASCADE | |
| `image` | ImageField | |
| `taken_at` | DateTimeField db_index | |

Хранение — 48 часов, дальше чистится вместе с ретеншном. Снапшоты решают три задачи: постер плеера до старта потока, OG-картинка для соцсетей и честный fallback, когда камера офлайн. Публичный архив записей не ведётся (§10.8).

**Абстракция `StreamProvider`** (`apps/live/clients/base.py`, ABC). Источник потока меняется настройкой `STREAM_PROVIDER`, код страницы и плеера не переписывается.

```python
class StreamProvider(ABC):
    @abstractmethod
    def get_playback(self, stream: LiveStreamDTO) -> PlaybackDTO: ...
    @abstractmethod
    def check_health(self, stream: LiveStreamDTO) -> HealthDTO: ...
    @abstractmethod
    def grab_snapshot(self, stream: LiveStreamDTO) -> bytes | None: ...
```

```python
class PlaybackDTO(BaseModel):
    kind: Literal["hls", "webrtc", "iframe"]
    url: HttpUrl                 # m3u8, whep или embed-ссылка
    poster_url: HttpUrl | None
    is_live: bool
    latency_hint_s: int
```

Реализации: `FakeStreamProvider` (отдаёт зацикленный тестовый ролик из `static/dev/`, умеет притворяться офлайном по флагу — на нём пишутся все тесты и вся вёрстка), `MediaMTXProvider`, `YouTubeLiveProvider`, `ExternalEmbedProvider`.

Конкретный провайдер выбирается позже и не блокирует разработку: страница, плеер, оформление, состояния и тесты делаются против фейка с первого дня.

**Состояние камеры — единственная точка вычисления:**

```python
# apps/live/domain.py — чистая функция, без Django
def resolve_state(stream: LiveStreamDTO, now: datetime) -> StreamState: ...
```

`StreamState` — `Enum`: `LIVE` / `CLOSED` / `OFFLINE` / `DISABLED`. Приоритет проверок фиксирован: `is_enabled` → `schedule` → `health_status`. Вычислять состояние в шаблоне, во view или в JS запрещено: иначе получаются четыре места с четырьмя разными представлениями о том, когда магазин закрыт.

### 4.4. `gallery` — галерея работ

Фотографии реальных букетов. Пополняется пачками когда удобно, ежедневной обязаловки нет. Отличие от каталога: каталог — это товар, который можно купить сейчас по цене; галерея — портфолио, доказательство уровня флориста.

**GalleryItem**

| Поле | Тип | Правила |
|---|---|---|
| `image` | ImageField | |
| `title` | CharField(160) blank | |
| `description` | CharField(255) blank | |
| `store` | FK Store null | где собран |
| `occasions` | M2M Occasion | фильтр |
| `flowers` | M2M Flower | фильтр |
| `color` | CharField(30) blank | фильтр по гамме |
| `price_from` | Decimal(10,2) null | «від 750 грн», не точная цена |
| `related_product` | FK Product null SET_NULL | «замовити схожий» |
| `is_published` | Boolean default True | |
| `sort_order` | PositiveSmallIntegerField | |
| `shot_on` | DateField null | для сортировки по свежести |

Индексы: `(is_published, sort_order)`, `(is_published, shot_on)`. Фильтры комбинируются, пустая выдача даёт `EmptyState` со ссылкой на каталог.

**GalleryTag** — свободные метки (`«великий букет»`, `«монобукет»`, `«коробка»`): `name`, `slug` unique, `is_active`. M2M к `GalleryItem`.

### 4.5. `orders`

**Order**

| Поле | Тип | Правила |
|---|---|---|
| `public_id` | CharField(26) unique | ULID, в URL |
| `access_token` | CharField(32) unique | второй секрет в URL статуса, защита от перебора |
| `store` | FK Store PROTECT | точка исполнения |
| `fulfillment_type` | CharField choices | `pickup` / `taxi` / `manager` |
| `recipient_name` | CharField(120) | |
| `recipient_phone` | CharField(20) | E.164 |
| `customer_name` | CharField(120) | |
| `customer_phone` | CharField(20) | E.164 |
| `delivery_address` | CharField(255) blank | обязателен только при `taxi` |
| `desired_date` | DateField | |
| `desired_time_slot` | CharField(20) | `10-13` / `13-16` / `16-19` / `asap` |
| `card_text` | TextField(500) blank | бесплатно |
| `comment` | TextField blank | |
| `payment_method` | CharField choices | `online` / `on_delivery` / `transfer` |
| `status` | CharField choices | см. §4.6 |
| `subtotal` | Decimal(10,2) | сумма позиций |
| `delivery_fee` | Decimal(10,2) null | ставит менеджер, при `pickup` = 0 |
| `total` | Decimal(10,2) | `subtotal + coalesce(delivery_fee, 0)` |
| `idempotency_key` | UUIDField unique | ключ клиента, защита от двойного сабмита |
| `utm` | JSONField default dict | источник трафика |
| `consent_at` | DateTimeField null | момент согласия на обработку ПД |
| `consent_policy_version` | CharField(20) blank | версия текста политики на момент согласия |
| `anonymized_at` | DateTimeField null | проставляется ретеншн-задачей, §10.4 |

**OrderItem**

| Поле | Тип | Правила |
|---|---|---|
| `order` | FK Order CASCADE | |
| `kind` | CharField choices | `product` / `custom` |
| `product` | FK Product PROTECT null | заполнен при `kind=product` |
| `title_snapshot` | CharField(200) | название на момент заказа |
| `composition_snapshot` | JSONField | состав кастомного букета, см. §5.4 |
| `unit_price` | Decimal(10,2) | цена на момент заказа |
| `qty` | PositiveSmallIntegerField | |
| `line_total` | Decimal(10,2) | |

Снапшоты обязательны: цена и состав в заказе не пересчитываются никогда после создания. Меняется цена товара — старые заказы не двигаются.

**OrderStatusLog** — `order` FK, `from_status`, `to_status`, `actor` (CharField: `system` / username), `reason` TextField blank, `created_at`. Пишется на каждый переход, без исключений.

### 4.6. Машина статусов заказа (заморожена)

```
new ──> confirmed ──> awaiting_payment ──> paid ──> assembling ──┬─> ready_for_pickup ──> completed
 │           │               │               │                   └─> in_delivery ───────> completed
 └──────────>└──────────────>└──────────────>└─────────────> cancelled
```

Разрешённые переходы — единственный источник: `orders/domain.py::ALLOWED_TRANSITIONS`.

```python
ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    NEW:               frozenset({CONFIRMED, CANCELLED}),
    CONFIRMED:         frozenset({AWAITING_PAYMENT, ASSEMBLING, CANCELLED}),
    AWAITING_PAYMENT:  frozenset({PAID, CANCELLED}),
    PAID:              frozenset({ASSEMBLING, CANCELLED}),
    ASSEMBLING:        frozenset({READY_FOR_PICKUP, IN_DELIVERY, CANCELLED}),
    READY_FOR_PICKUP:  frozenset({COMPLETED, CANCELLED}),
    IN_DELIVERY:       frozenset({COMPLETED, CANCELLED}),
    COMPLETED:         frozenset(),
    CANCELLED:         frozenset(),
}
```

**Инварианты домена** (каждый — отдельный тест, см. §10):

1. `INV-1`. Переход не из `ALLOWED_TRANSITIONS` бросает `IllegalStatusTransition`. Прямая запись `order.status = ...` вне `orders.services.transition_order` запрещена.
2. `INV-2`. `fulfillment_type == taxi` и `delivery_fee is None` → переход в `awaiting_payment` и в `paid` запрещён. Это защита обещания «менеджер называет точную сумму до оплаты».
3. `INV-3`. `fulfillment_type == taxi` → `delivery_address` непустой. Иначе `ValidationError` на создании.
4. `INV-4`. `fulfillment_type == pickup` → `delivery_fee == 0` и `delivery_address == ""`.
5. `INV-5`. `total == subtotal + coalesce(delivery_fee, 0)` всегда. Проверяется в БД `CheckConstraint` и в домене.
6. `INV-6`. Все `OrderItem` одного заказа доступны на `order.store` на момент создания.
7. `INV-7`. Любой переход пишет `OrderStatusLog`. Число логов == числу фактических переходов.
8. `INV-8`. Заказ в `completed` или `cancelled` неизменяем, кроме поля `comment`.

**DeliveryOption** — справочник вариантов получения, из него рендерится блок §1.2.

| Поле | Тип |
|---|---|
| `code` | CharField unique: `pickup` / `taxi` / `manager` |
| `title` | CharField(120) |
| `description` | TextField |
| `price_hint_min`, `price_hint_max` | Decimal(10,2) null |
| `requires_address` | Boolean |
| `is_active` | Boolean |
| `sort_order` | PositiveSmallIntegerField |

### 4.7. `payments`

**Payment**

| Поле | Тип | Правила |
|---|---|---|
| `order` | FK Order PROTECT | |
| `provider` | CharField(30) | `fake` / `liqpay` / `mono` / `wayforpay` |
| `provider_payment_id` | CharField(128) db_index blank | id на стороне провайдера |
| `amount` | Decimal(10,2) | |
| `currency` | CharField(3) default `UAH` | |
| `status` | CharField choices | `created` / `pending` / `succeeded` / `failed` / `refunded` |
| `invoice_url` | URLField blank | |
| `raw_response` | JSONField default dict | сырой ответ, **без карточных данных** |

`unique_together = ("provider", "provider_payment_id")` при непустом `provider_payment_id`.

**PaymentEvent** — журнал вебхуков: `payment` FK null, `provider`, `event_id` CharField db_index, `payload` JSONField, `signature_valid` Boolean, `processed_at` null.
`unique_together = ("provider", "event_id")` — это и есть механизм идемпотентности вебхуков.

### 4.8. `reviews`

**Review** — `author_name`, `text` TextField, `rating` PositiveSmallIntegerField (1–5), `store` FK null, `order` FK null, `photo` ImageField null, `is_published` Boolean default False, `published_at` null, `moderator_note` blank.
Публикация только вручную из админки. Автопубликация запрещена.

### 4.9. `pages`

**StaticPage** — `slug` unique, `title`, `body` (TextField, разрешённый HTML-сабсет), `seo_title`, `seo_description`, `is_active`.
**SiteSettings** (singleton) — `phone`, `email`, `telegram`, `instagram`, `og_image`, `header_notice` (строка-баннер), `is_orders_paused` Boolean + `pause_message`, `privacy_policy_version` CharField(20). Кэшируется в Redis на 5 минут.

### 4.10. `common`

**AuditLog** — журнал действий staff. Пишется на каждое изменение заказа, платежа, остатков и настроек из админки, а также на экспорт данных.

| Поле | Тип | Правила |
|---|---|---|
| `actor` | FK User PROTECT null | null = `system` |
| `action` | CharField(60) | `order.status_change`, `order.set_delivery_fee`, `payment.manual_confirm`, `orders.export`, `stock.update`, `settings.update` |
| `object_type` | CharField(60) | имя модели |
| `object_id` | CharField(64) | pk или `public_id` |
| `changes` | JSONField default dict | `{"field": {"old": ..., "new": ...}}`, **без PII** |
| `ip` | GenericIPAddressField null | |
| `user_agent` | CharField(255) blank | |

Индекс `(object_type, object_id, created_at)`. Запись только на добавление: редактирование и удаление `AuditLog` закрыты на уровне админки и прав БД.

---

## 5. HTTP-контракты

Два типа эндпоинтов. Не смешивать.

- **Страницы** — обычные Django-view, возвращают HTML. При заголовке `HX-Request: true` возвращают партиал вместо полной страницы.
- **JSON-эндпоинты** — под префиксом `/api/v1/`, вход и выход строго через Pydantic-схемы. Используются островками Alpine (конструктор, корзина, статус заказа).

Общие правила JSON-эндпоинтов:

- Тело запроса валидируется Pydantic-моделью из `<app>/schemas.py`. `ValidationError` → HTTP 422 с телом ниже. Разбирать `request.POST` вручную запрещено.
- Ответ сериализуется Pydantic-моделью. Отдавать `model_to_dict` запрещено — это утечка полей.
- Ошибка — единый формат, один хелпер `apps.common.http.error_response`:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Перевірте поля форми",
    "fields": {"recipient_phone": "Невірний формат телефону"}
  }
}
```

Коды ошибок (закрытый набор): `validation_error` (422), `not_found` (404), `conflict` (409), `rate_limited` (429), `payment_failed` (402), `internal_error` (500).

- Все POST требуют CSRF-токен. `csrf_exempt` разрешён ровно на вебхуках платежей и только вместе с проверкой подписи.
- Идемпотентность мутаций — заголовок `Idempotency-Key: <uuid4>`. Обязателен на `POST /api/v1/orders/`.

### 5.1. Магазины и общее

```
GET /api/v1/stores/
→ 200 StoreListResponse
{"stores": [{"slug": "centr", "name": "Центр", "address": "...",
             "phone": "+380...", "lat": 50.44, "lng": 30.52,
             "work_hours": {...}, "is_open_now": true}]}
```

Выбранная точка хранится в cookie `store` (slug, 90 дней, `SameSite=Lax`) и дублируется в сессии. Все каталожные страницы читают её через `apps.stores.selectors.get_current_store(request)`. Точка не выбрана → берётся `Store.objects.filter(is_active=True).first()` по `sort_order`.

### 5.2. Живая камера

```
GET /api/v1/live/?store=<slug>
→ 200 LiveStreamResponse
{
  "store": "centr",
  "title": "Наживо: зал на Хрещатику",
  "state": "live",
  "playback": {"kind": "hls",
               "url": "https://stream.example.com/centr/index.m3u8",
               "poster_url": "https://cdn.../snapshot.webp",
               "is_live": true,
               "latency_hint_s": 8},
  "aspect_ratio": "16:9",
  "has_audio": false,
  "next_online_at": null,
  "message": null,
  "snapshot": {"url": "https://cdn.../snapshot.webp",
               "taken_at": "2026-08-07T10:12:00Z"}
}
```

`state` — закрытый набор, каждое значение обязано иметь свой макет:

| `state` | Когда | Что видит клиент |
|---|---|---|
| `live` | камера online и внутри `schedule` | плеер играет |
| `closed` | вне часов работы точки | постер + «Зараз зачинено. Відкриємось о 09:00» + `next_online_at` |
| `offline` | `health_status = offline` внутри часов | постер + честный текст + телефон точки |
| `disabled` | `is_enabled = False` | секция камеры не рендерится вообще |

Правило: пустого чёрного прямоугольника без объяснения не существует. Каждое состояние — законченный экран с постером и понятным текстом.

Кэш Redis, ключ `live:{store_slug}`, TTL 30 c (короткий: это статус, он должен быть свежим). Инвалидация — на сохранении `LiveStream` и на смене `health_status`.

`playback.url` для приватных источников выдаётся как **подписанная ссылка** с TTL 5 минут (см. §10.8), а не как постоянный публичный адрес.

### 5.2b. Галерея работ

```
GET /api/v1/gallery/?store=&occasion=&flower=&color=&tag=&page=
→ 200 GalleryResponse
{
  "items": [{"id": 41, "title": "Монобукет піонів",
             "image_url": "...", "image_srcset": "...",
             "price_from": "750.00", "color": "pink",
             "occasions": ["den-narodzhennya"],
             "flowers": ["pion"],
             "tags": ["monobuket"],
             "related_product_url": "/catalog/pion-mono/"}],
  "filters": {"occasions": [...], "flowers": [...],
              "colors": [...], "tags": [...]},
  "page": 1, "pages": 7, "total": 168
}
```

`filters` возвращает только те значения, по которым есть хотя бы одна опубликованная работа. Фильтр, ведущий в пустоту, не показывается — это дешёвый способ никогда не отдать пустой экран.

### 5.3. Конструктор — опции

```
GET /api/v1/constructor/options/?store=<slug>
→ 200 ConstructorOptionsResponse
{
  "store": "centr",
  "flowers": [{"slug": "troyanda-red", "name": "Троянда червона",
               "color": "red", "price_per_stem": "45.00",
               "max_qty": 51, "image_url": "..."}],
  "addons": [{"slug": "eucalyptus", "name": "Евкаліпт",
              "kind": "greenery", "price": "35.00", "image_url": "..."}],
  "limits": {"min_stems": 3, "max_stems": 101, "max_positions": 5}
}
```

Отдаются только позиции с `is_active AND qty_available > 0` на этой точке. Недоступного в ответе нет — клиент физически не может собрать невозможный букет.

### 5.4. Конструктор — расчёт цены

```
POST /api/v1/constructor/price/
Body: ConstructorPriceRequest
{
  "store": "centr",
  "flowers": [{"slug": "troyanda-red", "qty": 15}],
  "addons": ["eucalyptus", "kraft"]
}
→ 200 ConstructorPriceResponse
{
  "subtotal": "710.00",
  "breakdown": [
    {"label": "Троянда червона × 15", "amount": "675.00"},
    {"label": "Евкаліпт", "amount": "35.00"}
  ],
  "composition_snapshot": {
    "flowers": [{"slug": "troyanda-red", "name": "Троянда червона",
                 "qty": 15, "unit_price": "45.00"}],
    "addons": [{"slug": "eucalyptus", "name": "Евкаліпт",
                "price": "35.00"}],
    "store": "centr",
    "priced_at": "2026-08-06T10:15:00Z"
  },
  "note": "флорист збере в цьому складі, форма може трохи відрізнятися"
}
```

`composition_snapshot` — ровно то, что кладётся в `OrderItem.composition_snapshot`. Формат заморожен. Клиент не пересчитывает цену у себя, сервер — единственный источник.

Расчёт живёт в `constructor/domain.py::calculate_price` — чистая функция, без БД, вход — dataclass с ценами. Тестируется property-based (§10).

3D-визуализацию не делаем. Показываем список состава + референс-фото + подпись `note`. Это дорого, не совпадает с реальностью и разрушает доверие сильнее, чем честная подпись.

### 5.5. Корзина

Хранится в сессии (Redis), не в БД. Анонимно, без регистрации.

```
GET    /api/v1/cart/                 → CartResponse
POST   /api/v1/cart/items/           → CartResponse   (AddCartItemRequest)
PATCH  /api/v1/cart/items/{item_id}/ → CartResponse   ({"qty": 2})
DELETE /api/v1/cart/items/{item_id}/ → CartResponse
```

```json
AddCartItemRequest
{"kind": "product", "product_slug": "buket-vesna", "qty": 1}
или
{"kind": "custom", "composition_snapshot": { ...из §5.4... }, "qty": 1}
```

```json
CartResponse
{"items": [{"item_id": "a1b2", "kind": "product", "title": "Букет Весна",
            "unit_price": "890.00", "qty": 1, "line_total": "890.00",
            "image_url": "...", "store": "centr"}],
 "subtotal": "890.00",
 "count": 1,
 "store": "centr"}
```

Инварианты корзины:

- Корзина привязана к одной точке. Смена точки при непустой корзине → 409 `conflict` с `{"action": "confirm_clear_cart"}`. Молча чистить корзину запрещено.
- `custom`-позиция ревалидируется сервером при добавлении: `composition_snapshot` пересчитывается заново, расхождение с присланной ценой → пересчёт по серверу, клиенту возвращается актуальная сумма. Цену с клиента не принимаем никогда.
- Позиция, ставшая недоступной на точке, помечается в ответе `"unavailable": true` и не даёт пройти в оформление.

### 5.6. Оформление заказа

Форма — минимум полей, регистрации нет. Адрес получателя спрашивается **только** при `fulfillment_type = taxi`.

```
POST /api/v1/orders/
Headers: Idempotency-Key: <uuid4>
Body: CreateOrderRequest
{
  "store": "centr",
  "fulfillment_type": "taxi",
  "recipient_name": "Олена",
  "recipient_phone": "+380671234567",
  "delivery_address": "вул. Хрещатик, 1, кв. 5",
  "desired_date": "2026-08-07",
  "desired_time_slot": "13-16",
  "customer_name": "Стас",
  "customer_phone": "+380509876543",
  "card_text": "З днем народження!",
  "payment_method": "online",
  "comment": "",
  "consent": true,
  "utm": {"source": "google"}
}
→ 201 CreateOrderResponse
{
  "public_id": "01J8Z...",
  "status_url": "/order/01J8Z.../a1b2c3.../",
  "total": "890.00",
  "delivery_fee": null,
  "next_action": "manager_will_call",
  "payment": null
}
```

`next_action` — закрытый набор: `manager_will_call` (такси, сумма ещё не известна), `redirect_to_payment` (тогда `payment.invoice_url` заполнен), `wait_for_pickup`.

Порядок для `taxi + online`: заказ создаётся в `new`, оплата **не** инициируется. Менеджер проставляет `delivery_fee` в админке → заказ уходит в `awaiting_payment` → клиенту летит ссылка на оплату. Инициировать оплату раньше — нарушение `INV-2`.

```
GET /api/v1/orders/{public_id}/{access_token}/ → OrderStatusResponse
{"public_id": "...", "status": "awaiting_payment",
 "status_label": "Очікує оплати", "total": "1010.00",
 "delivery_fee": "120.00", "payment_url": "https://...",
 "items": [...], "store": {...}, "updated_at": "..."}
```

Доступ строго по паре `public_id + access_token`. Перебор `public_id` без токена даёт 404. Это защита от IDOR: в заказе лежат имя, телефон и адрес получателя.

### 5.7. Вебхуки платежей

```
POST /api/v1/payments/{provider}/callback/
```

Обязательный порядок обработки, менять нельзя:

1. Прочитать сырое тело **до** любого разбора.
2. Проверить подпись провайдера. Невалидна → 400, запись `PaymentEvent(signature_valid=False)`, обработка прекращается.
3. Валидировать payload Pydantic-схемой провайдера.
4. Записать `PaymentEvent`. Конфликт по `(provider, event_id)` → 200 и выход. Это идемпотентность.
5. Перевести `Payment` и заказ через `transition_order` в `transaction.atomic`.
6. Отдать 200 быстро. Тяжёлое (SMS, Telegram) — в Celery через `on_commit`.

Сумму и валюту сверять с `Payment.amount`. Расхождение → статус `failed`, алерт менеджеру, заказ не переводится в `paid`.

### 5.8. Rate limiting (django-ratelimit)

| Эндпоинт | Лимит |
|---|---|
| `POST /api/v1/orders/` | 5/час на IP, 3/час на телефон |
| `POST /api/v1/constructor/price/` | 60/мин на IP |
| `POST /api/v1/cart/*` | 120/мин на IP |
| `GET /api/v1/live/` | 60/мин на IP — эндпоинт выдаёт подписанные ссылки на поток |
| `POST /reviews/` | 3/сутки на IP |
| Вебхуки | не лимитируются, защищены подписью |

Превышение → 429 `rate_limited`.

---

## 6. Pydantic: где применяется

Pydantic 2 — на всех границах системы. Внутри домена — `dataclass` или Pydantic-модели без Django.

1. **Настройки** — `config/settings/env.py`, `pydantic_settings.BaseSettings`. Все переменные окружения типизированы, отсутствие обязательной переменной валит приложение на старте, а не в рантайме. `os.getenv` в коде вне этого модуля запрещён.
2. **Вход JSON-эндпоинтов** — `<app>/schemas.py`, `*Request`.
3. **Выход JSON-эндпоинтов** — `*Response`.
4. **Payload задач Celery** — §7. Задача принимает `dict`, первой строкой валидирует его схемой.
5. **Payload вебхуков платежей** — схема на каждого провайдера.
6. **Ответы внешних API** — ответ платёжного провайдера и SMS-шлюза парсится схемой, а не `response.json()["foo"]`.
7. **`composition_snapshot`** — схема `CompositionSnapshot`, валидируется при записи и при чтении.

Правила: `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`. Деньги — `Decimal`, не `float`. Телефон — кастомный тип `PhoneNumber` с нормализацией в валидаторе.

---

## 7. Контракты Celery (заморожены)

Общие правила, нарушение — красное ревью:

- Аргументы задачи — только примитивы (id, строки, dict). Django-модель в аргументах запрещена: она устаревает и не сериализуется.
- Первая строка тела задачи — валидация payload Pydantic-схемой из `<app>/schemas.py`.
- **Каждая задача идемпотентна.** Второй запуск с тем же payload даёт ровно один эффект. Механизм: либо уникальный ключ в БД, либо `SETNX` в Redis на `task:{name}:{key}` с TTL, либо проверка целевого состояния перед действием.
- Задачи публикуются через `transaction.on_commit`.
- `autoretry_for`, `retry_backoff=True`, `retry_jitter=True`, `max_retries` задан явно. Бесконечных ретраев нет.
- `acks_late=True`, `task_reject_on_worker_lost=True`.
- В логах задачи нет телефона, адреса и текста открытки. Только `order.public_id`.

| Задача | Очередь | Payload | Идемпотентность | Retry |
|---|---|---|---|---|
| `notifications.notify_manager_new_order` | `notifications` | `{"order_public_id": str}` | Redis-ключ `notified:new_order:{public_id}`, TTL 24 ч | 5, backoff 10 c |
| `notifications.send_customer_sms` | `notifications` | `{"order_public_id": str, "template": str}` | ключ `sms:{public_id}:{template}` | 5, backoff 30 c |
| `notifications.notify_manager_payment_failed` | `notifications` | `{"payment_id": int}` | ключ по `payment_id` | 3 |
| `payments.poll_payment_status` | `payments` | `{"payment_id": int}` | проверка `Payment.status` — терминальный статус не трогается | 10, backoff 60 c |
| `payments.expire_stale_payments` | `payments` | `{}` (beat, каждые 15 мин) | переводит только `pending` старше 60 мин | 3 |
| `live.grab_stream_snapshot` | `media` | `{"stream_id": int}` (beat, каждые 10 мин) | пропускает, если снапшот моложе 5 мин | 3, backoff 30 c |
| `live.check_stream_health` | `default` | `{"stream_id": int}` (beat, каждые 2 мин) | пишет только при смене `health_status` | 3 |
| `live.cleanup_snapshots` | `media` | `{}` (beat, 03:00 Europe/Kyiv) | удаляет старше 48 ч, повтор ничего не меняет | 3 |
| `catalog.generate_image_renditions` | `media` | `{"model": str, "pk": int}` | пропускает, если рендишены существуют | 3 |
| `gallery.generate_image_renditions` | `media` | `{"gallery_item_id": int}` | пропускает, если рендишены существуют | 3 |
| `orders.release_abandoned_orders` | `default` | `{}` (beat, каждый час) | отменяет только `new` старше 48 ч без оплаты | 3 |
| `orders.send_status_change_notification` | `notifications` | `{"order_public_id": str, "to_status": str}` | ключ `{public_id}:{to_status}` | 5 |
| `orders.anonymize_old_orders` | `default` | `{}` (beat, 04:00 Europe/Kyiv) | берёт только `anonymized_at IS NULL` и `completed` старше 180 дней | 3 |
| `common.ping` | `default` | `{"nonce": str}` | Redis-ключ `ping:{nonce}`, TTL 1 ч | 3 |

`common.ping` — демо-задача скелета. Она же эталон: любая новая задача копирует её структуру (валидация payload схемой → проверка ключа идемпотентности → работа → запись ключа).

Очереди: `default`, `notifications`, `payments`, `media`. Воркеры разделены, чтобы медленная генерация превью не блокировала уведомление менеджеру о новом заказе.

Redis-БД: `0` — cache, `1` — sessions, `2` — celery broker/result.

---

## 8. UI-примитивы (собираются до фич)

Лежат в `templates/ui/`, подключаются через `{% include %}` с явными параметрами. Своя вёрстка кнопки в фиче — красное ревью.

| Компонент | Файл | Параметры |
|---|---|---|
| Button | `ui/button.html` | `variant` (primary/secondary/ghost/danger), `size`, `label`, `href`, `hx_*`, `disabled` |
| Input | `ui/input.html` | `name`, `label`, `type`, `value`, `error`, `required`, `placeholder`, `autocomplete` |
| PhoneInput | `ui/phone_input.html` | `name`, `value`, `error` — маска `+380 (__) ___-__-__` |
| Textarea | `ui/textarea.html` | `name`, `label`, `value`, `maxlength`, `counter` |
| Select | `ui/select.html` | `name`, `options`, `value`, `label`, `error` |
| RadioCard | `ui/radio_card.html` | `name`, `value`, `title`, `description`, `price_hint`, `checked` — варианты получения |
| ProductCard | `ui/product_card.html` | `product`, `store`, `show_price`, `lazy` |
| Badge | `ui/badge.html` | `text`, `tone` (neutral/success/warning/danger) |
| Modal | `ui/modal.html` | `id`, `title`, `body_slot`, `size` |
| Drawer | `ui/drawer.html` | `id`, `side` — мобильные фильтры и корзина |
| Toast | `ui/toast.html` | `message`, `tone` — рендерится по `HX-Trigger` |
| StoreSwitcher | `ui/store_switcher.html` | `stores`, `current` |
| LivePlayer | `ui/live_player.html` | `stream`, `state`, `playback`, `aspect_ratio`, `poster_url`, `compact` — окно камеры, §8.1 |
| LiveBadge | `ui/live_badge.html` | `state`, `label` — пульсирующая метка LIVE / «Зачинено» / «Офлайн» |
| GalleryGrid | `ui/gallery_grid.html` | `items`, `columns`, `lazy` — masonry-сетка работ |
| FilterChips | `ui/filter_chips.html` | `groups`, `active`, `hx_target` — фильтры галереи и каталога |
| PriceTag | `ui/price_tag.html` | `amount`, `old_amount`, `size` |
| QtyStepper | `ui/qty_stepper.html` | `name`, `value`, `min`, `max` |
| Stepper | `ui/stepper.html` | `steps`, `current` — шаги оформления |
| EmptyState | `ui/empty_state.html` | `icon`, `title`, `text`, `action_slot` |
| Skeleton | `ui/skeleton.html` | `kind` (card/line/image) |
| Breadcrumbs | `ui/breadcrumbs.html` | `items` |
| Pagination | `ui/pagination.html` | `page_obj`, `query` |
| DeliveryNote | `partials/delivery_note.html` | `options` — блок §1.2, один на весь сайт |

Все примитивы отрисованы на служебном роуте `/__kitchen-sink/` (доступен только при `DEBUG` или для staff). Это приёмочный критерий скелета.

Токены дизайна — только `tailwind.config.js`: палитра, радиусы, тени, шрифты. Хардкод `#hex` в шаблонах запрещён.

Навигация — **данные, не разметка**: `apps/pages/navigation.py::MAIN_NAV` — список пунктов. Layout рендерит его циклом. Добавление пункта = правка одного списка.

### 8.1. Окно камеры — спецификация оформления

Видео из магазина по умолчанию выглядит как кадр с камеры наблюдения: серо, мутно, дёшево. Всё оформление ниже решает ровно одну задачу — превратить это в витрину, которой доверяют. Требования обязательные, не декоративные.

**Рамка и посадка**

- Контейнер держит `aspect-ratio` из `LiveStream.aspect_ratio`. Макет не прыгает при загрузке потока — место зарезервировано сразу.
- Скруглённая рамка (`rounded-2xl`), внутренняя тень по краю кадра, мягкое внешнее свечение в фирменной палитре. Рамка выглядит как окно в магазин, а не как встроенный видеофайл.
- Тонкая градиентная подложка сверху и снизу кадра — на ней читаются оверлеи независимо от того, что в кадре.
- Один и тот же компонент в двух размерах: `compact` (блок на главной, 16:9, без оверлеев кроме бейджа) и полный (страница `/live/`).

**Оверлеи**

- Слева сверху — `LiveBadge`: точка с мягкой пульсацией (`animation: pulse 2s infinite`) и подпись «НАЖИВО». Пульсация отключается при `prefers-reduced-motion`.
- Справа сверху — название точки и адрес мелким шрифтом.
- Снизу — панель: кнопка полноэкранного режима, кнопка «Оновити», индикатор задержки при `latency_hint_s > 20`.
- Поверх кадра снизу справа — кнопка `Button primary` «Зателефонувати і запитати» с телефоном точки. Это главный смысл камеры: человек увидел что-то живьём и сразу спрашивает.
- Оверлеи не перекрывают центр кадра. Товар важнее интерфейса.

**Переключение точек**

Две вкладки-таба над окном (`Центр` / `Позняки`) с превью-снапшотом на каждой. Переключение — HTMX-заменой окна, без перезагрузки страницы. Выбранная точка синхронизирована с общим `store`-cookie (§5.1): переключил камеру — переключился и каталог.

**Состояния (по `state` из §5.2)**

- `live` — плеер играет. Автовоспроизведение только `muted` и `playsinline`, иначе iOS и мобильный Chrome его заблокируют. Звука нет по определению (§10.8).
- `closed` — постер из последнего снапшота, затемнённый, поверх — «Зараз зачинено» и время открытия. Кнопка «Дивитись галерею робіт» ведёт в `/gallery/`.
- `offline` — постер, честный текст «Камера тимчасово недоступна, ми вже розбираємось», телефон точки, ссылка на галерею. Никаких технических деталей ошибки.
- `disabled` — секция не рендерится вообще. Пустого места в макете не остаётся.
- Загрузка — `Skeleton` в размер кадра, поверх постера, не белый прямоугольник.

**Поведение и производительность**

- Поток не грузится, пока окно не попало в вьюпорт (`IntersectionObserver`). Камера на главной не съедает мобильный трафик у того, кто до неё не долистал.
- Первым кадром показывается постер-снапшот в WebP — окно выглядит наполненным ещё до старта потока.
- Вкладка ушла в фон → воспроизведение ставится на паузу. Вернулась → продолжается.
- Потеря сети → до трёх попыток переподключения с backoff, дальше состояние `offline` с кнопкой «Спробувати ще».
- Экономия трафика: на соединении `save-data` или `2g` поток не стартует автоматически, показывается постер и кнопка «Увімкнути трансляцію».
- Плеер (`hls.js`) грузится динамическим импортом только на страницах с камерой, не в общем бандле.

**Доступность**

`<video>` без звука не требует субтитров, но требует текстовой альтернативы: рядом всегда есть блок «Що зараз у наявності» со ссылкой на каталог выбранной точки. Клавиатурная навигация по всем кнопкам оверлея, видимый фокус, `aria-label` на каждой.

---

## 9. Требования к коду

### 9.1. ООП и проектирование

- Каждый внешний сервис — абстрактный базовый класс + фейк + реальная реализация. Обязательный набор с первого дня:
  - `payments.clients.base.PaymentProvider` (ABC): `create_invoice(order: OrderDTO) -> InvoiceDTO`, `verify_signature(raw: bytes, headers: Mapping) -> bool`, `parse_callback(payload: dict) -> PaymentResult`, `fetch_status(provider_payment_id: str) -> PaymentStatus`.
  - `notifications.clients.base.SmsClient` (ABC): `send(phone: str, text: str) -> SmsResult`.
  - `notifications.clients.base.MessengerClient` (ABC): `send_message(chat_id: str, text: str) -> None`.
  - `live.clients.base.StreamProvider` (ABC): интерфейс в §4.3.
  - Фейки: `FakePaymentProvider`, `FakeSmsClient`, `FakeMessengerClient`, `FakeStreamProvider` — пишут в БД/лог, умеют возвращать ошибку или «офлайн» по флагу. Разработка идёт против фейков с первого дня, реальные ключи и физические камеры не блокируют ничего.
- Реализация выбирается через фабрику по настройке `PAYMENT_PROVIDER` / `SMS_PROVIDER` / `STREAM_PROVIDER`. Импорт конкретного класса в сервисе запрещён.
- Зависимости передаются в конструктор use-case, не создаются внутри. Это делает тест без моков-патчей.
- Наследование — только там, где есть реальная общность. Композиция по умолчанию. Глубина иерархии больше двух — красное ревью.
- Singleton, глобальное состояние, изменяемые модульные переменные запрещены.
- Магические числа и строки — в `Enum` / `TextChoices` / константы модуля. Строковый литерал статуса в коде вне `OrderStatus` запрещён.
- Функция длиннее ~50 строк или с вложенностью больше 3 — разбивается.
- Дублирование бизнес-правила в двух местах — красное ревью. Правило живёт в домене в одном экземпляре.

### 9.2. Типы, стиль, инструменты

- Type hints обязательны на всех публичных функциях и методах. `mypy --strict` на `apps/*/domain.py`, `services.py`, `schemas.py`, `clients/`. Остальное — обычный режим.
- `ruff` (lint + format), правила: `E,F,I,N,UP,B,S,C4,DJ,PT,RUF`. `# noqa` только с указанием кода и причины.
- Docstring — на публичных сервисах и доменных функциях: что делает и какие инварианты держит. Не пересказ кода.
- Комментарии объясняют **почему**, не **что**. Закомментированный код в PR не остаётся.
- Язык всего технического текста — английский: имена, коммиты, PR, комментарии, docstrings. Пользовательские строки — украинский, через `gettext`.

### 9.3. Конвенция коммитов и PR

- Conventional Commits, всегда: `type(scope): summary`. `type` ∈ `feat|fix|test|refactor|chore|docs|perf`. `scope` — имя приложения (`orders`, `catalog`, `payments`). `summary` — императив, со строчной, без точки, до ~50 символов.
- Пример: `feat(orders): add delivery fee gate before payment`.
- Коммиты маленькие и по ходу работы, не один большой в конце. Каждый коммит по возможности проходит тайпчек.
- Тело коммита — только чтобы объяснить *почему*.
- PR: заголовок с ID задачи, тело — что делает слайс, какие контракты затрагивает, чем покрыт тестами.
- Ветка: `feat/<issue-id>-short-slug`.

### 9.4. Definition of Done одной задачи

1. `ruff check` и `ruff format --check` зелёные.
2. `mypy` зелёный на затронутых строгих модулях.
3. Миграции сгенерированы и применяются на чистой БД; `makemigrations --check --dry-run` не находит незакоммиченных изменений.
4. Тесты по доктрине §10 написаны и зелёные. Тесты выведены из критериев приёмки, не из реализации.
5. `bandit` без новых находок уровня medium+.
6. Страница/эндпоинт проверены руками на мобильном разрешении 375px.
7. Задача привязана к PR, PR смёржен через CI-гейт.

---

## 10. Безопасность (требования, не пожелания)

### 10.1. Django-настройки прода

```
DEBUG = False
ALLOWED_HOSTS — явный список
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000, INCLUDE_SUBDOMAINS, PRELOAD
SESSION_COOKIE_SECURE = True, HTTPONLY = True, SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True, CSRF_COOKIE_HTTPONLY = False, SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS — явный список
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 MB
```

`python manage.py check --deploy` без предупреждений — приёмочный критерий стадии 8.

CSP через `django-csp`: `default-src 'self'`, инлайновые скрипты запрещены (Alpine подключается файлом, `unsafe-eval` для Alpine закрывается сборкой CSP-билда Alpine).

### 10.2. Инъекции и вывод

- Только ORM и параметризованные запросы. `raw()` и `extra()` запрещены без ADR.
- Автоэкранирование шаблонов не отключается. `|safe` и `mark_safe` — только на поле `StaticPage.body`, предварительно очищенном `nkleach`/`bleach` по белому списку тегов.
- Текст отзыва и текст открытки экранируются везде, включая Telegram-сообщение менеджеру (Telegram HTML-разметка — отдельный экранировщик).
- Имена файлов при загрузке не доверяются: генерируется UUID-имя, расширение выводится из содержимого.

### 10.3. Загрузка изображений

Менеджер грузит фото работ в галерею пачками с телефона — это самая живая точка входа файлов в системе.

- Whitelist MIME по содержимому (Pillow `Image.open` + `verify()`), не по расширению.
- Максимум 10 МБ, максимум 8000×8000 px (защита от decompression bomb).
- Файл пересохраняется через Pillow (re-encode) — это убивает вложенный полезный груз и EXIF.
- EXIF-геотеги вырезаются: фото из магазина не должно раскрывать координаты.
- Медиа отдаются с `X-Content-Type-Options: nosniff`; каталог медиа не исполняет ничего.

### 10.4. Персональные данные

В заказе лежат имя, телефон и адрес третьего лица (получателя). Обращение с ними:

- Страница статуса доступна только по паре `public_id + access_token`. Один `public_id` в URL — недостаточно.
- Телефон и адрес не попадают в логи, в Sentry (`before_send` вырезает поля), в аналитику и в URL.
- Экспорт заказов из админки — только для группы `manager`, каждый экспорт пишется в `AuditLog`.
- Ретеншн: `delivery_address`, `recipient_phone`, `card_text` обнуляются задачей `orders.anonymize_old_orders` через 180 дней после `completed`. Агрегаты для отчётов остаются.
- Согласие на обработку — чекбокс `consent` в оформлении, обязательный, дата и версия текста политики сохраняются.

### 10.5. Аутентификация и админка

- Публичная часть анонимна: регистрации нет, паролей клиентов нет, значит и утекать нечему. Это осознанное решение, не упущение.
- Админка на `/manage/` (не `/admin/`), закрыта rate-limit'ом (`django-axes`: 5 попыток, блок 30 мин) и обязательной 2FA (`django-otp`) для всех staff.
- Роли-группы: `manager` (заказы, галерея, камера, остатки, отзывы), `florist` (галерея, остатки), `owner` (всё + экспорт + настройки + kill switch камеры). Права выдаются группе, не пользователю.
- Действия в админке над заказами и платежами пишутся в `AuditLog` (кто, что, когда, старое → новое значение).
- Сессия staff — 8 часов, `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` для staff.

### 10.6. Платежи

- Карточные данные на сайт не попадают никогда: только редирект/виджет провайдера. PCI-скоуп минимальный.
- Подпись вебхука проверяется до разбора тела, сравнение — `hmac.compare_digest`.
- Сумма из вебхука сверяется с `Payment.amount`. Расхождение → `failed` + алерт.
- Идемпотентность по `(provider, event_id)` на уровне БД-констрейнта, не на уровне `if`.
- Секреты провайдера — только в env, в БД и в репозитории их нет. `raw_response` перед сохранением чистится от полей с PAN/CVV.

### 10.7. Прочее

- Секреты — `.env`, в репозитории только `.env.example` с пустыми значениями. Гит-хук `detect-secrets` в pre-commit.
- Зависимости пинуются (`uv`/`pip-tools`), `pip-audit` в CI, обновление раз в месяц.
- Бэкап Postgres ежедневно, хранение 30 дней, восстановление проверяется раз в квартал (иначе это не бэкап).
- `/healthz/` отдаёт статус БД, Redis, Celery. Без раскрытия версий.
- Ошибки 500 не показывают трейс. Sentry с `send_default_pii=False`.
- Антиспам форм: honeypot-поле + проверка времени заполнения (< 3 c → отказ) + rate-limit. Капча подключается только если спам пробьёт эти три.

---

### 10.8. Приватность видеосъёмки (обязательно к исполнению)

Публичная трансляция из торгового зала снимает покупателей и продавцов. Это обработка персональных данных по ЗУ «Про захист персональних даних» и по GDPR, если поток доступен из ЕС. Требования ниже — не перестраховка: публичный стрим с узнаваемыми лицами и суммами покупок это реальный иск и реальный репутационный удар.

**Постановка камеры**

- Камера направлена на **холодильник и стеллаж с цветами**. Касса, терминал, экран POS, рабочее место продавца и зона очереди в кадр не попадают. Ракурс согласуется до монтажа, скриншот ракурса прикладывается к issue.
- Лица покупателей в кадре — случайные и нечитаемые. Если ракурс это не обеспечивает, ставится размытие зоны (`MediaMTX` + фильтр `ffmpeg`) или камера перевешивается. Компромисс тут не ищется.
- Разрешение выбирается минимально достаточное для «видно, какие цветы»: 720p хватает. 4K даёт читаемые лица и никакой пользы продукту.

**Звук**

Звук не передаётся никогда. `LiveStream.has_audio` всегда `False`, аудиодорожка вырезается на рестримере (`-an`), плеер отдаётся без аудиоканала. Запись разговоров в магазине без согласия сторон незаконна, и это единственный пункт раздела, у которого нет технических альтернатив.

**Хранение**

- Публичный архив трансляции не ведётся. Перемотка назад недоступна: HLS отдаётся с коротким окном (`playlist` 3–4 сегмента, `EXT-X-PLAYLIST-TYPE: EVENT` не используется).
- Снапшоты хранятся 48 часов и чистятся `live.cleanup_snapshots`. Снапшот с людьми в кадре не публикуется как постер: задача проверяет кадр и при обнаружении силуэтов в зоне у кассы берёт следующий. Простой вариант первой итерации — брать снапшот только вне часов пиковой посещаемости.
- Скачивание потока с сайта не предлагается. Кнопки «записать» нет.

**Информирование**

- Табличка на входе в магазин: ведётся видеотрансляция в интернет, кто оператор, куда обращаться. Это требование закона, а не вежливость.
- Раздел в политике конфиденциальности: что снимается, что не снимается, что звука нет, что архива нет, срок хранения снапшотов, контакт для обращений.
- Персонал предупреждён письменно и согласие получено до включения трансляции.

**Техническая защита источника**

- RTSP-URL, логин и пароль камеры хранятся только в env рестримера. В БД, в репозитории и в ответах API их нет. `LiveStream.source_ref` — публично безопасный идентификатор.
- Камера в отдельном VLAN, из интернета напрямую недоступна. Наружу торчит только рестример.
- Дефолтный пароль камеры меняется до подключения, прошивка обновляется. Незакрытая IP-камера это точка входа в сеть магазина, а не только утечка видео.
- Публичная ссылка на поток подписывается (HMAC + TTL 5 мин) и выдаётся эндпоинтом `/api/v1/live/`. Прямой постоянный адрес m3u8 наружу не публикуется — иначе его встроят на чужие сайты и весь трафик оплатите вы.
- Рестример за rate-limit и за `Referer`-проверкой; нагрузка на VPS ограничена (`maxReaders`), чтобы поток не уронил сайт.
- Kill switch: `LiveStream.is_enabled = False` в админке гасит трансляцию мгновенно и без деплоя. Менеджер обязан знать, где эта галочка.

## 11. Стратегия тестов

Главная ловушка: сессия пишет код, потом пишет тесты, которые подтверждают, что код делает то, что делает — вместе с багами. Тесты зелёные и не проверяют ничего.

**Правило: тест выводится из критериев приёмки задачи, не из реализации. Тест кодирует контракт.**

Практическое следствие: тест пишется по формулировке критерия приёмки из `DEV.md` до или параллельно с кодом. Если тест невозможно написать, не подсмотрев в реализацию — критерий приёмки сформулирован плохо, надо переформулировать.

### 11.1. Обязательные типы тестов на каждый слайс

1. **Доменные (unit, без БД).** Инварианты из §4.6, расчёт цены, правила доступности. Быстрые, их большинство.
2. **Контрактные на стыках.** JSON-эндпоинт отвечает ровно схемой из §5: ответ парсится Pydantic-моделью `*Response` — расхождение валит тест. Payload Celery-задачи валидируется схемой. Фейковый клиент — это тестовый шов: он валидирует вход против контракта и падает, если слайс шлёт мусор.
3. **Идемпотентность.** На каждую Celery-задачу — тест, который гоняет её дважды с тем же payload и проверяет, что эффект ровно один. На вебхук — тест повторной доставки того же `event_id`. Без этого получаем двойные списания и два SMS клиенту в 7 утра.
4. **Путь ошибки.** Фейк возвращает 500 / таймаут / невалидную подпись. Проверяется: заказ не переходит в `paid`, ретрай происходит, менеджер получает алерт, пользователь видит понятное сообщение.
5. **Property-based (hypothesis).** На чистой доменной логике. Генерируем входы, проверяем инварианты:
   - расчёт цены никогда не даёт отрицательную сумму;
   - `total == subtotal + delivery_fee` при любых валидных входах;
   - сумма `breakdown` равна `subtotal` с точностью до копейки;
   - последовательность любых разрешённых переходов не приводит в невалидное состояние;
   - `normalize_phone` идемпотентна: `f(f(x)) == f(x)`.
6. **E2E (Playwright), только на критическом пути.** Три сценария, не больше: покупка готового букета самовывозом; сборка в конструкторе → заказ такси → менеджер ставит цену → оплата; отправка отзыва. E2E дорогие, покрывать ими всё запрещено.

### 11.2. Инструменты и правила

- `pytest` + `pytest-django`, фикстуры в `conftest.py`, фабрики `factory-boy` (одна фабрика на модель, никаких хардкод-объектов в тестах).
- Одна БД-фикстура на модуль, `--reuse-db` локально.
- Внешние HTTP не вызываются в тестах никогда. Реальные клиенты подменяются фейками через настройку, не через `mock.patch` (патч ломается при рефакторинге, фабрика — нет).
- Время замораживается `freezegun`, где логика зависит от даты (расписание камеры, ретеншн, слоты доставки).
- Тест именуется по проверяемому правилу: `test_taxi_order_cannot_reach_paid_without_delivery_fee`, не `test_order_2`.
- Покрытие не самоцель, но `apps/*/domain.py` и `apps/*/services.py` — минимум 90%, гейт в CI.
- Флаки-тест чинится или удаляется в тот же день. Отключённый тест с `skip` без issue — красное ревью.

### 11.3. Гейт CI

PR-гейт (без деплоя): `ruff`, `mypy`, `makemigrations --check`, `pytest` (unit + integration + contract) на эфемерном Postgres и Redis, `bandit`, `pip-audit`, сборка Docker-образа, Playwright на трёх E2E-сценариях.
Мёрдж в `main`: миграции + деплой на тестовый VPS. Прод — по тегу вручную.

Слайс мёржится только с тестами. Гейт красный без них.

---

## 12. Владение инфраструктурой

Проект ведёт один разработчик, он же тимлид. Роли всё равно разделены: часть решений принимается «в режиме тимлида» и фиксируется в ядре, часть — «в режиме исполнителя» и фиксируется в коде. Смешивать нельзя, иначе контракты поплывут внутри одной головы.

- **Миграции** генерируются из моделей, применяются деплой-шагом, в PR-гейте прогоняются на эфемерном Postgres. Ручное редактирование сгенерированной миграции — только для `RunPython`-переносов данных, с комментарием и с обратной операцией.
- **Сид-скрипт** `scripts/seed.py` — общие фикстуры: 2 магазина, 12 цветов с остатками, 8 addon'ов, 15 товаров, 6 поводов, 2 `LiveStream` на фейк-провайдере (один `live`, один `offline` — чтобы оба состояния были видны сразу), 24 работы в галерее с тегами, 3 заказа в разных статусах, staff-пользователи трёх ролей. Фейки внешних клиентов отдают данные, согласованные с сидом.
- **Конфиг** — один модуль `config/settings/env.py` на pydantic-settings, `.env.example` заполнен всеми ключами с пустыми значениями и комментариями. Приложение запускается на фейках без единого реального секрета.
- **`docker compose up`** поднимает: web, postgres, redis, celery-worker (4 очереди), celery-beat, mailhog. Один шаг до рабочего окружения.

---

## 13. Дорожная карта по стадиям

Стадия — набор слайсов. Слайс — один PR. Детализация задач и критериев приёмки — в `DEV.md`.

| Стадия | Содержание | Выход |
|---|---|---|
| **0. Скелет** | репозиторий, docker compose, настройки на pydantic-settings, CI, base.html + навигация данными, UI-примитивы + kitchen-sink, Celery + демо-задача, фейки клиентов, сид, эталонная вертикаль (страница «Наши магазины» сверху донизу) | чек-лист скелета зелёный |
| **1. Каталог и магазины** | Store, Occasion, Flower, Product, доступность по точкам, переключатель точки, листинги по поводу/цветку/цене, карточка товара с блоком получения | каталог живой, товары кликаются |
| **2. Живая камера и галерея** | `StreamProvider` + фейк, `LiveStream`, страница `/live/` с окном по §8.1, четыре состояния, снапшоты и health-check, переключение точек, блок на главной; `GalleryItem` с фильтрами | клиент видит зал вживую, галерея закрывает SEO и ночные часы |
| **3. Конструктор** | опции по точке, расчёт цены на сервере, островок Alpine, снапшот состава, подпись про форму букета | из конструктора можно положить в корзину |
| **4. Корзина и оформление** | корзина в сессии, привязка к точке, форма оформления (5 блоков), три варианта получения, открытка, машина статусов, страница статуса заказа | заказ создаётся и виден менеджеру |
| **5. Уведомления** | Telegram менеджеру, SMS клиенту, уведомления на смену статуса, алерты | менеджер узнаёт о заказе за 10 секунд |
| **6. Оплата** | платёжная абстракция → реальный провайдер (LiqPay/Monobank/WayForPay), вебхуки, гейт `delivery_fee`, оплата при получении и переводом | онлайн-оплата работает end-to-end |
| **7. Контент и SEO** | отзывы с премодерацией, статические страницы, `sitemap.xml`, `robots.txt`, микроразметка Product/LocalBusiness, OG-теги, аналитика | страницы индексируются, галерея даёт объём контента |
| **8. Харденинг и запуск** | `check --deploy` чистый, CSP, бэкапы + проверка восстановления, нагрузочный прогон, Sentry, прод-деплой, инструкция менеджеру | боевой запуск |

Long-lead (запускать в день один, параллельно разработке): договор и ключи платёжного провайдера, аккаунт SMS-шлюза с подписью отправителя, домен и TLS, бот Telegram, аккаунт S3-хранилища, **закупка и монтаж IP-камер на двух точках + согласование ракурса + табличка на входе + письменное согласие персонала**. Ни одна из этих вещей не блокирует разработку: всё пишется против фейков с первого дня, камера — против `FakeStreamProvider` с зацикленным роликом.

**Решение по источнику потока отложено осознанно.** `StreamProvider` — абстракция, конкретный вариант выбирается перед стадией 2 из трёх:

| Вариант | Плюсы | Минусы | Когда брать |
|---|---|---|---|
| MediaMTX/go2rtc на своём VPS | полный контроль, никакого чужого брендинга, WebRTC с задержкой < 1 с, свой плеер и своё оформление | трафик и CPU на VPS, свой аптайм, дороже при росте зрителей | если камера — заявленное преимущество магазина |
| YouTube Live (iframe) | нулевая инфраструктура и нулевой трафик, работает везде | брендинг и рекомендации YouTube поверх вашего сайта, задержка 15–30 с, оформление по §8.1 реализуется лишь частично | быстрый старт, проверка гипотезы |
| Сервис видеонаблюдения (Angelcam и подобные) | быстро, готовый плеер | абонплата, ограниченное оформление, зависимость от вендора | если нет желания администрировать поток |

Смена варианта после запуска — правка одной переменной окружения и одной реализации `StreamProvider`. Страница, оформление, состояния и тесты не переписываются. Ради этого абстракция и вводится.

---

## 14. Что не делаем в v1 (зафиксировано, чтобы не расползлось)

Регистрацию и личный кабинет. Программу лояльности и промокоды. 3D-визуализацию букета. Многоязычность. Интеграцию с API такси (менеджер называет цену руками — это и есть фича доверия). Мобильное приложение. Онлайн-чат. Подписку на регулярную доставку. Складской учёт глубже `qty_available`.

По камере отдельно: публичный архив и перемотку трансляции, звук, запись и скачивание потока, распознавание лиц и любую аналитику по посетителям, управление камерой (PTZ) с сайта, чат под трансляцией. Первые пять — сознательный отказ по §10.8, а не «не успели».

Каждый пункт — отдельный `CONTRACT GAP` и бамп версии ядра, если понадобится.
