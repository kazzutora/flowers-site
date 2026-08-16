#!/usr/bin/env python
"""Idempotent fixtures for development, tests and demos.

Every slice that adds a model appends to this script (section 18 of tech.md).
"""

import pathlib
from typing import Any

# Stand-in photographs for the occasion tiles and the hero, so a fresh database
# does not open with empty boxes. Provenance and licences in CREDITS.md there.
ASSETS = pathlib.Path(__file__).resolve().parent / "seed_assets"

# The name on the sign. The same in both languages: it is a name, not a phrase
# to translate.
SITE_NAME = "Квіткова Примха"
ADDRESS_UK = "вул. Дворецька, 125, Рівне"
ADDRESS_RU = "ул. Дворецкая, 125, Ровно"

# The shop is open around the clock, every day.
WORKING_HOURS_UK = "Цілодобово, без вихідних"
WORKING_HOURS_RU = "Круглосуточно, без выходных"

# The numbers the shop answers and the account it posts from. Stored in E.164:
# PhoneNumberField keeps whatever it is given, and `tel:` links have to carry
# the country code to work from a phone abroad.
PHONE_PRIMARY = "+380992050565"
PHONE_SECONDARY = "+380972050565"
INSTAGRAM_URL = "https://www.instagram.com/kvitkova_prymkha"

# The shop as Google Maps knows it. The query is the name and the address
# percent-encoded: Google resolves it to the same pin the owner's short link
# points to, and an embed built that way carries the shop's name instead of
# bare coordinates. Encoding is not cosmetic - Google answers a raw Cyrillic
# query with an empty map.
MAP_EMBED_URL = (
    "https://www.google.com/maps?q="
    "%D0%9A%D0%B2%D1%96%D1%82%D0%BA%D0%BE%D0%B2%D0%B0%20%D0%9F%D1%80%D0%B8%D0%BC%D1%85%D0%B0"
    "%2C%20%D0%B2%D1%83%D0%BB.%20%D0%94%D0%B2%D0%BE%D1%80%D0%B5%D1%86%D1%8C%D0%BA%D0%B0"
    "%2C%20125%2C%20%D0%A0%D1%96%D0%B2%D0%BD%D0%B5"
    "&z=17&hl=uk&output=embed"
)
# Directions go by coordinates: getting the visitor to the door must not depend
# on a text search resolving inside their navigation app.
MAP_DIRECTIONS_URL = "https://www.google.com/maps/dir/?api=1&destination=50.6098648%2C26.2294084"


def attach_photo(instance: Any, field_name: str, path: pathlib.Path) -> None:
    """Fill an empty image field from the bundled fixtures.

    Only when it is empty. These photographs are stand-ins until the owner
    uploads their own work, and `make seed` must not undo that upload. The
    files are already webp within the limits of section 14.2, so the squeeze
    on save has nothing left to do.
    """
    from django.core.files.base import ContentFile

    field = getattr(instance, field_name)
    if field or not path.exists():
        return
    field.save(path.name, ContentFile(path.read_bytes()), save=True)


