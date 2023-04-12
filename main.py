import time
import gpio
import network
import _thread
from json import config
json = config("config/config.json")
## this is a ugit-test

## close servo
gpio.servo.duty_ns(gpio.AngleToPulsewidth(gpio.closedangle))
## turn off led
gpio.ToggleLed(False)

## check if gpio.switch is pressed at start
## config_mode when button is pressed upon boot
start_time = None
button_time = None
config_mode = False

if gpio.switch.value() == 0:
    print("Button is pressed upon boot")
    start_time = time.time()
    while gpio.switch.value() == 0:
        pass
    button_time = time.time() - start_time
    
    if button_time < 5:
        print("starting config mode")
        config_mode=True

    if button_time > 5:
        print("reset beercount")
        json.WriteValue("beercount", 1)
        gpio.BlinkLed(10,.25,.25)
        time.sleep(2)

def CalculateTapDuration(count):
    duration_full = float(json.GetContent('durationfull'))
    duration_empty = float(json.GetContent('durationempty'))
    liter_per_beer = float(json.GetContent('literperbeer'))
    beer_per_keg = round(6 * (1/liter_per_beer))
    if count >= beer_per_keg:
        count = beer_per_keg
    if count <= 0:
        count = 1
    tap_duration = duration_full + ((count-1) * (duration_empty-duration_full)/(beer_per_keg-1))
    tap_duration = round(tap_duration, 3)
    return tap_duration

overall_tap_duration = 30
overall_tap_duration_expired = False
def OverallTapDuration():
    global overall_tap_duration_expired
    time.sleep(overall_tap_duration)
    overall_tap_duration_expired = True
    _thread.exit()

while not config_mode:
    import uwebsockets_client
    import ure as re
    from ucollections import namedtuple
    
    ## connect to wifi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    ssid = json.GetContent("ssid")
    pwd = json.GetContent("pwd")
    # might already be connected somehow.
    if wlan.isconnected() == False:
        wlan.connect(ssid, pwd)

    # Wait for connection.
    while not wlan.isconnected():
        print("waiting to connect to wifi")
        gpio.BlinkLed(1, .75, .75)
        pass

    lnurldevicestring = json.GetContent("lnurldevicestring").replace("ws://","wss://")
    if json.GetContent("manualtapping") == "True":
        manual_tapping = True
    else:
        manual_tapping = False

    websocket = uwebsockets_client.connect(lnurldevicestring)
    ## stay in  tapping mode
    while wlan.isconnected():
        try:
            recv_msg = websocket.recv()
        except:
            break

        # if message none reconnect to websocket
        if recv_msg is None:
            break
        else:
            msg_re = re.compile(r'(\d+?)-(\d+)')
            match = msg_re.match(recv_msg)
            if match:
                ## not necessary 
                # msg = namedtuple('MSG', ('gpio', 'duration'))
                # msg = msg(match.group(1), match.group(2))
                print("Payment received!")
                actual_count=int(json.GetContent("beercount"))
                tap_duration = CalculateTapDuration(actual_count)
                overall_tap_duration_expired = False
                print("ready to tap beer no. %s is tapped with a duration of: %s" % (str(actual_count), str(tap_duration)))
                
                ## ready to tap! (gpio.ToggleLed on)
                while gpio.switch.value() == 1:
                    gpio.ToggleLed(True)
                
                if manual_tapping:
                    start_timer = False
                    overall_tap_duration_expired = False
                    button_start_time = 0
                    button_duration_time = 0
                    previous_button_duration_time = 0
                    _thread.start_new_thread(OverallTapDuration, ())
                    while not overall_tap_duration_expired and button_duration_time <= (tap_duration*1000):
                        while gpio.switch.value() == 0:
                            if not start_timer:
                                button_start_time = time.ticks_ms()
                                start_timer = True
                            gpio.servo.duty_ns(gpio.AngleToPulsewidth(gpio.openangle))
                            gpio.ToggleLed(False)
                            button_duration_time = previous_button_duration_time + (time.ticks_ms() - button_start_time)
                            if button_duration_time >= (tap_duration*1000):
                                break
                        start_timer = False
                        gpio.ToggleLed(True)
                        previous_button_duration_time = button_duration_time
                        gpio.servo.duty_ns(gpio.AngleToPulsewidth(gpio.closedangle))
                else:
                    gpio.servo.duty_ns(gpio.AngleToPulsewidth(gpio.openangle))
                    while True:
                        time.sleep(tap_duration)
                        break
                    gpio.servo.duty_ns(gpio.AngleToPulsewidth(gpio.closedangle))

                gpio.ToggleLed(False)
                json.WriteValue("beercount", actual_count+1)  # increase Beercount
                print("done tapping beer no. %s\n" % str(actual_count))
                gpio.ToggleLed(False)


## CONFIG AP MODE
if config_mode:
    from microdot import Microdot, send_file
    from microdot_websocket import with_websocket
    app = Microdot()
    import usocket as socket
    import gc
    gc.collect()

    ssid = 'BeertAP'
    password = '21Beertap'
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, authmode=network.AUTH_WPA_WPA2_PSK, password=password)

    while ap.active() == False:
        pass

    print('Connection successful')
    print(ap.ifconfig())

    ## Set Servo Open manually
    from machine import Pin
    counter = 0
    intTime = 0
    debTime = 200 # in ms

    def ButtonCounter(p):
        global intTime
        global counter
        if time.ticks_diff(time.ticks_ms(), intTime) > debTime:
            print(p.value())
            counter = counter+1
            print("Button pressed " + str(counter) + " times")
            intTime = time.ticks_ms()

    gpio.switch.irq(trigger=Pin.IRQ_FALLING, handler=ButtonCounter)

    def SetServo():
        global counter
        while True:
            time.sleep(.02)
            if counter >= 1:
                time.sleep(.8)
                if counter == 3:
                    print("OpenServo")
                    gpio.servo.duty_ns(gpio.AngleToPulsewidth(gpio.openangle))
                counter = 0

    ## Websocket
    @app.route('/')
    def index(request):
        return send_file('config/index.html')

    @app.route('/bootstrap')
    def bootstrap(request):
        return send_file('config/bootstrap.min.css')

    @app.route('/config')
    @with_websocket
    def config(request, ws):
        ws.send(json.ReadContent())
        while True:
            receiveddata = ws.receive()
            print(receiveddata)
            if (json.IsJson(receiveddata)):
                json.WriteAllContent(receiveddata)
            if (receiveddata == "reset beercount"):
                json.WriteValue("beercount", 1)
            if (receiveddata == "Close"):
                gpio.servo.duty_ns(gpio.AngleToPulsewidth(gpio.closedangle))
            if (receiveddata == "Open"):
                gpio.servo.duty_ns(gpio.AngleToPulsewidth(gpio.openangle))

    ## Breath Led in the Background
    _thread.start_new_thread(gpio.BreathLed, ())
    ## Check if Button is pressed 3 times to open servo without ConfigWebsite
    _thread.start_new_thread(SetServo, ())   

    ## Start Servo
    app.run(host='0.0.0.0', port=80)