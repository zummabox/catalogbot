from aiogram import F, types, Router
from aiogram.filters import CommandStart, Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_add_preorder, orm_get_product_name
# from database.orm_query import (
#     orm_add_to_cart,
#     orm_add_user,
# )

from filters.chat_types import ChatTypeFilter
from handlers.menu_processing import get_menu_content
from kbds.inline import MenuCallBack, get_user_catalog_btns
from kbds.reply import get_number, get_keyboard

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))



@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")

    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):

    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()


CANCEL_KB = get_keyboard(
    "Отмена",
    sizes=(1,),
)


class SearchProduct(StatesGroup):
    name = State()
    detail_for_search = None


@user_private_router.message(F.text.lower() == "поиск")
async def starring_at_product(message: types.Message, state: FSMContext):
    await message.answer('Введите название кроссовков, которые вы хотите найти или нажмите Отмена',
                         reply_markup=CANCEL_KB)
    await state.set_state(SearchProduct.name)


# Хендлер отмены и сброса состояния должен быть всегда именно здесь,
# после того, как только встали в состояние номер 1 (элементарная очередность фильтров)
@user_private_router.message(StateFilter("*"), Command("отмена"))
@user_private_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return
    if SearchProduct.detail_for_search:
        SearchProduct.detail_for_search = None
    await state.clear()
    await message.answer("Действия отменены")


@user_private_router.message(SearchProduct.name, F.text)
async def search_name(message: types.Message, state: FSMContext, session: AsyncSession):

    # Получаем название кроссовок из ответа пользователя
    product_name = message.text

    # Запускаем функцию поиска кроссовок по названию
    products = await orm_get_product_name(session, product_name)

    # Если кроссовки найдены, отправляем сообщение об этом
    if products:
        for product in products:
            await message.answer_photo(
                product.image,
                caption=f"<strong>{product.name}\n</strong><strong>{product.description}</strong>\n"
                        f"Стоимость: {round(product.price, 2)}", )
        await message.answer("Вот список найденных товаров ⬆️")
    else:
        await message.answer(f"К сожалению, кроссовок с названием '{product_name}' нет в наличии.")

    await state.clear()


class AddPreorder(StatesGroup):
    name = State()
    size = State()
    number = State()
    image = State()
    user_id = State()

    preorder_for_change = None

    texts = {
        'AddPreorder:name': 'Введите полное название кроссовок заново:',
        'AddPreorder:description': 'Введите описание заново:',
        'AddPreorder:price': 'Введите стоимость заново:',
        'AddPreorder:image': 'Этот стейт последний, поэтому...',
    }


@user_private_router.message(StateFilter(None), F.text.lower() == "предзаказ")
async def add_preorder(message: types.Message, state: FSMContext):
    await message.answer(
        'Введите полное название кроссовок, если не знаете название введите "Не знаю",'
        ' мы найдем кроссовки по фотографии')

    await state.set_state(AddPreorder.name)


############################# Хендлеры команд Отмена и Назад #########################


# Хендлер отмены и сброса состояния должен быть всегда именно здесь,
# после того, как только встали в состояние номер 1 (элементарная очередность фильтров)
@user_private_router.message(StateFilter("*"), Command("отмена"))
@user_private_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddPreorder.preorder_for_change:
        AddPreorder.preorder_for_change = None
    await state.clear()
    await message.answer("Действия отменены")


#########################################################################################

@user_private_router.message(AddPreorder.name, F.text)
async def add_name(message: types.Message, state: FSMContext):
    if 4 >= len(message.text) >= 150:
        await message.answer(
            "Название товара не должно превышать 150 символов\nили быть менее 5-ти символов. \n Введите заново"
        )
        return

    await state.update_data(name=message.text)
    await message.answer("Введите размер")
    await state.set_state(AddPreorder.size)


# Хендлер для отлова некорректных вводов для состояния name
@user_private_router.message(AddPreorder.name)
async def add_name(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст названия кроссовок или 'Не знаю'")


############################################################


@user_private_router.message(AddPreorder.size, F.text)
async def add_size(message: types.Message, state: FSMContext):
    try:
        float(message.text)
    except ValueError:
        await message.answer("Введите корректное значение")
        return

    await state.update_data(size=message.text)
    await message.answer("Отправьте ваш номер телефона", reply_markup=get_number)
    await state.set_state(AddPreorder.number)


# Хендлер для отлова некорректных ввода для состояния size
@user_private_router.message(AddPreorder.size)
async def add_price2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите размер")


@user_private_router.message(AddPreorder.number, F.contact)
async def add_number(message: types.Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    await message.answer("Отправьте фото кроссовок")
    await state.set_state(AddPreorder.image)


# Хендлер для отлова некорректных ввода для состояния number
@user_private_router.message(AddPreorder.number)
async def add_price2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите номер начиная с +7")


############################################################


@user_private_router.message(AddPreorder.image, F.photo)
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):

    await state.update_data(image=message.photo[-1].file_id)
    await state.update_data(user=message.from_user.username)
    data = await state.get_data()

    await orm_add_preorder(session, data)
    await message.answer_photo(data['image'],
                               caption=f"Заявка на предзаказ оформлена!\nНазвание:{data['name']}\nРазмер:{data['size']}\n"
                                       f"Номер телефона:{data['number']}")
    await state.clear()

    AddPreorder.preorder_for_change = None


@user_private_router.message(AddPreorder.image)
async def add_image(message: types.Message):
    await message.answer("Отправьте фото кроссовок")