def seed_site_settings() -> None:
    from apps.core.models import SiteSettings

    settings = SiteSettings.load()
    # Still demo: the owner has not given an address for either of these yet.
    settings.email = settings.email or "hello@example.com"
    settings.viber_url = settings.viber_url or "viber://chat?number=%2B380501112233"
    settings.telegram_url = settings.telegram_url or "https://t.me/example"
    # Assigned, not defaulted: unlike the demo contacts above these are the real
    # shop, so re-seeding a database that still carries the old name fixes it.
    settings.phone_primary = PHONE_PRIMARY
    settings.phone_secondary = PHONE_SECONDARY
    settings.instagram_url = INSTAGRAM_URL
    settings.site_name_uk = SITE_NAME
    settings.site_name_ru = SITE_NAME
    settings.address_uk = ADDRESS_UK
    settings.address_ru = ADDRESS_RU
    settings.map_embed_url = MAP_EMBED_URL
    settings.map_directions_url = MAP_DIRECTIONS_URL
    settings.pickup_text_uk = (
        settings.pickup_text_uk or "Можливість самостійно забрати ваше замовлення з магазину."
    )
    settings.pickup_text_ru = (
        settings.pickup_text_ru or "Возможность самостоятельно забрать ваш заказ из магазина."
    )
    settings.delivery_text_uk = (
        settings.delivery_text_uk or "Доставка по місту та Західній Україні згідно тарифів таксі."
    )
    settings.delivery_text_ru = (
        settings.delivery_text_ru or "Доставка по городу и Западной Украине согласно тарифов такси."
    )
    # Assigned rather than defaulted, for the same reason as the name and the
    # address above: the shop is open around the clock, and a database seeded
    # back when it kept daytime hours has to pick the correction up.
    settings.working_hours_uk = WORKING_HOURS_UK
    settings.working_hours_ru = WORKING_HOURS_RU
    settings.hero_title_uk = settings.hero_title_uk or "Квіти, які запам'ятовують"
    settings.hero_title_ru = settings.hero_title_ru or "Цветы, которые запоминают"
    settings.hero_subtitle_uk = (
        settings.hero_subtitle_uk or "Букети, композиції та оформлення залів ручної роботи."
    )
    settings.hero_subtitle_ru = (
        settings.hero_subtitle_ru or "Букеты, композиции и оформление залов ручной работы."
    )
    settings.save()
    attach_photo(settings, "hero_image", ASSETS / "hero.webp")


