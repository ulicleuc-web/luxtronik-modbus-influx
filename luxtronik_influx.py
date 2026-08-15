#!/usr/bin/env python3
"""Read Alpha Innotec/Luxtronik SHI Modbus-TCP values and publish them.

The script reads electrical energy, generated heat energy and current power
values from the Luxtronik Smart Home Interface, writes them to InfluxDB 1.x
and publishes selected values via MQTT for use in Home Assistant.
"""

from datetime import datetime

import paho.mqtt.publish as publish
from influxdb import InfluxDBClient
from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from config import (
    HEATPUMP_IP,
    HEATPUMP_PORT,
    MODBUS_UNIT_ID,
    INFLUX_DATABASE,
    INFLUX_HOST,
    INFLUX_PASSWORD,
    INFLUX_PORT,
    INFLUX_USER,
    MQTT_HOST,
)


# Luxtronik SHI input registers
REG_CURRENT_HEAT = 10300          # INT16,  kW / 10
REG_CURRENT_POWER = 10301         # UINT16, kW / 10
REG_MIN_POWER = 10302             # UINT16, kW / 10

REG_POWER_TOTAL = 10310           # UINT32, kWh / 10
REG_POWER_HEATING = 10312         # UINT32, kWh / 10
REG_POWER_HOTWATER = 10314        # UINT32, kWh / 10

REG_HEAT_TOTAL = 10320            # UINT32, kWh / 10
REG_HEAT_HEATING = 10322          # UINT32, kWh / 10
REG_HEAT_HOTWATER = 10324         # UINT32, kWh / 10


def _check_response(response, addr):
    """Raise an exception for an unsuccessful Modbus response."""
    if response.isError():
        raise RuntimeError(f"Modbus error while reading register {addr}: {response}")


def read_uint16_x10(client, addr, unitid=MODBUS_UNIT_ID):
    """Read one UINT16 input register and apply the /10 scale factor."""
    response = client.read_input_registers(addr, 1, slave=unitid)
    _check_response(response, addr)
    return response.registers[0] / 10.0


def read_int16_x10(client, addr, unitid=MODBUS_UNIT_ID):
    """Read one signed INT16 input register and apply the /10 scale factor."""
    response = client.read_input_registers(addr, 1, slave=unitid)
    _check_response(response, addr)

    value = response.registers[0]
    if value >= 0x8000:
        value -= 0x10000

    return value / 10.0


def read_uint32_kwh10(client, addr, unitid=MODBUS_UNIT_ID):
    """Read two UINT16 input registers as UINT32 and return kWh."""
    response = client.read_input_registers(addr, 2, slave=unitid)
    _check_response(response, addr)

    decoder = BinaryPayloadDecoder.fromRegisters(
        response.registers,
        byteorder=Endian.Big,
        wordorder=Endian.Big,
    )
    return decoder.decode_32bit_uint() / 10.0


def read_heatpump(client):
    """Read all values used by this project from the heat pump."""
    return {
        "current_heat": read_int16_x10(client, REG_CURRENT_HEAT, MODBUS_UNIT_ID),
        "current_power": read_uint16_x10(client, REG_CURRENT_POWER, MODBUS_UNIT_ID),
        "min_power": read_uint16_x10(client, REG_MIN_POWER, MODBUS_UNIT_ID),
        "power_total_kwh": read_uint32_kwh10(client, REG_POWER_TOTAL, MODBUS_UNIT_ID),
        "power_heating_kwh": read_uint32_kwh10(client, REG_POWER_HEATING, MODBUS_UNIT_ID),
        "power_hotwater_kwh": read_uint32_kwh10(client, REG_POWER_HOTWATER, MODBUS_UNIT_ID),
        "heat_energy_total_kwh": read_uint32_kwh10(client, REG_HEAT_TOTAL, MODBUS_UNIT_ID),
        "heat_energy_heating_kwh": read_uint32_kwh10(client, REG_HEAT_HEATING, MODBUS_UNIT_ID),
        "heat_energy_hotwater_kwh": read_uint32_kwh10(client, REG_HEAT_HOTWATER, MODBUS_UNIT_ID),
    }


