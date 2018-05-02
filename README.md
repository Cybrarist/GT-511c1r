# GT-511c1r
Improved firmware for GT-511c1r Fingerprint on Raspberry pi in python language 

The code "basic.py" is an improved version of (https://github.com/zafartahirov/fingerpi), you can see all the function in the zafartahirov's code because i've removed some of them.

if you want to add a function to basic.py, you can use sendCommand('name of command').

The main.py file has the code to Enroll a fingerprint, delete all fingerprints, get how many fingerprints been enrolled and to verify if that fingerprint been enrolled before.

if you're using RPi 3, please notice that the code is using ttyAMA0 not ttyS0, so you need to disable bluetooth and switch between them so that serial ports can work on ttyAMA0.




