import subprocess
import sys
import pytest
from unittest.mock import MagicMock
from prometheus_client import CollectorRegistry, Gauge
import main
from sensor import SensorSerialError


@pytest.fixture
def registry():
    return CollectorRegistry()


@pytest.fixture
def gauge(registry):
    return main.build_gauges(registry=registry)


def test_build_gauges_creates_expected_metrics():
    gauge = main.build_gauges(registry=CollectorRegistry())
    expected_keys = [
        'temperature', 'relative_humidity', 'ambient_light', 'barometric_pressure',
        'sound_noise', 'eTVOC', 'eCO2', 'discomfort_index', 'heat_stroke',
        'vibration_information', 'si_value', 'pga', 'seismic_intensity',
    ]
    assert set(gauge.keys()) == set(expected_keys)
    for key in expected_keys:
        assert isinstance(gauge[key], Gauge)


def test_update_gauges_happy_path(registry, gauge):
    sen = MagicMock()
    sen.read.return_value.get_all.return_value = {
        'temperature': 25.5, 'relative_humidity': 60.12, 'ambient_light': 500,
        'barometric_pressure': 1000.0, 'sound_noise': 45.67, 'eTVOC': 123, 'eCO2': 456,
        'discomfort_index': 70.55, 'heat_stroke': 28.3, 'vibration_information': 2,
        'si_value': 3.5, 'pga': 12.3, 'seismic_intensity': 4.567,
        'unrelated_key': 999,  # gaugeに存在しないキーは無視されるべき
    }
    main.update_gauges(sen, gauge)
    sen.read.assert_called_once()
    assert registry.get_sample_value('sensor_omron_temperature') == 25.5
    assert registry.get_sample_value('sensor_omron_humidity') == 60.12
    assert registry.get_sample_value('sensor_omron_light') == 500
    assert registry.get_sample_value('sensor_omron_barometric') == 1000.0
    assert registry.get_sample_value('sensor_omron_noise') == 45.67
    assert registry.get_sample_value('sensor_omron_etvoc') == 123
    assert registry.get_sample_value('sensor_omron_eco2') == 456
    assert registry.get_sample_value('sensor_omron_discomfort') == 70.55
    assert registry.get_sample_value('sensor_omron_heat') == 28.3
    assert registry.get_sample_value('sensor_omron_vibration') == 2
    assert registry.get_sample_value('sensor_omron_si') == 3.5
    assert registry.get_sample_value('sensor_omron_pga') == 12.3
    assert registry.get_sample_value('sensor_omron_seismic') == 4.567


def test_update_gauges_propagates_sensor_serial_error(gauge):
    sen = MagicMock()
    sen.read.side_effect = SensorSerialError('boom')
    with pytest.raises(SensorSerialError):
        main.update_gauges(sen, gauge)


def test_import_main_has_no_side_effects():
    result = subprocess.run(
        [sys.executable, '-c',
         "import main; import prometheus_client; "
         "names = {m.name for m in prometheus_client.REGISTRY.collect()}; "
         "assert not any(n.startswith('sensor_omron_') for n in names), names"],
        capture_output=True, timeout=5, text=True,
    )
    assert result.returncode == 0, result.stderr
