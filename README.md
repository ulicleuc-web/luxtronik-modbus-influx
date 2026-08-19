# Luxtronik Modbus → InfluxDB & MQTT

Python-Skript zum Auslesen einer Alpha Innotec / Luxtronik Wärmepumpe
über Modbus TCP.

Die Messwerte werden in InfluxDB 1.x gespeichert und zusätzlich per
MQTT veröffentlicht, z. B. zur Verwendung mit Home Assistant.

## Getestete Hardware

- Alpha Innotec LWW 122R3
- Softwarestand: V3.92.3-3a381baa
- Modbus TCP Port 502
- Unit-ID 1

## Ausgelesene Register

| Register | Bedeutung |
|---|---|
| 10300 | Aktuelle Heizleistung |
| 10301 | Aktuelle elektrische Leistung |
| 10302 | Minimale elektrische Leistung |
| 10310 | Strom gesamt |
| 10312 | Strom Heizung |
| 10314 | Strom Warmwasser |
| 10320 | Wärmemenge gesamt |
| 10322 | Wärmemenge Heizung |
| 10324 | Wärmemenge Warmwasser |

Register 10300–10302 liefern Leistungswerte in kW/10 und werden als
kW gespeichert.

Register 10310–10324 liefern Energiezähler in kWh/10 und werden als
kWh gespeichert.

- parallel werden die Daten auch an den MQTT Server weitegegeben

## Installation

```bash
pip3 install -r requirements.txt
cp config.example.py config.py

## Beispiel für Cron:
  */3 * * * * /usr/bin/python3 /pfad/luxtronik_influx.py

## Voraussetzung:
  Wärmepumpe ist für Modbus TCP Zugriffe freigeschaltet
  influxdb Datenbank existiert

## Elemente im measurement heatpump_energy
  current_heat
  current_power
  min_power
  heat_energy_heating_kwh
  heat_energy_hotwater_kwh
  heat_energy_total_kwh
  power_heating_kwh
  power_hotwater_kwh
  power_total_kwh
    
## Beispiel MQTT topics:
  heatpump/power_total_kwh 8126.1
  heatpump/power_heating_kwh 6378.2
  heatpump/power_hotwater_kwh 1747.9
  heatpump/heat_energy_total_kwh 58816.5
  heatpump/heat_energy_heating_kwh 49215.8
  heatpump/heat_energy_hotwater_kwh 9600.7
  heatpump/current_heat_kw 0.0
  heatpump/current_power_kw 0.0
  heatpump/min_power_kw 0.0
