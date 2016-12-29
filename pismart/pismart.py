from basic import _Basic_class
from adc import ADC
import math
from time import sleep
import os
import commands

class PiSmart(_Basic_class):
    _class_name = 'PiSmart'
    
    ON  = 1
    OFF = 0

    SERVO_POWER_OFF     = 0x20
    SERVO_POWER_ON      = 0x21
    SPEAKER_POWER_OFF   = 0x22
    SPEAKER_POWER_ON    = 0x23
    MOTOR_POWER_OFF     = 0x24
    MOTOR_POWER_ON      = 0x25
    SET_POWER_DC        = 0X26  # power_type = 0, DC power
    SET_POWER_2S        = 0X27  # power_type = 1, Li-po battery 2s
    SET_POWER_3S        = 0X28  # power_type = 2, Li-po battery 3s

    POWER_TYPE          = 0X1d  # send this number to ask arduino return power-type

    def __init__(self):
        self.logger_setup()
        self.speaker_volume = 70
        self.capture_volume = 100
        tmp = self.power_type
        sleep(0.01)         # when arduino open debug, sleep(> 0.3)
        self.adc = ADC(5)
        self._debug('Init PiSmart object complete')

    def servo_switch(self, on_off):
        self.pwm_switch(on_off)

    def pwm_switch(self, on_off):
        if on_off not in (0, 1):
            raise ValueError ("On_off set must be .ON(1) or .OFF(0), not \"{0}\".".format(on_off))
        if on_off == 1:
            self._write_sys_byte(self.SERVO_POWER_ON)
            self._debug('Servo switch ON')
        else:
            self._write_sys_byte(self.SERVO_POWER_OFF)
            self._debug('Servo switch OFF')

    def motor_switch(self, on_off):
        if on_off not in (0, 1):
            raise ValueError ("On_off set must be .ON(1) or .OFF(0), not \"{0}\".".format(on_off))
        if on_off == 1:
            self._write_sys_byte(self.MOTOR_POWER_ON)
            self._debug('Motor switch ON')
        else:
            self._write_sys_byte(self.MOTOR_POWER_OFF)
            self._debug('Motor switch OFF')

    def speaker_switch(self, on_off):
        if on_off not in (0, 1):
            raise ValueError ("On_off set must in .ON(1) or .OFF(0), not \"{0}\".".format(on_off))
        if on_off == 1:
            self._write_sys_byte(self.SPEAKER_POWER_ON)
            self._debug('Speaker switch ON')
        else:
            self._write_sys_byte(self.SPEAKER_POWER_OFF)
            self._debug('Speaker switch OFF')

    @property
    def power_type(self):
        self._power_type = self._read_sys_byte(self.POWER_TYPE)
        self._debug('Get power type from bottom board')
        return self._power_type
    
    @power_type.setter
    def power_type(self, power_type):
        if power_type not in ['2S', '3S', 'DC']:
            raise ValueError ('Power type only support: "2S", "3S" Li-po battery or "DC" power, not \"{0}\".'.format(power_type))
        else:
            self._power_type = power_type
            if power_type == '2S':
                self._write_sys_byte(self.SET_POWER_2S)
                self._debug('Set power type to 2S Li-po battery')
            elif power_type == '3S':
                self._write_sys_byte(self.SET_POWER_3S)
                self._debug('Set power type to 3S Li-po battery')
            elif power_type == 'DC':
                self._write_sys_byte(self.SET_POWER_DC)
                self._debug('Set power type to DC power')

    @property
    def power_voltage(self):
        A7_value = self.adc.read()
        A7_volt = float(A7_value) / 1024 * 5
        battery_volt = round(A7_volt * 14.7 / 4.7, 2)
        self._debug('Read battery: %s V' % battery_volt)
        return battery_volt

    @property
    def speaker_volume(self):
        return self._speaker_volume
    
    @speaker_volume.setter
    def speaker_volume(self, value):
        if value > 100:
            value = 100
            self._warning('Value is over 100, set to 100')
        if value < 0:
            value = 0
            self._warning('Value is less than 0, set to 0')
        # gain(dB) = 10 * log10(volume)
        self._speaker_volume = self._map(value, 0, 100, 10.0**(-102.39/10), 10.0**(4.0/10))
        self._speaker_volume = int(math.log10(self._speaker_volume) * 100) * 10
        self._debug('speaker dB = %s' % self._speaker_volume)
        cmd = "sudo amixer cset numid=1 -- %d" % self._speaker_volume
        self.run_command(cmd)
    
    @property
    def capture_volume(self):
        return self._capture_volume

    @capture_volume.setter
    def capture_volume(self, value):
        capture_volume_id = self._get_capture_volume_id()
        if value not in range(0, 101):
            raise ValueError ("Volume should be in [0, 100], not \"{0}\".".format(value))
        self._capture_volume = self._map(value, 0, 100, 0, 16)
        cmd = "sudo amixer -c 1 cset numid=%s -- %d" % (capture_volume_id, self._capture_volume)
        self.run_command(cmd)
        return 0

    def _get_capture_volume_id(self):
        all_controls = self.run_command("sudo amixer -c 1 controls")
        all_controls = all_controls.split('\n')
        capture_volume = ''
        capture_volume_id = ''
        for line in all_controls:
            if 'Mic Capture Volume' in line:
                capture_volume = line
        capture_volume=capture_volume.split(',')
        for variable in capture_volume:
            if 'numid' in variable:
                capture_volume_id = variable
        capture_volume_id = capture_volume_id.split('=')[1]
        return int(capture_volume_id)

    @property
    def cpu_temperature(self):
        raw_cpu_temperature = commands.getoutput("cat /sys/class/thermal/thermal_zone0/temp")
        cpu_temperature = float(raw_cpu_temperature)/1000
        #cpu_temperature = 'Cpu temperature : ' + str(cpu_temperature)
        return cpu_temperature

    @property
    def gpu_temperature(self):
        raw_gpu_temperature = commands.getoutput( '/opt/vc/bin/vcgencmd measure_temp' )
        gpu_temperature = float(raw_gpu_temperature.replace( 'temp=', '' ).replace( '\'C', '' ))
        #gpu_temperature = 'Gpu temperature : ' + str(gpu_temperature)
        return gpu_temperature

    @property
    def ram_info(self):
        p = os.popen('free')
        i = 0
        while 1:
            i = i + 1
            line = p.readline()
            if i==2:
                return line.split()[1:4]

    @property
    def ram_total(self):
        ram_total = round(int(self.ram_info[0]) / 1000,1)
        return ram_total

    @property
    def ram_used(self):
        ram_used = round(int(self.ram_info[1]) / 1000,1)
        return ram_used

    @property
    def disk_space(self):
        p = os.popen("df -h /")
        i = 0
        while 1:
            i = i +1
            line = p.readline()
            if i==2:
                return line.split()[1:5]

    @property
    def disk_total(self):
        disk_total = float(self.disk_space[0][:-1])
        return disk_total

    @property
    def disk_used(self):
        disk_used = float(self.disk_space[1][:-1])
        return disk_used

    @property                    
    def cpu_usage(self):
        return str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip())
