import time
import busio
import board

PCA9685_ADDRESS = 0x40
MODE1 = 0x00
MODE2 = 0x01
SUBADR1 = 0x02
SUBADR2 = 0x03
SUBADR3 = 0x04
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD
STP_CHA_L = 2047
STP_CHA_H = 4095
STP_CHB_L = 1
STP_CHB_H = 2047
STP_CHC_L = 1023
STP_CHC_H = 3071
STP_CHD_L = 3071
STP_CHD_H = 1023
BYG_CHA_L = 3071
BYG_CHA_H = 1023
BYG_CHB_L = 1023
BYG_CHB_H = 3071
BYG_CHC_L = 4095
BYG_CHC_H = 2047
BYG_CHD_L = 2047
BYG_CHD_H = 4095

Stepper = {}
Stepper["Ste1"] = 1
Stepper["Ste2"] = 2

Servos = {}
Servos["S1"] = 0x08
Servos["S2"] = 0x07
Servos["S3"] = 0x06
Servos["S4"] = 0x05
Servos["S5"] = 0x04
Servos["S6"] = 0x03
Servos["S7"] = 0x02
Servos["S8"] = 0x01
    
Motors = {}
Motors["M1"] = 0x1
Motors["M2"] = 0x2
Motors["M3"] = 0x3
Motors["M4"] = 0x4
    
Dir = {}
Dir["CW"] = 1
Dir["CCW"] = -1

Steppers = {}
Steppers["M1_M2"] = 0x1
Steppers["M3_M4"] = 0x2

initialized = False

i2c = busio.I2C(board.P19, board.P20)

def i2cWrite(addr, reg, value):
    try:
        i2c.try_lock()
        i2c.writeto(addr, bytes([reg, value]))
        i2c.unlock()
    except:
       print("DF0548 non détecté")

def i2cCmd(addr: number, value: number):
    try:
        i2c.try_lock()
        i2c.writeto(addr, bytes([value]))
        i2c.unlock()
    except:
        print("DF0548 non détecté")


def i2cRead(addr, reg):
    try:
        i2c.try_lock()
        i2c.writeto(addr, bytes([reg]))
        result = bytearray(1)
        i2c.readfrom_into(addr, result)
        i2c.unlock()
        return result[0]
    except:
        print("DF0548 non détecté")
        return 0

def initPCA9685():
    i2cWrite(PCA9685_ADDRESS, MODE1, 0x00)
    setFreq(50)
    initialized = True

def setFreq(freq):
    prescaleval = 25000000
    prescaleval /= 4096
    prescaleval /= freq
    prescaleval -= 1
    prescale = prescaleval
    oldmode = i2cRead(PCA9685_ADDRESS, MODE1)
    newmode = (oldmode & 0x7F) | 0x10
    i2cWrite(PCA9685_ADDRESS, MODE1, newmode)
    i2cWrite(PCA9685_ADDRESS, PRESCALE, int(prescale))
    i2cWrite(PCA9685_ADDRESS, MODE1, oldmode)
    time.sleep(0.01)
    i2cWrite(PCA9685_ADDRESS, MODE1, oldmode | 0xa1)


def setPwm(channel, on, off):
    if channel < 0 or channel > 15:
        return
    try:
        i2c.try_lock()
        i2c.writeto(PCA9685_ADDRESS, bytes([LED0_ON_L + 4 * channel, on & 0xff, (on >> 8) & 0xff, off & 0xff, (off >> 8) & 0xff]))
        i2c.unlock()
    except:
        print("DF0548 non détecté")


def setStepper_28(index, dir):
    if index == 1:
        if dir:
            setPwm(4, STP_CHA_L, STP_CHA_H)
            setPwm(6, STP_CHB_L, STP_CHB_H)
            setPwm(5, STP_CHC_L, STP_CHC_H)
            setPwm(7, STP_CHD_L, STP_CHD_H)
        else:
            setPwm(7, STP_CHA_L, STP_CHA_H)
            setPwm(5, STP_CHB_L, STP_CHB_H)
            setPwm(6, STP_CHC_L, STP_CHC_H)
            setPwm(4, STP_CHD_L, STP_CHD_H)
    else:
        if dir:
            setPwm(0, STP_CHA_L, STP_CHA_H)
            setPwm(2, STP_CHB_L, STP_CHB_H)
            setPwm(1, STP_CHC_L, STP_CHC_H)
            setPwm(3, STP_CHD_L, STP_CHD_H)
        else:
            setPwm(3, STP_CHA_L, STP_CHA_H)
            setPwm(1, STP_CHB_L, STP_CHB_H)
            setPwm(2, STP_CHC_L, STP_CHC_H)
            setPwm(0, STP_CHD_L, STP_CHD_H)



