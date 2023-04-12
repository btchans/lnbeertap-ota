from machine import Pin, PWM
from time import sleep

## servo
servo_gpio=14
servo = PWM(Pin(servo_gpio), 100)
openangle=90
closedangle=128

## led
led_gpio=13
led = PWM(Pin(led_gpio), 5000)

## button
switch_gpio=12
switch = Pin(switch_gpio, Pin.IN, Pin.PULL_UP)

def AngleToPulsewidth(angle):
    if angle > 180 or angle < 0 :
        return False
    start = 566000
    end = 2475000
    ratio = (end - start)/180
    angle_as_percent = angle * ratio
    return round(start + angle_as_percent)

def BreathLed():
    while True:
        for dutyCycle_up in range(0, 1024,2):
            led.duty(dutyCycle_up)
            sleep(0.001)
        sleep(.9)
        for dutyCycle_down in range(1023, 0,-2):
            led.duty(dutyCycle_down)
            sleep(0.001)
        sleep(.7)

def ToggleLed(toggle):
    if toggle:
        led.duty(1023)
    else:
        led.duty(0)

def BlinkLed(times = 3, duration = .5, pause = .3):
    for i in range(times):
        ToggleLed(True)
        sleep(duration)
        ToggleLed(False)
        sleep(pause)