STATIC_PAGES: tuple[dict[str, Any], ...] = (
    {
        "slug": "pro-nas",
        "title_uk": "Про нас",
        "title_ru": "О нас",
        "seo_description_uk": f"{SITE_NAME}: букети, композиції та оформлення залів.",
        "seo_description_ru": f"{SITE_NAME}: букеты, композиции и оформление залов.",
        "body_uk": (
            "<p>Ми збираємо букети вручну і працюємо з квітами щодня. Кожна робота в"
            " галереї — наша, зроблена для конкретної людини і конкретного дня.</p>"
            "<h2>Як ми працюємо</h2>"
            "<p>Приймаємо замовлення по телефону, у Viber і Telegram. Ви називаєте номер"
            " роботи з галереї, дату і орієнтовний бюджет — ми підказуємо, що можливо"
            " саме зараз, і збираємо букет до потрібної години.</p>"
            "<h2>Про квіти</h2>"
            "<p>Асортимент залежить від сезону і поставки. Ми повторюємо роботу"
            " максимально близько до фото, а якщо якоїсь квітки немає — телефонуємо і"
            " пропонуємо заміну, а не ставимо перед фактом.</p>"
        ),
        "body_ru": (
            "<p>Мы собираем букеты вручную и работаем с цветами каждый день. Каждая"
            " работа в галерее — наша, сделанная для конкретного человека и конкретного"
            " дня.</p>"
            "<h2>Как мы работаем</h2>"
            "<p>Принимаем заказы по телефону, в Viber и Telegram. Вы называете номер"
            " работы из галереи, дату и ориентировочный бюджет — мы подсказываем, что"
            " возможно сейчас, и собираем букет к нужному часу.</p>"
            "<h2>О цветах</h2>"
            "<p>Ассортимент зависит от сезона и поставки. Мы повторяем работу"
            " максимально близко к фото, а если какого-то цветка нет — звоним и"
            " предлагаем замену, а не ставим перед фактом.</p>"
        ),
    },
    {
        "slug": "dostavka-i-oplata",
        "title_uk": "Доставка і оплата",
        "title_ru": "Доставка и оплата",
        "seo_description_uk": (
            "Доставка по місту, самовивіз із майстерні, оплата картою або готівкою."
        ),
        "seo_description_ru": (
            "Доставка по городу, самовывоз из мастерской, оплата картой или наличными."
        ),
        "body_uk": (
            "<h2>Доставка</h2>"
            "<p>Доставляємо по місту в узгоджений інтервал. Кур'єр телефонує за"
            " п'ятнадцять хвилин до приїзду. Якщо букет — сюрприз, ми не дзвонимо"
            " отримувачу заздалегідь, а домовляємось із вами.</p>"
            "<h2>Самовивіз</h2>"
            "<p>Забрати замовлення можна в майстерні у робочі години. Скажіть номер"
            " роботи — букет чекатиме зібраним.</p>"
            "<h2>Оплата</h2>"
            "<p>Картою за посиланням або готівкою при отриманні. Для оформлення залів"
            " беремо передоплату, розмір обговорюємо при замовленні.</p>"
        ),
        "body_ru": (
            "<h2>Доставка</h2>"
            "<p>Доставляем по городу в согласованный интервал. Курьер звонит за"
            " пятнадцать минут до приезда. Если букет — сюрприз, мы не звоним"
            " получателю заранее, а договариваемся с вами.</p>"
            "<h2>Самовывоз</h2>"
            "<p>Забрать заказ можно в мастерской в рабочие часы. Назовите номер"
            " работы — букет будет ждать собранным.</p>"
            "<h2>Оплата</h2>"
            "<p>Картой по ссылке или наличными при получении. Для оформления залов"
            " берём предоплату, размер обсуждаем при заказе.</p>"
        ),
    },
    {
        "slug": "faq",
        "title_uk": "Питання і відповіді",
        "title_ru": "Вопросы и ответы",
        "seo_description_uk": (
            "Коли замовляти, чи можна повторити букет із фото, скільки стоять квіти."
        ),
        "seo_description_ru": (
            "Когда заказывать, можно ли повторить букет с фото, сколько стоят цветы."
        ),
        "body_uk": (
            "<h2>За скільки замовляти?</h2>"
            "<p>Букет — за день, оформлення залу — за тиждень. У сезон свят краще"
            " заздалегідь: 8 березня і 1 вересня розбирають за кілька днів.</p>"
            "<h2>Чи можна повторити роботу з галереї?</h2>"
            "<p>Так. Назвіть номер роботи — повторимо максимально близько. Квіти можуть"
            " відрізнятися залежно від сезону та поставки.</p>"
            "<h2>Скільки коштує?</h2>"
            "<p>Ціна залежить від квітів і розміру. Назвіть орієнтир — підберемо"
            " варіант, який у нього вкладається.</p>"
            "<h2>Скільки стоїть букет?</h2>"
            "<p>Від трьох днів, якщо тримати у воді, підрізати стебла і не ставити"
            " на сонці чи біля батареї.</p>"
        ),
        "body_ru": (
            "<h2>За сколько заказывать?</h2>"
            "<p>Букет — за день, оформление зала — за неделю. В сезон праздников лучше"
            " заранее: 8 марта и 1 сентября разбирают за несколько дней.</p>"
            "<h2>Можно ли повторить работу из галереи?</h2>"
            "<p>Да. Назовите номер работы — повторим максимально близко. Цветы могут"
            " отличаться в зависимости от сезона и поставки.</p>"
            "<h2>Сколько стоит?</h2>"
            "<p>Цена зависит от цветов и размера. Назовите ориентир — подберём вариант,"
            " который в него укладывается.</p>"
            "<h2>Сколько стоит букет?</h2>"
            "<p>От трёх дней, если держать в воде, подрезать стебли и не ставить на"
            " солнце или у батареи.</p>"
        ),
    },
    {
        "slug": "polityka-konfidentsiynosti",
        "title_uk": "Політика конфіденційності",
        "title_ru": "Политика конфиденциальности",
        "seo_description_uk": "Які дані ми збираємо, навіщо і як довго зберігаємо.",
        "seo_description_ru": "Какие данные мы собираем, зачем и как долго храним.",
        "body_uk": (
            "<p>Ця сторінка пояснює, які дані ми збираємо і навіщо. Замініть контакти"
            " та реквізити на власні перед запуском.</p>"
            "<h2>Які дані ми збираємо</h2>"
            "<p>З форми заявки: ім'я, номер телефону, зручний спосіб зв'язку і те, що ви"
            " самі написали в коментарі. З форми відгуку: ім'я, текст, оцінку, за"
            " бажанням фото і телефон для зв'язку.</p>"
            "<h2>Навіщо</h2>"
            "<p>Щоб зателефонувати вам, узгодити замовлення і привезти квіти. Ми не"
            " передаємо ці дані третім особам і не надсилаємо розсилок.</p>"
            "<h2>IP-адреса</h2>"
            "<p>Ми не зберігаємо вашу IP-адресу. Замість неї зберігається необоротний"
            " хеш — він потрібен лише для захисту форм від автоматичних відправлень.</p>"
            "<h2>Cookie і аналітика</h2>"
            "<p>Обране зберігається у вашому браузері, а не в нас. Аналітика"
            " підключається лише після того, як ви натиснули «Прийняти» в банері"
            " внизу екрана, і показує знеособлену статистику відвідувань.</p>"
            "<h2>Скільки зберігаємо</h2>"
            "<p>Заявки й відгуки зберігаються, доки потрібні для роботи з замовленням."
            " Ви можете попросити нас видалити ваші дані — зателефонуйте або напишіть"
            " на пошту, вказану в контактах.</p>"
        ),
        "body_ru": (
            "<p>Эта страница объясняет, какие данные мы собираем и зачем. Замените"
            " контакты и реквизиты на свои перед запуском.</p>"
            "<h2>Какие данные мы собираем</h2>"
            "<p>Из формы заявки: имя, номер телефона, удобный способ связи и то, что вы"
            " сами написали в комментарии. Из формы отзыва: имя, текст, оценку, по"
            " желанию фото и телефон для связи.</p>"
            "<h2>Зачем</h2>"
            "<p>Чтобы позвонить вам, согласовать заказ и привезти цветы. Мы не передаём"
            " эти данные третьим лицам и не рассылаем писем.</p>"
            "<h2>IP-адрес</h2>"
            "<p>Мы не храним ваш IP-адрес. Вместо него хранится необратимый хеш — он"
            " нужен только для защиты форм от автоматических отправлений.</p>"
            "<h2>Cookie и аналитика</h2>"
            "<p>Избранное хранится в вашем браузере, а не у нас. Аналитика подключается"
            " только после того, как вы нажали «Принять» в баннере внизу экрана, и"
            " показывает обезличенную статистику посещений.</p>"
            "<h2>Сколько храним</h2>"
            "<p>Заявки и отзывы хранятся, пока нужны для работы с заказом. Вы можете"
            " попросить нас удалить ваши данные — позвоните или напишите на почту,"
            " указанную в контактах.</p>"
        ),
    },
)

