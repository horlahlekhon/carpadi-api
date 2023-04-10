import datetime
import random
from enum import Enum
from typing import Optional

import requests
from django.conf import settings
from pydantic import BaseModel, Field

from src.models.models import FuelTypes, CarTypes
from src.notifications.services import logger

dummy = {
    'battery_kw': '',
    'battery_type': '',
    'battery_type_desc': '',
    'battery_voltage_desc': '',
    'body_style': 'UT',
    'body_style_desc': 'SPORT UTILITY VEHICLE',
    'door_cnt': '4',
    'drive_type': 'AWD',
    'drive_type_desc': 'All Wheel Drive',
    'engine_has_supercharger': 'No',
    'engine_has_turbocharger': 'No',
    'engine_has_variable_valve_timing': 'Yes',
    'engine_block_type': 'V-type',
    'engine_carbureted_barrel_cnt': 'NA',
    'engine_carbureted_type': 'Fuel Injection',
    'engine_cylinder_cnt': '6',
    'engine_displacement_cubic_cm': '',
    'engine_displacement_cubic_inches': '213',
    'engine_displacement_cubic_liters': '3.5',
    'engine_fuel_injection': 'Multiport',
    'engine_model': '',
    'engine_manufacturer': '',
    'tire_front_desc': '',
    'tire_front_pressure_lbs': '',
    'tire_front_size': '17R245',
    'make': 'HONDA',
    'model': 'PILOT',
    'year': str(random.randint(1900, 2023)),
    'mfg_base_msrp': '40670',
    'manufacturer': 'Honda',
    'origin_desc': 'Import Built in North America',
    'plant_city_name': 'LINCOLN',
    'plant_country_name': 'United States',
    'plant_location_name': 'ALABAMA',
    'tire_rear_desc': '',
    'tire_rear_recommended_pressure': '',
    'tire_rear_size': '17R245',
    'weight_base': '4608',
    'trim': 'TOURING',
    'trk_bed_length_code': 'R',
    'trk_bed_length_desc': 'Regular',
    'trk_brk_code': 'HYD',
    'trk_brk_desc': 'HYDRAULIC',
    'trk_cab_code': 'SUV',
    'trk_cab_desc': 'Sport Utility',
    'wheel_end_cnt': '4',
    'wheel_powertrain_cnt': '4',
    'fuel_cpcty_gallons': '21',
    'vehicle_type': 'Truck',
    'fuel_type': 'Gas',
    'transmission': 'AUTOMATIC',
}


class DriveTypes(str, Enum):
    FrontWheelDrive = "FWD"
    AllWheelDrive = "AWD"
    FourWheelDrive = "4WD"
    RearWheelDrive = "RWD"
    Unknown = "unknown"


class EvilDichotomies(str, Enum):
    Yes = ("Yes",)
    No = "No"
    Unknown = "Unknown"


class ResponseMetadata(BaseModel):
    message: str
    credentials: str
    counter: int