def setStepper_42(index, dir):
    if index == 1:
        if dir:
            setPwm(7, BYG_CHA_L, BYG_CHA_H)
            setPwm(6, BYG_CHB_L, BYG_CHB_H)
            setPwm(5, BYG_CHC_L, BYG_CHC_H)
            setPwm(4, BYG_CHD_L, BYG_CHD_H)
        else:
            setPwm(7, BYG_CHC_L, BYG_CHC_H)
            setPwm(6, BYG_CHD_L, BYG_CHD_H)
            setPwm(5, BYG_CHA_L, BYG_CHA_H)
            setPwm(4, BYG_CHB_L, BYG_CHB_H)
        
    else:
        if dir:
            setPwm(3, BYG_CHA_L, BYG_CHA_H)
            setPwm(2, BYG_CHB_L, BYG_CHB_H)
            setPwm(1, BYG_CHC_L, BYG_CHC_H)
            setPwm(0, BYG_CHD_L, BYG_CHD_H)
        else:
            setPwm(3, BYG_CHC_L, BYG_CHC_H)
            setPwm(2, BYG_CHD_L, BYG_CHD_H)
            setPwm(1, BYG_CHA_L, BYG_CHA_H)
            setPwm(0, BYG_CHB_L, BYG_CHB_H)        
    

def servo(index, degree):
    if not initialized:
        initPCA9685()

    v_us = (degree * 1800 / 180 + 600)
    value = v_us * 4096 / 20000
    setPwm(index + 7, 0, int(value))

def motorRun(index, direction, speed):
    if not initialized:
        initPCA9685()

    speed = speed * 16 * direction
    if speed >= 4096:
        speed = 4095
    
    if speed <= -4096:
        speed = -4095
    
    if index > 4 or index <= 0:
        return

    pn = (4 - index) * 2
    pp = (4 - index) * 2 + 1

    if speed >= 0:
        setPwm(pp, 0, speed)
        setPwm(pn, 0, 0)
    else:
        setPwm(pp, 0, 0)
        setPwm(pn, 0, -speed)


def stepperDegree_42(index, direction, degree):
    if not initialized:
        initPCA9685()
    
    setStepper_42(index, direction > 0)
    if degree == 0:
        return

    Degree = abs(degree)
    time.sleep(((50000 * Degree) / (360 * 100))/1000)
    if index == 1:
        motorStop(1)
        motorStop(2)
    else:
        motorStop(3)
        motorStop(4)

def stepperTurn_42(index, direction, turn):
    if turn == 0:
        return
    
    degree = turn * 360
    stepperDegree_42(index, direction, degree)

def stepperDegree_28(index, direction, degree):
        if not initialized:
            initPCA9685()
        
        if degree == 0:
            return
        
        Degree = abs(degree)
        Degree = Degree * direction
    
        setStepper_28(index, Degree > 0)
        Degree = abs(Degree)
        time.sleep(((1000 * Degree) / 360)/1000)
        if index == 1:
            motorStop(1)
            motorStop(2)
        else:
            motorStop(3)
            motorStop(4)

def stepperTurn_28(index, direction, turn):
    if turn == 0:
        return
    
    degree = turn * 360
    stepperDegree_28(index, direction, degree)