HOW_TO_STEPS: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "icon": "search",
        "title_uk": "Оберіть роботу",
        "title_ru": "Выберите работу",
        "text_uk": "Знайдіть у галереї те, що подобається, і запамʼятайте номер.",
        "text_ru": "Найдите в галерее то, что нравится, и запомните номер.",
    },
    {
        "order": 2,
        "icon": "phone",
        "title_uk": "Зателефонуйте",
        "title_ru": "Позвоните",
        "text_uk": "Назвіть номер роботи, дату і бюджет. Підкажемо, що можливо.",
        "text_ru": "Назовите номер работы, дату и бюджет. Подскажем, что возможно.",
    },
    {
        "order": 3,
        "icon": "gift",
        "title_uk": "Заберіть або отримайте",
        "title_ru": "Заберите или получите",
        "text_uk": "Зберемо до потрібної години. Доставимо або віддамо в майстерні.",
        "text_ru": "Соберём к нужному часу. Доставим или отдадим в мастерской.",
    },
)


def seed_static_pages() -> None:
    from apps.core.models import StaticPage

    for page in STATIC_PAGES:
        StaticPage.objects.update_or_create(slug=page["slug"], defaults=page)


def seed_how_to_steps() -> None:
    from apps.core.models import HowToStep

    for step in HOW_TO_STEPS:
        HowToStep.objects.update_or_create(order=step["order"], defaults=step)


OCCASIONS: tuple[dict[str, Any], ...] = (
    {"slug": "podarunok", "name_uk": "Подарунок", "name_ru": "Подарок", "order": 1},
    {"slug": "vesillya", "name_uk": "Весілля", "name_ru": "Свадьба", "order": 2},
    {"slug": "yuvilei", "name_uk": "Ювілей", "name_ru": "Юбилей", "order": 3},
    {
        "slug": "den-narodzhennya",
        "name_uk": "День народження",
        "name_ru": "День рождения",
        "order": 4,
    },
    {"slug": "korporatyv", "name_uk": "Корпоратив", "name_ru": "Корпоратив", "order": 5},
    {"slug": "traurni", "name_uk": "Траурні", "name_ru": "Траурные", "order": 6},
    {
        "slug": "oformlennya-zaly",
        "name_uk": "Оформлення залу",
        "name_ru": "Оформление зала",
        "order": 7,
    },
)