class VinDecodeResponse(BaseModel):
    battery_kw: str = Field(
        default='',
        description="The measure of total battery power expressed in kilowatts. For example: " "71KW, 85KW, 75KW, 67KW.",
    )
    battery_type: str = Field(
        default='',
        description="A value that identifies the kind of battery in the vehicle. For example: "
        "PbA - Lead Acid,NMH - Nickel Metal Hydride",
    )
    battery_type_desc: str = Field(
        default='',
        description="The description of the code for the Battery Type Code. For "
        "example:PbA - Lead Acid,NMH - Nickel Metal Hydride.",
    )
    battery_voltage_desc: str = Field(default='', description="The voltage rating of the battery as provided by the manufactuer.")
    body_style: str = Field(default='', description="A code that describes the body style of the vehicle. For example, CP=Coupe")
    body_style_desc: str = Field(default='', description="The description of the code Body Style Code For example: Coupe ")
    door_cnt: int = Field(default=0, description="The number of doors the vehicle has.")
    drive_type: DriveTypes = Field(
        default=DriveTypes.Unknown,
        description="This element describes type of driving configuration for cars and " "trucks such as FWD, AWD, RWD.",
    )
    engine_has_supercharger: EvilDichotomies = Field(
        default='', description="Indicates if the engine has a supercharger or not. " "Yes, No or Unknown."
    )
    engine_has_turbocharger: EvilDichotomies = Field(
        description="Indicates whether a vehicle has Variable Valve Timing.  Yes, No or Unknown."
    )
    engine_block_type: str = Field(default='', description="Engine block type")
    engine_carbureted_barrel_cnt: str = Field(default=0, description="the numbers of barrels in a carburated engine")
    engine_carbureted_type: str = Field(
        default='',
        description="The description of the code which identifies the vehicle "
        "carburetion type. For example Carburator, Fuel Injection, "
        "Unknown or Electric n/a.",
    )
    engine_cylinder_cnt: str = Field(
        default='',
        description="Contains a code that represents the number of cylinders a vehicle's " "combustion engine can have.",
    )
    engine_displacement_cubic_cm = Field(
        default='',
        description="(Displacement CC) displacement in cubic centimeters. We intend "
        "to use this as the definitive, exact diplacement value, "
        "i.e. 4967 cc.",
    )
    engine_displacement_cubic_inches = Field(
        default='',
        description="(Displacement CID) displacement in cubic inches. This is a "
        "rounded, marketing value, like 302 cubic inches, "
        "instead of 4967 cc.",
    )
    engine_displacement_cubic_liters = Field(
        default='',
        description="(Displacement Liters) displacement in rounded Liters, "
        "where 1,000 cubic centimeters = 1 liter. Even domestic "
        "makes will advertise displacement in terms of liters (e.g. "
        "5.0 liter mustang, which equates to a 302 CID or 4967 cc "
        "displacement).",
    )
    engine_fuel_injection = Field(
        default='', description="The type of fuel injection used by a vehicle. For example, Direct, " "Throttlebody"
    )
    engine_model: str = Field(default='', description="engine model")
    engine_manufacturer: str = Field(default='', description="engine manufacturer")
    fuel_cpcty_gallons: str = Field(
        default='',
        description="The total fuel capacity (in gallons) for the vehicle with standard "
        "equipment as reported by the OEM. The Fuel Capacity measurement does "
        "not include optional second fuel tanks for trucks",
    )
    fuel_type: str = Field(default='', description="(Fuel) What an internal combustion burns to move a piston in a cylinder")
    tire_front_desc: str = Field(default='', description="more specific tire description (ex. Michelin Eagle P245/40ZR)")
    tire_front_pressure_lbs: str = Field(
        default='', description="(Front Tire Pressure) Vehicle Mfr reccomendation for tire " "pressure, in pounds/sq. in."
    )
    tire_front_size: str = Field(default='', description="(Front Tire Size Description) As in '17R245'")
    make: str = Field(default='', description="(Make - Name) Full name of the make (i.e. Chevrolet)")
    model: str = Field(default='', description="vehicle model")
    year: int = Field(
        default=datetime.datetime.now().year,
        description="The marketing year defined by the OEM which the vehicle was produced. The value "
        "contained in this attribute may not always match the calendar year in which the "
        "vehicle was actually manufactured. Many OEMs release models prior to calendar "
        "year.",
    )
    mfg_base_msrp: str = Field(
        default='',
        description="Contains the base price of the vehicle as designated by the OEM's "
        "specifications. BASE PRICE includes only the price for the base model of "
        "the vehicle, excluding any optional equipment that may have been added as "
        "a result of the vehicle's TRIM LEVEL.",
    )
    manufacturer: str = Field(
        default='',
        description="(Vehicle Manufacturer Name) The name of the vehicle manufacturer, "
        "i.e. General Motors, as defined by the National Crime Information Center.",
    )
    tire_rear_desc: str = Field(default='', description="more specific tire description (ex. Michelin Eagle P245/40ZR)")
    tire_rear_recommended_pressure: str = Field(
        default='', description="(Rear Tire Pressure) Vehicle Mfr reccomendation for tire " "pressure, in pounds/sq. in."
    )
    tire_rear_size: str = Field(default='', description='(Rear Tire Size Description) As in "17R245"')
    weight_base: str = Field(
        default='',
        description="Contains the base weight of the vehicle, as defined in the OEM's "
        "specifications. The base weight of a vehicle is the empty weight of the "
        "base model of the vehicle (i.e., the stripped down version of the vehicle).",
    )
    trim: str = Field(default='', description="vehicle trim")
    trk_bed_length_code: str = Field(
        default='',
        description='(Bed Length) Code representing the manufacturers description of the '
        'relative size of the cargo area of a pickup truck or van. A "long" '
        'Ford Ranger bed (compact pickup) may well be shorter than a "short" '
        'bed on an F350. (large industrial pickup).',
    )
    trk_bed_length_desc: str = Field(description="length of the bed of a truck")
    trk_brk_code: str = Field(
        default='',
        description="(Brake Type) The type of brakes on the Vehicle (currently commercial truck "
        "only). Truck VIN determines this currently",
    )
    trk_brk_desc: str = Field(default='', description="Description of the brake type")
    trk_cab_code: str = Field(
        default='', description="(Cab Configuration) Cab Type describes the physical configuration of a " "truck's cabin."
    )
    trk_cab_desc: str = Field(default='', description="cabin description a the truck")
    vehicle_type: str = Field(
        default='',
        description="The description of the code for the vehicle type code. For example: "
        "passenger, truck, motorcycle, commercial trailer. ",
    )
    transmission: str = Field(default='', description="Provides transmission type of the vehicle")


