
#!/usr/bin/python

# The purpose of this script is to read the battery voltage using the MCP3008 ADC
# through the SPI of the raspberry pi and then display the battery level to the user.
#
# The ADC is 10-bit and will be powered with 5V therefore the resolution is 5 / 1024 = 0.00488V / bit
#
#
# |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~LED Logic*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
# |          PI            |             LED             |                     Voltage                   |
# |  Pin    |     Desc     |  Pin  |    Colour   | State | Percent |     Volts     |   Bits  | # of bits |
# --------------------------------------------------------------------------------------------------------
#   10/12/8  GPIO 15/18/14   3/4/1   GRN/YEL/RED     6      > 100%       >= 4.248V    >= 870     >=10
#        10        GPIO 15       3           GRN     5     80-100%   4.003V-4.203V   819-860       41
#     10/12     GPIO 15/18     3/4       GRN/YEL     4      60-80%   3.803V-4.003V   778-819       41
#        12        GPIO 18       4           YEL     3      40-60%   3.602V-3.803V   737-778       41
#      12/8     GPIO 18/14     4/1       YEL/RED     2      20-40%   3.402V-3.602V   696-737       41
#         8        GPIO 14       1           RED     1       0-20%   3.201V-3.402V   655-696       41
#      10/8     GPIO 15/14     3/1       GRN/RED     0        < 0%       <= 3.149V    <= 645     <=10
#
# * Hysterisis is required to avoid flickering. 5% or 0.0488V or 10 bits will be used
#
#
# Note: more GND pins are availble on the raspi
#
# |~~~~~~~~LED Wiring~~~~~~~~~|
# |     PI     |     LED      |
# | Pin | Desc | Pin | Colour |
# -----------------------------
#    6      GND   2     comm
#    8   GPIO14   1      RED
#   10   GPIO15   3      GRN
#   12   GPIO18   4      YEL
#
# |~~~~~~~~~~~~~MCP3008 Wiring~~~~~~~~~~~~~|
# |    MCP3008   |      PI      | Battery  |
# | Pin |  Desc  | Pin |  Desc  | Temrinal |
# ------------------------------------------
#    1       CH0                     POS
#    9      DGND    6       GND      NEG
#   10        CS   24       CE0
#   11       Din   19      MOSI
#   12      Dout   21      MISO
#   13       CLK   23      SCLK
#   14      AGND    6       GND      NEG
#   15      Vref    2        5V
#   16       Vdd    2        5V
#
#

import spidev
import time
import os

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0,0)

# Set GPIO to board mode
GPIO.setmode(GPIO.board)

# Set GPIO pins to outputs
GPIO.setup(8, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(10, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(12, GPIO.OUT, initial=GPIO.HIGH)

# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def ReadChannel(channel):
  adc = spi.xfer2([1,(8+channel)<<4,0])
  data = ((adc[1]&3) << 8) + adc[2]
  return data

# Function for calculating LED State
def LEDState(led,vbat):
  if vbat > 860:
      ledstate = 6
  elif 819 < vbat <= 860:
      ledstate = 5
  elif 778 < vbat <= 819:
      ledstate = 4
  elif 737 < vbat <= 778:
      ledstate = 3
  elif 696 < vbat <= 737:
      ledstate = 2
  elif 655 < vbat <= 696:
      ledstate = 1
  elif vbat <= 655:
      ledstate = 0

  # Adding in hysterisis when within normal values. When bettery voltage passes extreme thresholds ledstate updates without hysterisis.
  hyst = 5
  if ledstate < led and vbat < vthresh[led] - hyst and 1 <= ledstate <= 5:
      lednew = ledstate
  elif ledstate > led and vbat > vthresh[ledstate] + hyst and 1 <= ledstate <= 5:
      lednew = ledstate
  elif ledstate = 0 or ledstate = 6:
      lednew = ledstate
  else:
      lednew = led

  return lednew


# Define sensor channels
bat_channel = 0

# Initial voltage reading
bat_level = ReadChannel(bat_channel)

# Define initial LED State
led_state = 6
led_state = LEDState(led_state,bat_level)

# Define lists for GPIO levels for a given LED State (make setting GPIO easy)
io8  = [1,1,1,0,0,0,1]
io10 = [1,0,0,0,1,1,1]
io12 = [0,0,1,1,1,0,1]

# Define list for voltage thresholds
#            0   1   2   3   4   5   6
vthresh = [645,655,696,737,778,819,860]

# Define delay between readings
delay = 5



while True:

  # Read the light sensor data
  bat_level = ReadChannel(bat_channel)

  # Calculate LED state
  led_state = LEDState(led_state,bat_level)

  # Setting GPIO
  GPIO.output(8, io8[led_state])
  GPIO.output(10, io10[led_state])
  GPIO.output(12, io12[led_state])

  # Print out results
  print "--------------------------------------------"
  print("Battery Voltage: {} ({}V)".format(bat_level,bat_level*5/1024))

  # Wait before repeating loop
  time.sleep(delay)
