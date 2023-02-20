# Create your models here.

from django.db import models


class RoadTest(models.TextChoices):
    Acceleration = "acceleration", _("Acceleration ")
    TransmissionShiftQuality = "transmission_shift", _("Quality of transmission shifts")
    Steering = "steering", _("Steering")
    SuspensionPerformance = "suspension_performance", _("Performance of vehicle suspension")
    Starting = "starting", _("Starting")
    Idling = "idling", _("Idling")
    EnginePerformance = "engine_performance", _("Engine performance")


class ElectricalSystems(models.TextChoices):
    PowerMirrors = "power_mirror", _("Power mirrors")
    AudioSystem = "audio_system", _("Audio systems")
    OnBoardComputer = "onboard_computer", _("Onboard Computer")
    HeadLights = "headlights", _("Head lights")
    TailLight = "tail_light", _("Tail lights")
    SignalLights = "signal_lights", _("Signal lights")
    BrakeLight = "brake_lights", _("Brake lights")
    ParkingLight = "parking_light", _("Parking lights")
    PowerSteering = "power_steering", _("Power steering")
    PowerLocks = "power_locks", _("Power locks")
    PowerSeats = "power_seats", _("Power seats")
    PowerWindows = "power_windows", _("Power windows")


class Interior(models.TextChoices):
    Seats = "seats", _("Seats")
    HeadLiner = "headliner", _("Head linder")
    Carpet = "carpet", _("Carpets")
    DoorPanels = "door_panels", _("Door panels")
    GloveBox = "glove_box", _("Glove box")
    VanityMirror = "vanity_mirror", _("Vanity mirror")
    InteriorTrim = "interior_trim", _("Interior trim")
    Dashboard = "dashboard", _("Dashboard")
    DashboardGauges = "dashboard_gauges", _("Dashboard Gauges")
    AirConditioning = "air_conditioning", _("Air conditioning")
    Heater = "heater", _("Heater")
    Defroster = "defroster", _("Defroster")


class UnderHood(models.TextChoices):
    EngineCompartment = "engine_compartment", _("Engine Compartment")
    Battery = "battery", _("Battery")
    Oil = "oil", _("Oil")
    Fluids = "fluids", _("Fluids")
    Belt = "belt", _("Belts")
    Hoses = "hoses", _("Hoses")
    AnyNonStockModifications = "any_non_stock_modifications", _("Any non-stock modifications")
    DriveAxle = "drive_axle", _("Drive Axle")
    Suspension = "suspension", _("Suspension")
    BrakeSystem = "brake_system", _("brake system")


class UnderBody(models.TextChoices):
    Frame = "frame", _("Frame")
    ExhaustSystem = "exhaust_system", _("Exhaust System")
    Transmission = "transmission", _("transmission")
    DriveAxle = "drive_axle", _("Drive Axle")
    Suspension = "suspension", _("Suspension")
    BrakeSystem = "brake_system", _("brake system")


class Glass(models.TextChoices):
    Windshield = "windshield", _("Windshield")
    Windows = "windows", _("Windows")
    Mirrors = "mirrors", _("Mirrors")
    RearWindows = "rear_windows", _("Rear windows")


class TyresAndWheels(models.TextChoices):
    TyreCondition = "tyres_condition", _("Condition of Tyres")
    WheelsCondition = "wheels_condition", _("Condition of wheels")
    SpareTyre = "spare_tyre", _("Spare tyre")


class Exterior(models.TextChoices):
    Hood = "hood", _("Hood")
    Front = "front", _("Front")
    FrontBumper = "front_bumper", _("Front bumper")
    Fenders = "fenders", _("Fenders")
    Doors = "doors", _("Doors")
    Roof = "roof", _("Roof")
    Rear = "rear", _("Rear")
    RearNumber = "rear_bumper", _("Rear bumper")
    Trunk = "trunk", _("Trunk")
    Trim = "trim", _("trim")
    FuelDoor = "fuel_door", _("Fuel door")
    PaintCondition = "paint_condition", _("Condition of paint")
