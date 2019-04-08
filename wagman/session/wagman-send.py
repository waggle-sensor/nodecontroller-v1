from serial import Serial
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license
import sys

serial = Serial(sys.argv[1])

while True:
    serial.write(input('$ ').encode('ascii'))
    serial.write(b'\n')

serial.close()
