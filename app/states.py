from aiogram.fsm.state import State, StatesGroup


class Reg(StatesGroup):
    point = State()


class BagFull(StatesGroup):
    aluminum_count = State()
    pet_count = State()
    glass_count = State()
    other_count = State()
    confirmation = State()  # Добавлено новое состояние

class Help(StatesGroup):
    request = State()
class ShipmentStates(StatesGroup):
    point_id = State()
    # Основные материалы
    pet_kg = State()
    pet_price = State()
    paper_kg = State()
    paper_price = State()
    alum_kg = State()
    alum_price = State()
    glass_kg = State()
    glass_price = State()
    small_beer_box_kg = State()
    small_beer_box_price = State()
    large_beer_box_kg = State()
    large_beer_box_price = State()
    mixed_beer_box_kg = State()
    mixed_beer_box_price = State()
    # Другие материалы
    oil_kg = State()
    oil_price = State()
    colored_plastic_kg = State()
    colored_plastic_price = State()
    iron_kg = State()
    iron_price = State()
    plastic_bag_kg = State()
    plastic_bag_price = State()
    mix_kg = State()
    mix_price = State()
    other_kg = State()
    other_price = State()


class Reports(StatesGroup):
    report_type = State()
    waiting_region_id = State()



class CreatePoint(StatesGroup):
    point_id = State()
    point_name = State()
    point_owner_name = State()
    phone_number = State()
    address = State()
    confirmation = State()

class ManagePoints(StatesGroup):
    action = State()
    point_id = State()
    edit_field = State()
    new_value = State()

class ManageZones(StatesGroup):
    action = State()
    zone_id = State()
    region_id = State()



class DriverRoute(StatesGroup):
    start = State()

class Notifications(StatesGroup):
    weight = State()
    price = State()
    new_bag = State()

