# Version 6
# Write data to a file on flash until DNS issues are resolved

# Version 5
# Change format for floating point percentage to :3.0f
# Send summary to paul.cronhardt and full message to home.paul.cronhardt

# Version 4
# Fix division for percent on time
# Reset Start time at end of day
# Use calendar.timegm() to compute total time
# Use last sample time for delta end time

# Version 3
# Add summary to top of email
# Minutes Total Minutes, Top On Minutes, Bottom On Minutes, %Time On
# ---------------------------------------------------------------------- 
import calendar
import glob
import time
import os
import smtplib
import RPi.GPIO as GPIO
 
def read_temp_raw(dev):
  f = open(dev, 'r')
  lines = f.readlines()
  f.close()
  return lines

def read_temp(dev):
  lines = read_temp_raw(dev)
  while lines[0].strip()[-3:] != 'YES':
    time.sleep(0.2)
    lines = read_temp_raw()
  equals_pos = lines[1].find('t=')
  if equals_pos != -1:
    temp_string = lines[1][equals_pos+2:]
    temp_c = float(temp_string) / 1000.0
    temp_f = temp_c * 9.0 / 5.0 + 32.0
    return temp_f

def readPhoto (RCpin):
  reading = 0
  GPIO.setup(RCpin, GPIO.OUT)
  GPIO.output(RCpin, GPIO.LOW)
  time.sleep(0.1)
 
  GPIO.setup(RCpin, GPIO.IN)
  # This takes about 1 millisecond per loop cycle
  while ((GPIO.input(RCpin) == GPIO.LOW) and (reading < 256)):
    reading += 1
    time.sleep(0.01)
  return reading
 
GPIO.setmode(GPIO.BCM)

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28*')
deviceTop = device_folders[0] + '/w1_slave'
deviceBot = device_folders[1] + '/w1_slave'

start_time = time.localtime()
top_on_mins = 0
bot_on_mins = 0
prev_day = start_time.tm_mday

def log_data(t, string):
  file_name = time.strftime('%Y%m%d_log', t) + '.txt'
  f = open(file_name, 'w')
  f.write(string)
  f.close()

data_string = ''
while (not os.path.exists('stop.txt')):
  t = time.localtime()
  curr_day = t.tm_mday
  while (not os.path.exists('stop.txt') and (curr_day == prev_day)):
    t = time.localtime()
    curr_day = t.tm_mday
    st = time.strftime('%m/%d/%Y %H:%M:%S', t)

    # readPhoto(pin) returns 255 when the LED is off
    topLED = (0, 1)[readPhoto(17) < 250]
    top_on_mins += topLED
    botLED = (0, 1)[readPhoto(27) < 250]
    bot_on_mins += botLED
    st += '{:2d}{:4.0f}{:2d}{:4.0f}'.format(topLED, read_temp(deviceTop),
          botLED, read_temp(deviceBot))
    print st
    data_string += st
    data_string += '\n'

    time.sleep(53)

  end_time = t
  delta_mins = (calendar.timegm(end_time) - calendar.timegm(start_time)) / 60
  percent = int(((top_on_mins+bot_on_mins+0.0)/delta_mins)*100)
  summary = 'Total Mins {:4d} Top Mins {:4d} Bot Mins {:4d} On {:3.0f}%' \
            .format(delta_mins, top_on_mins, bot_on_mins, percent)
  summary += '\n'
  data_string = summary + data_string
  log_data(end_time, data_string)

  data_string = ''
  prev_day = curr_day
  start_time = time.localtime()
  top_on_mins = 0
  bot_on_mins = 0

os.remove('stop.txt')
if (len(data_string) > 0):
  end_time = t
  delta_mins = (calendar.timegm(end_time) - calendar.timegm(start_time)) / 60
  percent = int(((top_on_mins+bot_on_mins+0.0)/delta_mins)*100)
  summary = 'Total Mins {:4d} Top Mins {:4d} Bot Mins {:4d} On {:3.0f}%' \
            .format(delta_mins, top_on_mins, bot_on_mins, percent)
  summary += '\n'
  data_string = summary + data_string
  log_data(end_time, data_string)

