#!/usr/bin/env python3
from sensor import Sensor, SensorSerialError
from prometheus_client import start_http_server, Gauge
import time
import os, signal
import logging
logging.basicConfig(level=logging.DEBUG)


def build_gauges(registry=None):
    """Construct the Gauge objects used to export sensor readings.

    Pass a dedicated prometheus_client.CollectorRegistry (e.g. in tests) to
    avoid colliding with the global default registry across multiple calls.
    """
    kwargs = {'registry': registry} if registry is not None else {}
    return {
        'temperature': Gauge('sensor_omron_temperature', 'Temperature', **kwargs),
        'relative_humidity': Gauge('sensor_omron_humidity', 'Humidity', **kwargs),
        'ambient_light': Gauge('sensor_omron_light', 'Ambient light', **kwargs),
        'barometric_pressure': Gauge('sensor_omron_barometric', 'Barometric pressure', **kwargs),
        'sound_noise': Gauge('sensor_omron_noise', 'Sound noise', **kwargs),
        'eTVOC': Gauge('sensor_omron_etvoc', 'eTVOC', **kwargs),
        'eCO2': Gauge('sensor_omron_eco2', 'eCO2', **kwargs),
        'discomfort_index': Gauge('sensor_omron_discomfort', 'Discomfort index', **kwargs),
        'heat_stroke': Gauge('sensor_omron_heat', 'Heat stroke', **kwargs),
        'vibration_information': Gauge('sensor_omron_vibration', 'Vibration information', **kwargs),
        'si_value': Gauge('sensor_omron_si', 'SI value', **kwargs),
        'pga': Gauge('sensor_omron_pga', 'PGA', **kwargs),
        'seismic_intensity': Gauge('sensor_omron_seismic', 'Seismic intensity', **kwargs),
    }


def open_sensor_with_retry(sen, retry_interval=10):
    """Retry sen.open() on SensorSerialError instead of letting it crash the process.

    Mirrors the same log/sleep/retry behavior the __main__ loop already uses
    for read failures, so startup connection failures aren't treated
    differently than in-loop ones.
    """
    while True:
        try:
            sen.open()
            return
        except SensorSerialError:
            logging.error('Sensor serial error occurred.', exc_info=True)
            time.sleep(retry_interval)


def update_gauges(sen, gauge):
    """One poll cycle: read the sensor and push values into `gauge`.

    Does NOT catch SensorSerialError itself -- it propagates unchanged so
    the caller (the __main__ loop) retains the same retry/backoff behavior
    as before.
    """
    for (k, v) in sen.read().get_all().items():
        if k in gauge:
            gauge[k].set(v)


if __name__ == "__main__":
    SENSOR_SERIAL_DEVICE = os.environ.get('SENSOR_SERIAL_DEVICE', '/dev/ttyUSB0')
    SERVER_HTTP_PORT = int(os.environ.get('SERVER_HTTP_PORT', 8000))
    start_http_server(SERVER_HTTP_PORT)
    gauge = build_gauges()
    logging.debug('start')
    sen = Sensor(SENSOR_SERIAL_DEVICE)
    signal.signal(signal.SIGTERM, lambda *args: sen.close())
    signal.signal(signal.SIGINT, lambda *args: sen.close())
    open_sensor_with_retry(sen)
    try:
        while sen.isopen():
            try:
                update_gauges(sen, gauge)
            except SensorSerialError:
                logging.error('Sensor serial error occurred.', exc_info=True)
                time.sleep(10)
                continue
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    except:
        logging.error('An error occurred.', exc_info=True)
    sen.close()
    logging.debug('end')
