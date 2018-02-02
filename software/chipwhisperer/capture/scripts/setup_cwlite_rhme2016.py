"""Setup script for CWLite/1200 with NOTDUINO (CW304) specifically parametered for
AES challengees from Riscure Hack-me 2016.
"""
import chipwhisperer as cw
from chipwhisperer.capture.targets import Rhme2016Serial


scope = cw.scope()
self.scope = scope

target = Rhme2016Serial.Rhme2016Serial()
self.target = target

scope.io.target_pwr = False

scope.gain.gain = 45
scope.gain.mode = 'low'
scope.adc.samples = 24400
scope.adc.offset = 0
scope.adc.basic_mode = "rising_edge"
scope.clock.clkgen_freq = 16000000
scope.clock.adc_src = "extclk_x4"
scope.clock.freq_ctr_src = "extclk"
scope.trigger.triggers = "tio4"
scope.io.tio1 = "serial_tx"
scope.io.tio2 = "serial_rx"
scope.io.hs2 = None

target.baud = 19200
target.challenge = "Piece of SCAke"

scope.io.target_pwr = True

try:
    self.api.capture1()
except:
    pass
#self.api.capture1()