TAG_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "slug": "type",
        "name_uk": "Тип виробу",
        "name_ru": "Тип изделия",
        "filter_kind": "checkbox",
        "order": 1,
        "tags": (
            ("buket", "Букет", "Букет", ""),
            ("kompozytsiya", "Композиція", "Композиция", ""),
            ("koshyk", "Кошик", "Корзина", ""),
            ("korobka", "Коробка", "Коробка", ""),
            ("vinok", "Вінок", "Венок", ""),
        ),
    },
    {
        "slug": "color",
        "name_uk": "Колір",
        "name_ru": "Цвет",
        "filter_kind": "color_swatch",
        "order": 2,
        "tags": (
            ("bilyi", "Білий", "Белый", "#FFFFFF"),
            ("rozhevyi", "Рожевий", "Розовый", "#F2C9C9"),
            ("chervonyi", "Червоний", "Красный", "#C0392B"),
            ("zhovtyi", "Жовтий", "Жёлтый", "#F1C40F"),
            ("fioletovyi", "Фіолетовий", "Фиолетовый", "#8E6BB0"),
            ("zelenyi", "Зелений", "Зелёный", "#5E7355"),
        ),
    },
    {
        "slug": "flower",
        "name_uk": "Квіти",
        "name_ru": "Цветы",
        "filter_kind": "checkbox",
        "order": 3,
        "tags": (
            ("troyandy", "Троянди", "Розы", ""),
            ("pivonii", "Півонії", "Пионы", ""),
            ("tyulpany", "Тюльпани", "Тюльпаны", ""),
            ("hortenziyi", "Гортензії", "Гортензии", ""),
            ("eustoma", "Еустома", "Эустома", ""),
        ),
    },
    {
        "slug": "season",
        "name_uk": "Сезон",
        "name_ru": "Сезон",
        "filter_kind": "checkbox",
        "order": 4,
        "tags": (
            ("vesna", "Весна", "Весна", ""),
            ("lito", "Літо", "Лето", ""),
            ("osin", "Осінь", "Осень", ""),
            ("zyma", "Зима", "Зима", ""),
        ),
    },
)

