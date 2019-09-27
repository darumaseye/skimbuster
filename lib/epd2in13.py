# *****************************************************************************
# The present file is a merge between epd2in13.py and epdconfig.py both
# released by Waveshare team with the following license statements:
#
# *****************************************************************************
# * | File        :	  epd2in13.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V4.0
# * | Date        :   2019-06-20
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# /*****************************************************************************
# * | File        :	  epdconfig.py
# * | Author      :   Waveshare team
# * | Function    :   Hardware underlying interface
# * | Info        :
# *----------------
# * | This version:   V1.0
# * | Date        :   2019-06-21
# * | Info        :
# ******************************************************************************
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import logging
import spidev
import RPi.GPIO
import time

class EPD:
    def __init__(self):
        self._RST_PIN = 17
        self._DC_PIN = 25
        self._BUSY_PIN = 24
        self._CS_PIN = 8
        self.EPD_WIDTH = 122
        self.EPD_HEIGHT = 250
        self.GPIO = RPi.GPIO
        self.SPI = spidev.SpiDev(0, 0)

    lut_full_update = [
        0x22, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x11,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E,
        0x01, 0x00, 0x00, 0x00, 0x00, 0x00
    ]

    lut_partial_update = [
        0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x0F, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ]

    def _digital_write(self, pin, value):
        self.GPIO.output(pin, value)

    def _digital_read(self, pin):
        return self.GPIO.input(self._BUSY_PIN)

    def _delay_ms(self, delaytime):
        time.sleep(delaytime / 1000.0)

    def _spi_writebyte(self, data):
        self.SPI.writebytes(data)

    def _module_init(self):
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setwarnings(False)
        self.GPIO.setup(self._RST_PIN, self.GPIO.OUT)
        self.GPIO.setup(self._DC_PIN, self.GPIO.OUT)
        self.GPIO.setup(self._CS_PIN, self.GPIO.OUT)
        self.GPIO.setup(self._BUSY_PIN, self.GPIO.IN)
        self.SPI.max_speed_hz = 4000000
        self.SPI.mode = 0b00
        return 0

    def module_exit(self):
        logging.debug("spi end")
        self.SPI.close()

        logging.debug("close 5V, Module enters 0 power consumption ...")
        self.GPIO.output(self._RST_PIN, 0)
        self.GPIO.output(self._DC_PIN, 0)

        self.GPIO.cleanup()


    # Hardware reset
    def reset(self):
        self._digital_write(self._RST_PIN, 1)
        self._delay_ms(200)
        self._digital_write(self._RST_PIN, 0)
        self._delay_ms(10)
        self._digital_write(self._RST_PIN, 1)
        self._delay_ms(200)

    def send_command(self, command):
        self._digital_write(self._DC_PIN, 0)
        self._digital_write(self._CS_PIN, 0)
        self._spi_writebyte([command])
        self._digital_write(self._CS_PIN, 1)

    def send_data(self, data):
        self._digital_write(self._DC_PIN, 1)
        self._digital_write(self._CS_PIN, 0)
        self._spi_writebyte([data])
        self._digital_write(self._CS_PIN, 1)

    def ReadBusy(self):
        while (self._digital_read(self._BUSY_PIN) == 1):  # 0: idle, 1: busy
            self._delay_ms(100)

    def TurnOnDisplay(self):
        self.send_command(0x22)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0xC4)
        self.send_command(0x20)  # MASTER_ACTIVATION
        self.send_command(0xFF)  # TERMINATE_FRAME_READ_WRITE

        logging.debug("e-Paper busy")
        self.ReadBusy()
        logging.debug("e-Paper busy release")

    def init(self, lut):
        if (self._module_init() != 0):
            return -1
        # EPD hardware init start
        self.reset()
        self.send_command(0x01)  # DRIVER_OUTPUT_CONTROL
        self.send_data((self.EPD_HEIGHT - 1) & 0xFF)
        self.send_data(((self.EPD_HEIGHT - 1) >> 8) & 0xFF)
        self.send_data(0x00)  # GD = 0 SM = 0 TB = 0

        self.send_command(0x0C)  # BOOSTER_SOFT_START_CONTROL
        self.send_data(0xD7)
        self.send_data(0xD6)
        self.send_data(0x9D)

        self.send_command(0x2C)  # WRITE_VCOM_REGISTER
        self.send_data(0xA8)  # VCOM 7C

        self.send_command(0x3A)  # SET_DUMMY_LINE_PERIOD
        self.send_data(0x1A)  # 4 dummy lines per gate

        self.send_command(0x3B)  # SET_GATE_TIME
        self.send_data(0x08)  # 2us per line

        self.send_command(0X3C)  # BORDER_WAVEFORM_CONTROL
        self.send_data(0x03)

        self.send_command(0X11)  # DATA_ENTRY_MODE_SETTING
        self.send_data(0x03)  # X increment; Y increment

        # WRITE_LUT_REGISTER
        self.send_command(0x32)
        for count in range(30):
            self.send_data(lut[count])

        return 0

    ##
    #  @brief: specify the memory area for data R/W
    ##
    def SetWindows(self, x_start, y_start, x_end, y_end):
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end >> 3) & 0xFF)
        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    ##
    #  @brief: specify the start point for data R/W
    ##
    def SetCursor(self, x, y):
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x >> 3) & 0xFF)
        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)
        self.ReadBusy()

    def getbuffer(self, image):
        if self.EPD_WIDTH % 8 == 0:
            linewidth = int(self.EPD_WIDTH / 8)
        else:
            linewidth = int(self.EPD_WIDTH / 8) + 1

        buf = [0xFF] * (linewidth * self.EPD_HEIGHT)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        if (imwidth == self.EPD_WIDTH and imheight == self.EPD_HEIGHT):
            logging.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    if pixels[x, y] == 0:
                        # x = imwidth - x
                        buf[int(x / 8) + y * linewidth] &= ~(0x80 >> (x % 8))
        elif (imwidth == self.EPD_HEIGHT and imheight == self.EPD_WIDTH):
            logging.debug("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.EPD_HEIGHT - x - 1
                    if pixels[x, y] == 0:
                        # newy = imwidth - newy - 1
                        buf[int(newx / 8) + newy * linewidth] &= ~(0x80 >> (y % 8))
        return buf

    def display(self, image):
        if self.EPD_WIDTH % 8 == 0:
            linewidth = int(self.EPD_WIDTH / 8)
        else:
            linewidth = int(self.EPD_WIDTH / 8) + 1

        self.SetWindows(0, 0, self.EPD_WIDTH, self.EPD_HEIGHT);
        for j in range(0, self.EPD_HEIGHT):
            self.SetCursor(0, j);
            self.send_command(0x24);
            for i in range(0, linewidth):
                self.send_data(image[i + j * linewidth])
        self.TurnOnDisplay()

    def Clear(self, color):
        if self.EPD_WIDTH % 8 == 0:
            linewidth = int(self.EPD_WIDTH / 8)
        else:
            linewidth = int(self.EPD_WIDTH / 8) + 1

        self.SetWindows(0, 0, self.EPD_WIDTH, self.EPD_HEIGHT);
        for j in range(0, self.EPD_HEIGHT):
            self.SetCursor(0, j);
            self.send_command(0x24);
            for i in range(0, linewidth):
                self.send_data(color)
        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x10)  # enter deep sleep
        self.send_data(0x01)
        self._delay_ms(100)

        self.module_exit()

### END OF FILE ###