def print_values(values):
    """Print the current readings for manual runs and cron logs."""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    print(
        f"{timestamp} current:     "
        f"heat={values['current_heat']} "
        f"power={values['current_power']} "
        f"min_power={values['min_power']}"
    )
    print(
        f"{timestamp} e_power:     "
        f"total={values['power_total_kwh']} "
        f"heating={values['power_heating_kwh']} "
        f"hotwater={values['power_hotwater_kwh']}"
    )
    print(
        f"{timestamp} heat_energy: "
        f"total={values['heat_energy_total_kwh']} "
        f"heating={values['heat_energy_heating_kwh']} "
        f"hotwater={values['heat_energy_hotwater_kwh']}"
    )


def write_influx(values):
    """Write one point to an existing InfluxDB 1.x database."""
    points = [
        {
            "measurement": "heatpump_energy",
            "tags": {
                "host": "raspberrypi",
            },
            "fields": {
                "power_total_kwh": float(values["power_total_kwh"]),
                "power_heating_kwh": float(values["power_heating_kwh"]),
                "power_hotwater_kwh": float(values["power_hotwater_kwh"]),
                "heat_energy_total_kwh": float(values["heat_energy_total_kwh"]),
                "heat_energy_heating_kwh": float(values["heat_energy_heating_kwh"]),
                "heat_energy_hotwater_kwh": float(values["heat_energy_hotwater_kwh"]),
                "current_heat": float(values["current_heat"]),
                "current_power": float(values["current_power"]),
                "min_power": float(values["min_power"]),
            },
        }
    ]

    client = InfluxDBClient(
        host=INFLUX_HOST,
        port=INFLUX_PORT,
        username=INFLUX_USER,
        password=INFLUX_PASSWORD,
        database=INFLUX_DATABASE,
    )

    try:
        if not client.write_points(points):
            raise RuntimeError("InfluxDB did not accept the data point")
    finally:
        client.close()


def publish_mqtt(values):
    """Publish selected readings to MQTT for Home Assistant or other clients."""
    messages = [
        {
        "topic": "heatpump/power_total_kwh",
        "payload": str(values["power_total_kwh"]),
        "retain":True,
        },
        {
        "topic": "heatpump/power_heating_kwh",
        "payload": str(values["power_heating_kwh"]),
        "retain":True,
        },
        {
        "topic": "heatpump/power_hotwater_kwh",
        "payload": str(values["power_hotwater_kwh"]),
        "retain":True,
        },
        {
        "topic": "heatpump/heat_energy_total_kwh",
        "payload": str(values["heat_energy_total_kwh"]),
        "retain":True,
        },
        {
        "topic": "heatpump/heat_energy_heating_kwh",
        "payload": str(values["heat_energy_heating_kwh"]),
        "retain":True,
        },
        {
        "topic": "heatpump/heat_energy_hotwater_kwh",
        "payload": str(values["heat_energy_hotwater_kwh"]),
        "retain":True,
        },
        {
        "topic": "heatpump/current_heat_kw",
        "payload": str(values["current_heat"]),
        "retain":True,
        },
        {
        "topic": "heatpump/current_power_kw",
        "payload": str(values["current_power"]),
        "retain":True,
        },
        {
        "topic": "heatpump/min_power_kw",
        "payload": str(values["current_power"]),
        "retain":True,
        },
    ]

    publish.multiple(messages, hostname=MQTT_HOST)


def main():
    client = ModbusTcpClient(HEATPUMP_IP, port=HEATPUMP_PORT)

    if not client.connect():
        raise ConnectionError(
            f"Could not connect to heat pump at {HEATPUMP_IP}:{HEATPUMP_PORT}"
        )

    try:
        values = read_heatpump(client)
    finally:
        client.close()

    print_values(values)
    write_influx(values)
    publish_mqtt(values)


if __name__ == "__main__":
    main()
