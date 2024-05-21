from aiogram.utils.formatting import Bold, as_list, as_marked_section


categories = ['Nike', 'Adidas', 'New Balance', 'Boss', 'Asics', 'Другие']

description_for_info_pages = {
    "main": "Добро пожаловать!",
    "about": "Реплики, зато какие!🔥\nМагазин КАЧЕСТВЕННЫХ реплик.",
    "payment": as_marked_section(
        Bold("Варианты оплаты:"),
        "Предоплата",
        "Наложенный платеж",
        marker="✅ ",
    ).as_html(),
    "shipping": as_list(
        as_marked_section(
            Bold("Варианты доставки:"),
            "Почта России",
            "CDEK",
            "Самовывоз",
            marker="✅ ",
        ),
    ).as_html(),
    'catalog': 'Категории:',
    'search': 'Поиск',
    'cart': 'В корзине ничего нет!',
    'preorder': 'Предзаказ'
}