class VehicleInfoData(BaseModel):
    engine: str
    transmission: str
    car_type: str
    fuel_type: str
    age: int
    trim: str
    manufacturer: str
    drive_type: str  # DriveTypes
    num_of_cylinders: int
    raw_data: dict
    model: str
    year: int

    class Config:
        arbitrary_types_allowed = True


def build_absolute_uri(path):
    return f'{settings.SITE_URL}{path}'


def check_vin(vin: str) -> Optional[VehicleInfoData]:
    if settings.APP_ENV != "prod":
        data = VinDecodeResponse(**dummy)
        return VehicleInfoData(
            engine=data.engine_model,
            transmission=data.transmission,
            car_type=data.body_style,
            fuel_type=data.fuel_type,
            age=datetime.datetime.now().year - data.year if data.year else 0,
            trim=data.trim,
            manufacturer=data.manufacturer,
            drive_type=data.drive_type.value,
            num_of_cylinders=data.engine_cylinder_cnt,
            raw_data=dummy,
            model=data.model,
            year=data.year,
        )
    headers = {"partner-token": settings.CARMD_PARTNER_TOKEN, "Authorization": settings.CARMD_APIKEY}

    response = requests.get(settings.CARMD_VIN_CHECK(vin), headers=headers)
    js = response.json()
    if response.status_code == 200:
        meta = ResponseMetadata(**js.get("message"))
        if meta.message == "ok":
            data = VinDecodeResponse(**js.get("data"))
            return VehicleInfoData(
                engine=data.engine_model,
                transmission=data.transmission,
                car_type=data.body_style,
                fuel_type=data.fuel_type,
                age=datetime.datetime.now().year - data.year if data.year else 0,
                trim=data.trim,
                manufacturer=data.manufacturer,
                drive_type=data.drive_type.value,
                num_of_cylinders=data.engine_cylinder_cnt,
                raw_data=js.get("data"),
                model=data.model,
                year=data.year,
            )
    logger.debug(f"Tried to check vehicle details for vin {vin}. but got an error response: {js}")
    return None