# Five works, filled the way the owner is meant to fill one: several angles, a
# description, the composition, the size and a price. The photographs sit in
# `seed_assets/works`; their provenance is in CREDITS.md beside them.
WORKS: tuple[dict[str, Any], ...] = (
    {
        "photos": "vesilnyi",
        "photo_count": 3,
        "title_uk": "Весільний букет нареченої",
        "title_ru": "Свадебный букет невесты",
        "description_uk": (
            "Ніжний букет у пудрових тонах: півонії, троянди і еустома з дрібною"
            " зеленню. Збираємо вранці у день весілля, щоб квіти простояли всю"
            " церемонію і вечір."
        ),
        "description_ru": (
            "Нежный букет в пудровых тонах: пионы, розы и эустома с мелкой"
            " зеленью. Собираем утром в день свадьбы, чтобы цветы простояли всю"
            " церемонию и вечер."
        ),
        "composition_uk": "півонії, троянди, еустома, евкаліпт",
        "composition_ru": "пионы, розы, эустома, эвкалипт",
        "size_text_uk": "діаметр 28 см",
        "size_text_ru": "диаметр 28 см",
        "price_from": 1450,
        "occasions": ("vesillya",),
        "tags": ("buket", "rozhevyi", "pivonii", "lito"),
    },
    {
        "photos": "pivonii",
        "photo_count": 2,
        "title_uk": "Букет півоній",
        "title_ru": "Букет пионов",
        "description_uk": (
            "Півонії у сезон, з кінця травня до середини червня. Беремо квіти в"
            " напівроспуску, щоб букет розкрився вже вдома і простояв довше."
        ),
        "description_ru": (
            "Пионы в сезон, с конца мая до середины июня. Берём цветы в"
            " полураспуске, чтобы букет раскрылся уже дома и простоял дольше."
        ),
        "composition_uk": "півонії, фісташка",
        "composition_ru": "пионы, фисташка",
        "size_text_uk": "висота 45 см",
        "size_text_ru": "высота 45 см",
        "price_from": 1200,
        "occasions": ("podarunok", "den-narodzhennya"),
        "tags": ("buket", "rozhevyi", "pivonii", "vesna"),
    },
    {
        "photos": "tyulpany",
        "photo_count": 2,
        "title_uk": "Букет тюльпанів",
        "title_ru": "Букет тюльпанов",
        "description_uk": (
            "Класика березня. Збираємо круглим куполом, від двадцяти п'яти штук;"
            " колір підбираємо під ваш привід, від білого до насиченого рожевого."
        ),
        "description_ru": (
            "Классика марта. Собираем круглым куполом, от двадцати пяти штук;"
            " цвет подбираем под ваш повод, от белого до насыщенного розового."
        ),
        "composition_uk": "тюльпани",
        "composition_ru": "тюльпаны",
        "size_text_uk": "51 тюльпан",
        "size_text_ru": "51 тюльпан",
        "price_from": 950,
        "occasions": ("podarunok", "den-narodzhennya"),
        "tags": ("buket", "bilyi", "tyulpany", "vesna"),
    },
    {
        "photos": "kompozytsiya",
        "photo_count": 2,
        "title_uk": "Авторська композиція",
        "title_ru": "Авторская композиция",
        "description_uk": (
            "Щільна композиція у глибоких відтінках: жоржини, троянди і фактурна"
            " зелень. Тримає форму без води кілька годин, тому годиться і для"
            " вручення на сцені, і для столу."
        ),
        "description_ru": (
            "Плотная композиция в глубоких оттенках: георгины, розы и фактурная"
            " зелень. Держит форму без воды несколько часов, поэтому годится и для"
            " вручения на сцене, и для стола."
        ),
        "composition_uk": "жоржини, троянди, протея, евкаліпт",
        "composition_ru": "георгины, розы, протея, эвкалипт",
        "size_text_uk": "висота 40 см",
        "size_text_ru": "высота 40 см",
        "price_from": 1350,
        "occasions": ("korporatyv", "yuvilei"),
        "tags": ("kompozytsiya", "chervonyi", "troyandy", "osin"),
    },
    {
        "photos": "sklyana",
        "photo_count": 2,
        "title_uk": "Квіти у скляній вазі",
        "title_ru": "Цветы в стеклянной вазе",
        "description_uk": (
            "Гортензія і садові квіти у прозорій вазі: букет, який не треба"
            " перекладати вдома. Ваза входить у вартість."
        ),
        "description_ru": (
            "Гортензия и садовые цветы в прозрачной вазе: букет, который не надо"
            " перекладывать дома. Ваза входит в стоимость."
        ),
        "composition_uk": "гортензія, польові квіти, зелень",
        "composition_ru": "гортензия, полевые цветы, зелень",
        "size_text_uk": "висота 35 см",
        "size_text_ru": "высота 35 см",
        "price_from": 890,
        "occasions": ("podarunok", "den-narodzhennya"),
        "tags": ("kompozytsiya", "rozhevyi", "hortenziyi", "lito"),
    },
)


def seed_occasions() -> None:
    from apps.catalog.models import Occasion

    for occasion in OCCASIONS:
        saved, _created = Occasion.objects.update_or_create(
            slug=occasion["slug"], defaults=occasion
        )
        attach_photo(saved, "cover", ASSETS / "occasions" / f"{saved.slug}.webp")


def seed_tags() -> None:
    from apps.catalog.models import Tag, TagGroup

    for group_data in TAG_GROUPS:
        tags = group_data["tags"]
        group, _created = TagGroup.objects.update_or_create(
            slug=group_data["slug"],
            defaults={key: value for key, value in group_data.items() if key != "tags"},
        )
        for order, (slug, name_uk, name_ru, color_hex) in enumerate(tags, start=1):
            Tag.objects.update_or_create(
                slug=slug,
                defaults={
                    "group": group,
                    "name_uk": name_uk,
                    "name_ru": name_ru,
                    "color_hex": color_hex,
                    "order": order,
                },
            )


