
#!/usr/bin/python

""" ~~MK2 is using the Adafruit library instead of the regular old spidev~~

  The purpose of this script is to read the battery voltage using the MCP3008 ADC
  through the SPI of the raspberry pi and then display the battery level to the user.

  The ADC is 10-bit and will be powered with 5V therefore the resolution is 5 / 1024 = 0.00488V / bit


  |~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~LED Logic*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
  |          PI            |             LED             |                     Voltage                   |
  |  Pin    |     Desc     |  Pin  |    Colour   | State | Percent |     Volts     |   Bits  |   of bits |
  --------------------------------------------------------------------------------------------------------
    10/12/8  GPIO 15/18/14   3/4/1   GRN/YEL/RED     6      > 100%       >= 4.248V    >= 870     >=10
         10        GPIO 15       3           GRN     5     80-100%   4.003V-4.203V   819-860       41
      10/12     GPIO 15/18     3/4       GRN/YEL     4      60-80%   3.803V-4.003V   778-819       41
         12        GPIO 18       4           YEL     3      40-60%   3.602V-3.803V   737-778       41
       12/8     GPIO 18/14     4/1       YEL/RED     2      20-40%   3.402V-3.602V   696-737       41
          8        GPIO 14       1           RED     1       0-20%   3.201V-3.402V   655-696       41
       10/8     GPIO 15/14     3/1       GRN/RED     0        < 0%       <= 3.149V    <= 645     <=10

  * Hysterisis is required to avoid flickering. 5 percent / 0.0488V / 10 bits will be used


  Note: more GND pins are availble on the raspi

  |~~~~~~~~LED Wiring~~~~~~~~~|
  |     PI     |     LED      |
  | Pin | Desc | Pin | Colour |
  -----------------------------
     6      GND   2     comm
     8   GPIO14   1      RED
    10   GPIO15   3      GRN
    12   GPIO18   4      YEL

  |~~~~~~~~~~~~~MCP3008 Wiring~~~~~~~~~~~~~|
  |    MCP3008   |      PI      | Battery  |
  | Pin |  Desc  | Pin |  Desc  | Temrinal |
  ------------------------------------------
     1       CH0                     POS
     9      DGND    6       GND      NEG
    10        CS   24       CE0
    11       Din   19      MOSI
    12      Dout   21      MISO
    13       CLK   23      SCLK
    14      AGND    6       GND      NEG
    15      Vref    2        5V
    16       Vdd    2        5V
"""



""" Loading libraries and initializing GPIO ports
"""
import time
import RPi.GPIO as GPIO

# Import SPI library (for hardware SPI) and MCP3008 library. Adafruitstyle
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

# Software SPI configuration:
#CLK  = 23
#MISO = 21
#MOSI = 19
#CS   = 24
#mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

# Set GPIO to board mode
GPIO.setmode(GPIO.BOARD)

# Define pins
redpin = 8
greenpin = 10
yellowpin = 12

# Set GPIO pins to outputs
GPIO.setup(redpin, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(greenpin, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(yellowpin, GPIO.OUT, initial=GPIO.HIGH)

""" Functions
"""
# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def ReadChannel(channel):
  # If you want to read more than one channel
  #ch = 8 # define number of channels
  #values[0]*ch
  #for i in range(ch):
    #values[i] = mcp.read_adc(i)

  adc = mcp.read_adc(channel)
  return adc

# Function for calculating LED State
def LEDState(ledold,vbat):
  if vbat >= 870:
      ledtmp = 6
  elif 819 < vbat < 870:
      ledtmp = 5
  elif 778 < vbat <= 819:
      ledtmp = 4
  elif 737 < vbat <= 778:
      ledtmp = 3
  elif 696 < vbat <= 737:
      ledtmp = 2
  elif 655 < vbat <= 696:
      ledtmp = 1
  elif vbat <= 655:
      ledtmp = 0

  # Adding in hysterisis when within normal values. When bettery voltage passes extreme thresholds ledtmp updates without hysterisis.
  hyst = 5
  if ledtmp < ledold and vbat < vthresh[ledold] - hyst and 1 <= ledtmp <= 5: # When battery is discharging
      lednew = ledtmp
  elif ledtmp > ledold and vbat > vthresh[ledtmp] + hyst and 1 <= ledtmp <= 5: # When battery is charging
      lednew = ledtmp
  elif ledtmp == 0 or ledtmp == 6 and ledold != ledtmp: # Extreme states
      lednew = ledtmp
  else: # No change. Either led = ledtmp or the hysterisis requirement was not met
      lednew = ledold

  return lednew

""" Defining golobal varables
"""
# Define sensor channels
bat_channel = 0

# Define list for voltage thresholds
#            0   1   2   3   4   5   6
vthresh = [645,655,696,737,778,819,860]

# Initial voltage reading
bat_level = ReadChannel(bat_channel)

# Define initial LED State
led_state = 6
led_state = LEDState(led_state,bat_level)

# Define lists for GPIO levels for a given LED State (make setting GPIO easy)
io8  = [1,1,1,0,0,0,1]
io10 = [1,0,0,0,1,1,1]
io12 = [0,0,1,1,1,0,1]

# Define delay between readings (seconds)
delay = 1

""" Main loop
"""
while True:

  # Read the light sensor data
  bat_level = ReadChannel(bat_channel)
  bat_volts = round(bat_level * (5 / 1023), 2)

  # Calculate LED state
  led_state = LEDState(led_state,bat_level)

  # Setting GPIO
  GPIO.output(8, io8[led_state])
  GPIO.output(10, io10[led_state])
  GPIO.output(12, io12[led_state])

  # Print out results
  print "--------------------------------------------"
  print("Battery Voltage: {} ({}V)".format(bat_level,bat_volts))
  print("LED State: {}".format(led_state))

  # Wait before repeating loop
  time.sleep(delay)
