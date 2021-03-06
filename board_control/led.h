#include <Arduino.h>
#define LED_DEBUG         false   // DEBUG = true,print message

/* use to contral the led ring */
#define  RED 				9
#define  BLUE 				8
#define  BRIGHT 			100
#define  RUNING 			66
#define  DIMING 			20
#define  OFF 				0
#define  BREATH_DELAY 		15

extern void breath(int start_value, int end_value, int led);
extern void ledBreathPowerOn();
extern void ledBreathPowerOff();


extern void breathLedSetup();

extern void powerOffLedBreathUp();

extern void powerOffLedBreathDown();