def seed_works() -> None:
    from django.core.files.base import ContentFile

    from apps.catalog.models import Occasion, Tag, Work, WorkImage

    occasions = {item.slug: item for item in Occasion.objects.all()}
    tags = {item.slug: item for item in Tag.objects.all()}

    for entry in WORKS:
        # The Ukrainian title is the natural key here: the article comes from a
        # sequence and would differ on every run.
        work = Work.objects.filter(title_uk=entry["title_uk"]).first() or Work(
            title_uk=entry["title_uk"]
        )
        for field in (
            "title_ru",
            "description_uk",
            "description_ru",
            "composition_uk",
            "composition_ru",
            "size_text_uk",
            "size_text_ru",
            "price_from",
        ):
            setattr(work, field, entry[field])
        work.status = Work.Status.PUBLISHED
        work.save()

        work.occasions.set([occasions[slug] for slug in entry["occasions"] if slug in occasions])
        work.tags.set([tags[slug] for slug in entry["tags"] if slug in tags])

        if work.images.exists():
            continue
        for number in range(1, entry["photo_count"] + 1):
            path = ASSETS / "works" / f"{entry['photos']}-{number}.webp"
            if not path.exists():
                continue
            WorkImage.objects.create(
                work=work,
                alt_uk=entry["title_uk"],
                alt_ru=entry["title_ru"],
                order=number - 1,
                image=ContentFile(path.read_bytes(), name=path.name),
            )


REVIEWS: tuple[dict[str, Any], ...] = (
    {
        "author_name": "Олена",
        "rating": 5,
        "is_featured": True,
        "text_uk": "Букет був свіжий, зібрали за годину. Наречена в захваті, дякую!",
        "text_ru": "Букет был свежий, собрали за час. Невеста в восторге, спасибо!",
    },
    {
        "author_name": "Ігор",
        "rating": 5,
        "is_featured": True,
        "text_uk": "Замовляв по телефону, назвав номер роботи. Привезли рівно те, що на фото.",
        "text_ru": "Заказывал по телефону, назвал номер работы. Привезли ровно то, что на фото.",
    },
    {
        "author_name": "Марія",
        "rating": 5,
        "is_featured": True,
        "text_uk": "Оформлювали зал на весілля. Приїхали раніше і все встигли.",
        "text_ru": "Оформляли зал на свадьбу. Приехали раньше и всё успели.",
    },
    {
        "author_name": "Андрій",
        "rating": 4,
        "text_uk": "Гарний букет на день народження. Хотілося більше зелені, але це моя вина.",
        "text_ru": "Красивый букет на день рождения. Хотелось больше зелени, но это моя вина.",
    },
    {
        "author_name": "Наталя",
        "rating": 5,
        "text_uk": "Півонії стояли тиждень. Тепер замовляю тільки тут.",
        "text_ru": "Пионы стояли неделю. Теперь заказываю только здесь.",
    },
)


def seed_reviews() -> None:
    from apps.reviews.models import Review

    for review in REVIEWS:
        Review.objects.update_or_create(
            author_name=review["author_name"],
            defaults={
                **review,
                "source": Review.Source.ADMIN,
                "status": Review.Status.PUBLISHED,
                "consent": True,
            },
        )


