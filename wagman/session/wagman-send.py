from serial import Serial
import sys

serial = Serial(sys.argv[1])

while True:
    serial.write(input('$ ').encode('ascii'))
    serial.write(b'\n')

serial.close()
