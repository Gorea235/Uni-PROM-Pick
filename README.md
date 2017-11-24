# Introduction 
The main source code for the first-year university PROM module. This project is the 'pick' system, where we had to use an I2C device and some hardware to create a system that would able to break into the lock system we had to create (which can be found [here](https://github.com/Gorea235/Uni-PROM-Lock)).

This repo was initially hosted on VSTS to allow us to work on the code in private, which is why the names attached to the commits are odd.

# Functionality
A lot of the functionality of this system is based off the [lock](https://github.com/Gorea235/Uni-PROM-Lock) system, so I recommend looking at that first.

This system is a picker for the lock system. It works by having lines connect to the lock hardware and writing and reading values to it to input digits and recieve output. The hardware of this system is a GPIO expander driving and reading open collectors. In order to simulate the pressing of digits, the system writes which column should be pulled down into the bus, which then drives the open collectors which are connected to the lock keypad column. Since the lock system loops through the rows to check the columns, I designed a logic system that got the row values, and the value of which row and column was requested, and put them through a set of NOT, OR and AND gates, and the output of this was fed to the open collectors. By doing this, the open collector for the given column will only be activated when the row on the locker matched the row given by the picker.

In order to check the result of a digit press, we used open collectors wired in reverse connected to the green and red LEDs on the lock. These lines will be read (or it will wait for an interrupt if `USE_INTERRUPT` is enabled in [interface.py](/src/interface.py)) and inform the picker on the state of the lock.

The picker has support for both the imemdiate and full reject modes that the lock has. For immediate reject, it will input a digit, and wait a small while to see if the red LED actives. If it does, then it will input all the digits it has found before hand, and then try the next digit. If it doesn't, it adds the digit it inputted to the found digits, and trys to find the next digit. If it finds that the green LED activated, then, it knows that the digit it just tried is the final one and will then output the found code. For full reject, it will input all the digits and wait to see if the red or green LED activates. If it's the red, it tries the next code, if it's the green, it will output the code it just tried and exit. In order to speed up the brute-force method, it uses some heuristics to attempt to find the code faster. On initialisation, it will read a file with a bunch of pre-defined codes that would be commonly used, and tries them first. If none match, then it will work its way through every possible code that hasn't been tried.

I use the Event lib in this project for the same reason as the [lock](https://github.com/Gorea235/Uni-PROM-Lock) project. I have also copied the logging file from the lock project into this one, and specified it as a lib (since I needed it for the same thing).

# Build and Test
Due to the simplicity and time contraints, we skiped the unit testing that the main lock system had. Instead, we just using the build script to compile the source code to a folder ready for pushing to the Pi.
