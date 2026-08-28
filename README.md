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
| 10000 | Status Wärmepumpe |
| 10002 | Status Betriebsart |
| 10003 | Status Heizen |
| 10004 | Status Warmwasser |
| 10100 | Rücklauftemperatur IST |
| 10101 | Rücklauftemperatur SOLL |
| 10105 | Vorlauftemperatur IST |
| 10120 | Warmwassertemperatur IST |
| 10121 | Warmwassertemperatur SOLL |
| 10108 | Aussentemperatur |
| 10300 | Aktuelle Heizleistung |
| 10301 | Aktuelle elektrische Leistung |
| 10302 | Minimale elektrische Leistung |
| 10310 | Strom gesamt |
| 10312 | Strom Heizung |
| 10314 | Strom Warmwasser |
| 10320 | Wärmemenge gesamt |
| 10322 | Wärmemenge Heizung |
| 10324 | Wärmemenge Warmwasser |

Register 10000–10004 liefern Statuswerte (UINT16)

Register 10100–10105 liefern Temperaturwerte in °C/10 und werden als
°C gespeichert.

Register 10120–10121 liefern Temperaturwerte in °C/10 und werden als
°C gespeichert.

Register 10300–10302 liefern Temperaturwerte in kW/10 und werden als
kW gespeichert.

Register 10310–10324 liefern Energiezähler in kWh/10 und werden als
kWh gespeichert.

- parallel werden die Daten auch an den MQTT Server weitegegeben

## Installation

```bash
pip3 install -r requirements.txt
cp config.example.py config.py
```

## Beispiel für Cron:
```text
  */3 * * * * /usr/bin/python3 /pfad/luxtronik_influx.py
```

## Voraussetzung:
  Wärmepumpe ist für Modbus TCP Zugriffe freigeschaltet
  influxdb Datenbank existiert

## Elemente im measurement heatpump_energy
```text
fieldKey                 fieldType
--------                 ---------
current_heat             float
current_power            float
flow_real                float
heat_energy_heating_kwh  float
heat_energy_hotwater_kwh float
heat_energy_total_kwh    float
hotwater_real_temp       float
hotwater_target_temp     float
min_power                float
outside_temp             float
power_heating_kwh        float
power_hotwater_kwh       float
power_total_kwh          float
reflux_real              float
reflux_target            float
stat_heating             integer
stat_heatpump            integer
stat_hotwater            integer
stat_mode                integer
```
    
## Beispiel MQTT topics:
```text
heatpump/power_total_kwh 8133.2
heatpump/power_heating_kwh 6378.2
heatpump/power_hotwater_kwh 1755.0
heatpump/heat_energy_total_kwh 58843.0
heatpump/heat_energy_heating_kwh 49215.8
heatpump/heat_energy_hotwater_kwh 9627.2
heatpump/current_heat_kw 0.0
heatpump/current_power_kw 0.0
heatpump/min_power_kw 1.4
heatpump/outside_temp_c 22.1
heatpump/reflux_target_c 23.0
heatpump/reflux_real_c 15.0
heatpump/flow_real_c 31.0
heatpump/hotwater_target_temp_C 52.5
heatpump/hotwater_real_temp_C 50.6
heatpump/stat_heatpump 0
heatpump/stat_mode 5
heatpump/stat_heating 1
heatpump/stat_hotwater 1
```