POSTS: tuple[dict[str, Any], ...] = (
    {
        "slug": "yak-obraty-buket",
        "title_uk": "Як обрати букет",
        "title_ru": "Как выбрать букет",
        "excerpt_uk": "Коротка інструкція для тих, хто обирає квіти вперше.",
        "excerpt_ru": "Короткая инструкция для тех, кто выбирает цветы впервые.",
        "body_uk": (
            "<p>Почніть із приводу. Букет на день народження, весільний і траурний"
            " збираються по-різному, і це найшвидший спосіб звузити вибір.</p>"
            "<h2>Далі — колір</h2>"
            "<p>Один-два кольори виглядають дорожче за п'ять. Якщо сумніваєтесь,"
            " беріть відтінки однієї гами.</p>"
            "<h2>І тільки потім квіти</h2>"
            "<p>Троянди стоять довше, півонії красивіші, польові — тепліші. Скажіть,"
            " що важливіше, і ми підберемо.</p>"
        ),
        "body_ru": (
            "<p>Начните с повода. Букет на день рождения, свадебный и траурный"
            " собираются по-разному, и это самый быстрый способ сузить выбор.</p>"
            "<h2>Дальше — цвет</h2>"
            "<p>Один-два цвета выглядят дороже пяти. Если сомневаетесь, берите"
            " оттенки одной гаммы.</p>"
            "<h2>И только потом цветы</h2>"
            "<p>Розы стоят дольше, пионы красивее, полевые — теплее. Скажите, что"
            " важнее, и мы подберём.</p>"
        ),
    },
    {
        "slug": "skilky-stoyat-kvity",
        "title_uk": "Скільки стоять квіти",
        "title_ru": "Сколько стоят цветы",
        "excerpt_uk": "Що робити, щоб букет прожив довше трьох днів.",
        "excerpt_ru": "Что делать, чтобы букет прожил дольше трёх дней.",
        "body_uk": (
            "<p>Підріжте стебла під кутом і поставте у чисту вазу з холодною водою."
            " Міняйте воду щодня.</p>"
            "<h2>Чого не робити</h2>"
            "<p>Не ставте букет на сонце, біля батареї і поруч із фруктами: вони"
            " виділяють газ, від якого квіти в'януть швидше.</p>"
        ),
        "body_ru": (
            "<p>Подрежьте стебли под углом и поставьте в чистую вазу с холодной водой."
            " Меняйте воду каждый день.</p>"
            "<h2>Чего не делать</h2>"
            "<p>Не ставьте букет на солнце, у батареи и рядом с фруктами: они"
            " выделяют газ, от которого цветы вянут быстрее.</p>"
        ),
    },
    {
        "slug": "kvity-po-sezonah",
        "title_uk": "Квіти по сезонах",
        "title_ru": "Цветы по сезонам",
        "excerpt_uk": "Що цвіте навесні, влітку, восени і взимку.",
        "excerpt_ru": "Что цветёт весной, летом, осенью и зимой.",
        "body_uk": (
            "<p>Навесні — тюльпани, нарциси, півонії наприкінці травня. Влітку —"
            " гортензії, еустома, садові троянди.</p>"
            "<h2>Осінь і зима</h2>"
            "<p>Восени добре виглядають жоржини і хризантеми, взимку — все, що"
            " витримує мороз дорогою до дверей.</p>"
        ),
        "body_ru": (
            "<p>Весной — тюльпаны, нарциссы, пионы в конце мая. Летом — гортензии,"
            " эустома, садовые розы.</p>"
            "<h2>Осень и зима</h2>"
            "<p>Осенью хорошо выглядят георгины и хризантемы, зимой — всё, что"
            " выдерживает мороз по дороге до двери.</p>"
        ),
    },
)


def seed_posts() -> None:
    from apps.blog.models import Post
    from apps.catalog.models import Work

    works = list(Work.published.all()[:3])
    for post in POSTS:
        saved, _created = Post.objects.update_or_create(
            slug=post["slug"], defaults={**post, "status": Post.Status.PUBLISHED}
        )
        attach_photo(saved, "cover", ASSETS / "blog" / f"{saved.slug}.webp")
        if works and not saved.related_works.exists():
            saved.related_works.set(works)


def run() -> dict[str, int]:
    """Fill the database. Running it twice changes nothing."""
    from apps.blog.models import Post
    from apps.catalog.models import Occasion, Tag, TagGroup, Work, WorkImage
    from apps.core.models import HowToStep, SiteSettings, StaticPage
    from apps.reviews.models import Review

    seed_site_settings()
    seed_static_pages()
    seed_how_to_steps()
    seed_occasions()
    seed_tags()
    seed_works()
    seed_reviews()
    seed_posts()
    return {
        "reviews": Review.objects.count(),
        "posts": Post.objects.count(),
        "site_settings": SiteSettings.objects.count(),
        "static_pages": StaticPage.objects.count(),
        "how_to_steps": HowToStep.objects.count(),
        "occasions": Occasion.objects.count(),
        "tag_groups": TagGroup.objects.count(),
        "tags": Tag.objects.count(),
        "works": Work.objects.count(),
        "work_images": WorkImage.objects.count(),
    }


def main() -> None:
    import django

    django.setup()
    for name, count in run().items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
