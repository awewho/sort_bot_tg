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
    # Основные
    alum_kg = State()
    alum_price = State()
    pet_kg = State()
    pet_price = State()
    glass_kg = State()
    glass_price = State()
    paper_kg = State()
    paper_price = State()
    metal_kg = State()
    metal_price = State()
    oil_kg = State()
    oil_price = State()
    other_kg = State()
    other_price = State()
    # Микс
    alum_pl_mix_kg = State()
    alum_pl_mix_price = State()
    alum_pl_glass_mix_kg = State()
    alum_pl_glass_mix_price = State()
    alum_iron_cans_mix_kg = State()
    alum_iron_cans_mix_price = State()
    pet_mix_kg = State()
    pet_mix_price = State()
    other_mix_kg = State()
    other_mix_price = State()


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

