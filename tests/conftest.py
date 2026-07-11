import pytest
from unittest.mock import MagicMock, patch
from sensor import Sensor

READ_FIXTURE_HEX = "aaaaaaaaaaaaaaaaf6097c17f40140420f00d7117b00c8018f1b0e0b0223007b00d7110000000000000000000000000000000000000000000000"
READ_FIXTURE_BYTES = bytes.fromhex(READ_FIXTURE_HEX)
READ_FIXTURE_EXPECTED = {
    'temperature': 25.5, 'relative_humidity': 60.12, 'ambient_light': 500,
    'barometric_pressure': 1000.0, 'sound_noise': 45.67, 'eTVOC': 123, 'eCO2': 456,
    'discomfort_index': 70.55, 'heat_stroke': 28.3, 'vibration_information': 2,
    'si_value': 3.5, 'pga': 12.3, 'seismic_intensity': 4.567,
}


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr('sensor.time.sleep', lambda *a, **k: None)


@pytest.fixture
def mock_port():
    port = MagicMock()
    port.is_open = True
    port.inWaiting.return_value = 0
    port.read.return_value = b''
    return port


@pytest.fixture
def sensor(mock_port):
    with patch('sensor.serial.Serial', return_value=mock_port):
        return Sensor('/dev/ttyFAKE')
