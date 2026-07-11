#!/usr/bin/env python3
import serial
import sys, time
import logging

class SensorSerialError(serial.SerialException): pass
class Sensor:
    SENSOR_NORMALLY_ON = bytearray([0x52, 0x42, 0x0a, 0x00, 0x02, 0x11, 0x51, 0x01, 0x00, 0x00, 0xff, 0x00])
    SENSOR_NORMALLY_OFF = bytearray([0x52, 0x42, 0x0a, 0x00, 0x02, 0x11, 0x51, 0x00, 0x00, 0x00, 0x00, 0x00])
    SENSOR_READ = bytearray([0x52, 0x42, 0x05, 0x00, 0x01, 0x21, 0x50])
    SENSOR_LATEST_DATA_LONG_LEN = 54 + 4
    CLOSE_MAX_RETRIES = 3
    def __init__(self, device='/dev/ttyUSB0', speed=115200, databit=serial.EIGHTBITS, parity=serial.PARITY_NONE):
        self.serial = serial.Serial(device, speed, databit, parity)
        self.isopened = False
        self.data = {}
        self.lastmodified = 0.0
    def _get_command(self, buf):
        length = len(buf)
        crc = 0xFFFF
        for i in range(length):
            crc = crc ^ buf[i]
            for i in range(8):
                carrayFlag = crc & 1
                crc = crc >> 1
                if (carrayFlag == 1):
                    crc = crc ^ 0xA001
        crcH = crc >> 8
        crcL = crc & 0x00FF
        return buf + (bytearray([crcL, crcH]))
    def isopen(self):
        return (self.isopened and self.serial.is_open)
    def open(self):
        if self.isopen():
            return
        try:
            command = self._get_command(self.SENSOR_NORMALLY_ON)
            self.serial.write(command)
            time.sleep(0.5)
            self.isopened = True
            return self.serial.read(self.serial.inWaiting())
        except serial.SerialException as e:
            raise SensorSerialError(e)
    def close(self):
        if not self.isopen():
            return
        attempt = 0
        last_error = None
        while attempt < self.CLOSE_MAX_RETRIES:
            attempt += 1
            try:
                command = self._get_command(self.SENSOR_NORMALLY_OFF)
                self.serial.write(command)
                time.sleep(0.5)
                self.isopened = False
                return self.serial.read(self.serial.inWaiting())
            except serial.SerialException as e:
                last_error = e
                # Retry
        # 上限到達: ポートを強制クローズ扱いにし、例外は握りつぶす
        self.isopened = False
        logging.error(
            'Failed to close sensor after %d attempts.',
            self.CLOSE_MAX_RETRIES,
            exc_info=last_error,
        )
        return
    def read(self):
        if not self.isopen():
            self.open()
        try:
            command = self._get_command(self.SENSOR_READ)
            self.serial.write(command)
            time.sleep(0.5)
            raw = self.serial.read(self.serial.inWaiting())
            if len(raw) == self.SENSOR_LATEST_DATA_LONG_LEN:
                data = bytearray(raw)
                self.data = {
                    'temperature': int('{:02x}{:02x}'.format(data[9], data[8]), 16) / 100.0,
                    'relative_humidity': int('{:02x}{:02x}'.format(data[11], data[10]), 16) / 100.0,
                    'ambient_light': int('{:02x}{:02x}'.format(data[13], data[12]), 16),
                    'barometric_pressure': int('{:02x}{:02x}{:02x}{:02x}'.format(data[17], data[16], data[15], data[14]), 16) / 1000.0,
                    'sound_noise': int('{:02x}{:02x}'.format(data[19], data[18]), 16) / 100.0,
                    'eTVOC': int('{:02x}{:02x}'.format(data[21], data[20]), 16),
                    'eCO2': int('{:02x}{:02x}'.format(data[23], data[22]), 16),
                    'discomfort_index': int('{:02x}{:02x}'.format(data[25], data[24]), 16) / 100.0,
                    'heat_stroke': int('{:02x}{:02x}'.format(data[27], data[26]), 16) / 100.0,
                    'vibration_information': int('{:02x}'.format(data[28]), 16),
                    'si_value': int('{:02x}{:02x}'.format(data[30], data[29]), 16) / 10.0,
                    'pga': int('{:02x}{:02x}'.format(data[32], data[31]), 16) / 10.0,
                    'seismic_intensity': int('{:02x}{:02x}'.format(data[34], data[33]), 16) / 1000.0
                }
        except serial.SerialException:
            self.close()
        return self
    def get_all(self):
        return self.data
    def get_temperature(self):
        return self.data['temperature'] if 'temperature' in self.data else 0.0
    def get_relative_humidity(self):
        return self.data['relative_humidity'] if 'relative_humidity' in self.data else 0.0
    def get_ambient_light(self):
        return self.data['ambient_light'] if 'ambient_light' in self.data else 0
    def get_barometric_pressure(self):
        return self.data['barometric_pressure'] if 'barometric_pressure' in self.data else 0.0
    def get_sound_noise(self):
        return self.data['sound_noise'] if 'sound_noise' in self.data else 0.0
    def get_eTVOC(self):
        return self.data['eTVOC'] if 'eTVOC' in self.data else 0
    def get_eCO2(self):
        return self.data['eCO2'] if 'eCO2' in self.data else 0
    def get_discomfort_index(self):
        return self.data['discomfort_index'] if 'discomfort_index' in self.data else 0.0
    def get_heat_stroke(self):
        return self.data['heat_stroke'] if 'heat_stroke' in self.data else 0.0
    def get_vibration_information(self):
        return self.data['vibration_information'] if 'vibration_information' in self.data else 0
    def get_si_value(self):
        return self.data['si_value'] if 'si_value' in self.data else 0.0
    def get_pga(self):
        return self.data['pga'] if 'pga' in self.data else 0.0
    def get_seismic_intensity(self):
        return self.data['seismic_intensity'] if 'seismic_intensity' in self.data else 0.0


if __name__ == "__main__":
    sen = Sensor().read()
    print("Temperature: {}".format(sen.get_temperature()))
    print("RelativeHumidity: {}".format(sen.get_relative_humidity()))
    print("AmbientLight: {}".format(sen.get_ambient_light()))
    print("BarometicPressure: {}".format(sen.get_barometric_pressure()))
    print("SoundNoise: {}".format(sen.get_sound_noise()))
    print("eTVOC: {}".format(sen.get_eTVOC()))
    print("eCO2: {}".format(sen.get_eCO2()))
    print("DiscomfortIndex: {}".format(sen.get_discomfort_index()))
    print("HeatStroke: {}".format(sen.get_heat_stroke()))
    print("VibrationInformation: {}".format(sen.get_vibration_information()))
    print("PGA: {}".format(sen.get_pga()))
    print("SeismicIntensity: {}".format(sen.get_seismic_intensity()))