def stepperDegreeDual_42(stepper, direction1, degree1, direction2, degree2):
    if not initialized:
        initPCA9685()
    
    timeout1 = 0
    timeout2 = 0
    Degree1 = abs(degree1)
    Degree2 = abs(degree2)

    if stepper == 1:
        if Degree1 == 0 and Degree2 == 0:
            setStepper_42(0x01, direction1 > 0)
            setStepper_42(0x02, direction2 > 0)
        elif (Degree1 == 0) and (Degree2 > 0):
            timeout1 = (50000 * Degree2) / (360 * 100)
            setStepper_42(0x01, direction1 > 0)
            setStepper_42(0x02, direction2 > 0)
            time.sleep(timeout1/1000)
            motorStop(3)
            motorStop(4)
        elif (Degree2 == 0) and (Degree1 > 0):
            timeout1 = (50000 * Degree1) / (360 * 100)
            setStepper_42(0x01, direction1 > 0)
            setStepper_42(0x02, direction2 > 0)
            time.sleep(timeout1)
            motorStop(1)
            motorStop(2)
        elif Degree2 > Degree1:
            timeout1 = (50000 * Degree1) / (360 * 100)
            timeout2 = (50000 * (Degree2 - Degree1)) / (360 * 100)
            setStepper_42(0x01, direction1 > 0)
            setStepper_42(0x02, direction2 > 0)
            time.sleep(timeout1/1000)
            motorStop(1)
            motorStop(2)
            time.sleep(timeout2/1000)
            motorStop(3)
            motorStop(4)
        elif Degree2 <= Degree1:
            timeout1 = (50000 * Degree2) / (360 * 100)
            timeout2 = (50000 * (Degree1 - Degree2)) / (360 * 100)
            setStepper_42(0x01, direction1 > 0)
            setStepper_42(0x02, direction2 > 0)
            time.sleep(timeout1/1000)
            motorStop(3) 
            motorStop(4)
            time.sleep(timeout2/1000)
            motorStop(1) 
            motorStop(2)
    elif stepper == 2:
        if (Degree1 == 0) and (Degree2 == 0):
            setStepper_28(0x01, direction1 > 0)
            setStepper_28(0x02, direction2 > 0)
        elif (Degree1 == 0) and (Degree2 > 0):
            timeout1 = (50000 * Degree2) / (360 * 100)
            setStepper_28(0x01, direction1 > 0)
            setStepper_28(0x02, direction2 > 0)
            time.sleep(timeout1/1000)
            motorStop(3)
            motorStop(4)
        elif (Degree2 == 0) and (Degree1 > 0):
            timeout1 = (50000 * Degree1) / (360 * 100)
            setStepper_28(0x01, direction1 > 0)
            setStepper_28(0x02, direction2 > 0)
            time.sleep(timeout1/1000)
            motorStop(1)
            motorStop(2)
        elif Degree2 > Degree1:
            timeout1 = (50000 * Degree1) / (360 * 100)
            timeout2 = (50000 * (Degree2 - Degree1)) / (360 * 100)
            setStepper_28(0x01, direction1 > 0)
            setStepper_28(0x02, direction2 > 0)
            time.sleep(timeout1/1000)
            motorStop(1)
            motorStop(2)
            time.sleep(timeout2/1000)
            motorStop(3)
            motorStop(4)
        elif (Degree2 <= Degree1):
            timeout1 = (50000 * Degree2) / (360 * 100)
            timeout2 = (50000 * (Degree1 - Degree2)) / (360 * 100)
            setStepper_28(0x01, direction1 > 0)
            setStepper_28(0x02, direction2 > 0)
            time.sleep(timeout1/1000)
            motorStop(3)
            motorStop(4)
            time.sleep(timeout2/1000)
            motorStop(1)
            motorStop(2)

def stepperTurnDual_42(stepper, direction1, trun1, direction2, trun2):
    if (trun1 == 0) and (trun2 == 0):
        return

    degree1 = trun1 * 360
    degree2 = trun2 * 360

    if stepper == 1:
        stepperDegreeDual_42(stepper, direction1, degree1, direction2, degree2)
    elif stepper == 2:
        stepperDegreeDual_42(stepper, direction1, degree1, direction2, degree2)


def motorStop(index):
    setPwm((4 - index) * 2, 0, 0)
    setPwm((4 - index) * 2 + 1, 0, 0)


def motorStopAll():
    for idx in range(4):
        motorStop(idx+1)

def version():
    return "1.0.0"
