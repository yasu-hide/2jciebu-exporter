import pytest
import serial

from sensor import Sensor, SensorSerialError
from tests.conftest import READ_FIXTURE_BYTES, READ_FIXTURE_EXPECTED


# ---------------------------------------------------------------------------
# _get_command
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "buf, expected_crc",
    [
        (Sensor.SENSOR_NORMALLY_ON, bytearray([0xd2, 0x35])),
        (Sensor.SENSOR_NORMALLY_OFF, bytearray([0xae, 0x05])),
        (Sensor.SENSOR_READ, bytearray([0xe2, 0x4b])),
        (bytearray([]), bytearray([0xff, 0xff])),
        (bytearray([0x00]), bytearray([0xbf, 0x40])),
    ],
)
def test_get_command(sensor, buf, expected_crc):
    result = sensor._get_command(buf)
    assert result == buf + expected_crc
    assert len(result) == len(buf) + 2
    assert result[:len(buf)] == buf
    assert isinstance(result, bytearray)


# ---------------------------------------------------------------------------
# isopen
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "isopened, port_is_open, expected",
    [
        (False, True, False),
        (True, True, True),
        (True, False, False),
    ],
)
def test_isopen(sensor, mock_port, isopened, port_is_open, expected):
    sensor.isopened = isopened
    mock_port.is_open = port_is_open
    assert sensor.isopen() == expected


# ---------------------------------------------------------------------------
# open
# ---------------------------------------------------------------------------

def test_open_normal(sensor, mock_port):
    sensor.isopened = False
    result = sensor.open()
    mock_port.write.assert_called_once_with(
        sensor._get_command(Sensor.SENSOR_NORMALLY_ON)
    )
    assert sensor.isopened is True
    assert result == mock_port.read.return_value


def test_open_noop_when_already_open(sensor, mock_port):
    sensor.isopened = True
    mock_port.is_open = True
    result = sensor.open()
    assert result is None
    mock_port.write.assert_not_called()


def test_open_error_converted(sensor, mock_port):
    sensor.isopened = False
    mock_port.write.side_effect = serial.SerialException('boom')
    with pytest.raises(SensorSerialError):
        sensor.open()
    assert sensor.isopened is False


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------

def test_close_noop_when_not_open(sensor, mock_port):
    sensor.isopened = False
    result = sensor.close()
    assert result is None
    mock_port.write.assert_not_called()


def test_close_normal(sensor, mock_port):
    sensor.isopened = True
    mock_port.is_open = True
    sensor.close()
    mock_port.write.assert_called_once_with(
        sensor._get_command(Sensor.SENSOR_NORMALLY_OFF)
    )
    assert sensor.isopened is False


def test_close_retries_once_then_succeeds(sensor, mock_port):
    calls = {'n': 0}

    def flaky_write(data):
        calls['n'] += 1
        if calls['n'] == 1:
            raise serial.SerialException('transient')

    mock_port.write.side_effect = flaky_write
    sensor.isopened = True
    sensor.close()
    assert mock_port.write.call_count == 2
    assert sensor.isopened is False


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------

def test_read_normal(sensor, mock_port):
    sensor.isopened = True
    mock_port.is_open = True
    mock_port.inWaiting.return_value = 58
    mock_port.read.return_value = READ_FIXTURE_BYTES

    result = sensor.read()

    assert result is sensor
    assert sensor.get_all() == pytest.approx(READ_FIXTURE_EXPECTED)


def test_read_invalid_length_leaves_data_unchanged(sensor, mock_port):
    sensor.isopened = True
    mock_port.is_open = True
    sensor.data = {'temperature': 1.23}
    mock_port.inWaiting.return_value = 10
    mock_port.read.return_value = b'\x00' * 10

    result = sensor.read()

    assert sensor.data == {'temperature': 1.23}
    assert result is sensor


def test_read_serial_exception_before_open_propagates(sensor, mock_port):
    sensor.isopened = False
    mock_port.write.side_effect = serial.SerialException('boom')

    with pytest.raises(SensorSerialError):
        sensor.read()


def test_read_serial_exception_after_open_is_swallowed(sensor, mock_port):
    sensor.isopened = True
    mock_port.is_open = True

    read_command = bytes(sensor._get_command(Sensor.SENSOR_READ))

    def write_side_effect(data):
        if bytes(data).startswith(read_command[:len(Sensor.SENSOR_READ)]):
            raise serial.SerialException('read failed')

    mock_port.write.side_effect = write_side_effect

    result = sensor.read()

    assert result is sensor
    assert sensor.isopened is False


# ---------------------------------------------------------------------------
# get_all / getters
# ---------------------------------------------------------------------------

GETTERS = [
    ('get_temperature', 'temperature', 0.0),
    ('get_relative_humidity', 'relative_humidity', 0.0),
    ('get_ambient_light', 'ambient_light', 0),
    ('get_barometric_pressure', 'barometric_pressure', 0.0),
    ('get_sound_noise', 'sound_noise', 0.0),
    ('get_eTVOC', 'eTVOC', 0),
    ('get_eCO2', 'eCO2', 0),
    ('get_discomfort_index', 'discomfort_index', 0.0),
    ('get_heat_stroke', 'heat_stroke', 0.0),
    ('get_vibration_information', 'vibration_information', 0),
    ('get_si_value', 'si_value', 0.0),
    ('get_pga', 'pga', 0.0),
    ('get_seismic_intensity', 'seismic_intensity', 0.0),
]


def test_getters_with_values(sensor):
    values = {key: index for index, (_, key, _) in enumerate(GETTERS)}
    sensor.data = values

    for method, key, _default in GETTERS:
        assert getattr(sensor, method)() == values[key]

    assert sensor.get_all() == values


def test_getters_default_values(sensor):
    sensor.data = {}

    for method, _key, default in GETTERS:
        assert getattr(sensor, method)() == default

    assert sensor.get_all() == {}
