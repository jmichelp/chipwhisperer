"""Setup script for CWLite/1200 with NOTDUINO (CW304) specifically parametered for
AES challengees from Riscure Hack-me 2016.
"""

try:
    scope = self.scope
    target = self.target
except NameError:
    pass

scope.gain.gain = 45
scope.gain.mode = 'low'
scope.adc.samples = 5000
scope.adc.offset = 0
scope.adc.basic_mode = "rising_edge"
scope.clock.clkgen_freq = 16000000
scope.clock.adc_src = "clkgen_x4"
scope.trigger.triggers = "tio4"
scope.io.tio1 = "serial_tx"
scope.io.tio2 = "serial_rx"
scope.io.hs2 = "clkgen"

target.baud = 19200
target.challenge = "Piece of SCAke"

