from aiogram.fsm.state import State, StatesGroup

class Reg(StatesGroup):
    point = State()


class BindPoint(StatesGroup):
    address = State()
    confirm = State()

class BagFull(StatesGroup):
    bags_count = State()



class Reports(StatesGroup):
    report_type = State()

class Help(StatesGroup):
    request = State()


class DriverRoute(StatesGroup):
    start = State()

class Notifications(StatesGroup):
    weight = State()
    price = State()
    new_bag = State()

class ShipmentStates(StatesGroup):
    point_id = State()
    alum_kg = State()
    alum_price = State()
    pet_kg = State()
    pet_price = State()
    glass_kg = State()
    glass_price = State()
    mixed_kg = State()
    mixed_price = State()
