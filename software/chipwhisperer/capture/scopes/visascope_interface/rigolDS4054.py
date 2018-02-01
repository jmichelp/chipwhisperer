# Authors: Jean-Michel Picod
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================
import logging
import time
from _base import VisaScope
from chipwhisperer.common.utils import util
from chipwhisperer.common.utils.parameter import setupSetParam, Parameterized
from chipwhisperer.common.utils.pluginmanager import Plugin


class VisaScopeInterface_RigolDS4054(VisaScope, Parameterized, Plugin):
    _name = "Rigol DS 4054"

    # TODO: What scales & ranges are allowed on the DS4054?
    xScales = {"500 mS":500E-3, "200 mS":200E-3, "100 mS":100E-3, "50 mS":50E-3,
               "20 mS":20E-3, "10 mS":10E-3, "5 mS":5E-3, "2 mS":2E-3, "1 mS":1E-3,
               "500 uS":500E-6, "200 uS":200E-6, "100 uS":100E-6, "50 uS":50E-6,
               "20 uS":20E-6, "10 uS":10E-6, "5 uS":5E-6, "2uS":2E-6, "1 uS":1E-6}

    yScales = {"10 V":10, "5 V":5, "2 V":2, "500 mV":500E-3, "200 mV":200E-3, "100 mV":100E-3,
               "50 mV":50E-3, "20 mV":20E-3, "10 mV":10E-3, "5 mV":5E-3}

    probeAttenuations = {'0.01':0.01, '0.02':0.02, '0.05':0.05, '0.1':0.1, '0.2':0.2, '0.5':0.5,
                         '1':1, '2':2, '5':5, '10':10, '20':20, '50':50, '100':100, '200':200,
                         '500':500, '1000':1000}

    triggerModes = {'Edge':'EDGE', 'Pulse':'PULS', 'Runt':'RUNT', 'Num. Edges':'NEDG', 'Slope':'SLOP',
                    'Video':'VID', 'Pattern':'PATT', 'RS-232':'RS232', 'I2C':'IIC', 'SPI':'SPI',
                    'CAN':'CAN', 'Flexray':'FLEX', 'USB':'USB'}

    triggerSources = {'CHAN1':'CHAN1', 'CHAN2':'CHAN2', 'CHAN3':'CHAN3', 'CHAN4':'CHAN4',
                      'EXT':'EXT', 'EXT5':'EXT5', 'ACL':'ACL'}

    header = [  ":CHANnel1:PROBe 1",
                ":CHANnel1:DISPlay ON",
                ":CHANnel1:COUPling DC",
                ":CHANnel2:PROBe 1",
                ":CHANnel2:SCALe 1",
                ":CHANnel2:OFFSet 0",
                ":CHANnel2:DISPLay ON",
                ":TRIGger:COUPling DC",
                ":TRIGger:MODE EDGE",
                ":TRIGger:EDGE:SOURce CHANnel2",
                ":TRIGger:EDGE:SLOPe NEGative",
                ":TRIGger:EDGE:LEVel 2.0",
                ":TRIGger:NREJect ON",
                ":TRIGger:SWEep NORMal",
                ":WAVeform:SOURce CHANnel1",
                ":WAVeform:FORMat WORD",
                ":WAVeform:MODE NORMal",
                ]


    def __init__(self):
        VisaScope.__init__(self)
        channels = {}
        for i in range(1, 5):
          channels['CHAN{}'.format(i)] = i
        self.getParams().addChildren([
            {'name':'Trace Measurement', 'key': 'trace', 'type':'group', 'children':[
                {'name':'Source', 'key':'tracesource', 'type':'list', 'values':channels, 'value':1, 'action':self.updateCurrentSettings},
                {'name':'Probe Att.', 'key':'traceprobe', 'type':'list', 'values':self.probeAttenuations, 'value':1, 'action':self.updateCurrentSettings},
                {'name':'Coupling', 'key':'tracecouple', 'type':'list', 'values':{'AC':'AC', 'DC':'DC', 'GND':'GND'}, 'value':'DC', 'action':self.updateCurrentSettings},
                {'name':'BW Limit.', 'key':'tracebandwidth', 'type':'list', 'values':{'20M':'20M', '100M':'100M', 'OFF':'OFF'}, 'value':'OFF', 'action':self.updateCurrentSettings},
                {'name':'Impedance', 'key':'traceimpedance', 'type':'list', 'values':{'1M':'OMEG', '50R':'FIFTy'}, 'value':'1M', 'action':self.updateCurrentSettings},
            ]},
            {'name':'Trigger', 'key':'trig', 'type':'group', 'children':[
                {'name':'Source', 'key':'trigsource', 'type':'list', 'values':channels, 'value':2, 'action':self.updateCurrentSettings},
                {'name':'Probe Att.', 'key':'trigprobe', 'type':'list', 'values':self.probeAttenuations, 'value':1, 'action':self.updateCurrentSettings},
                {'name':'Coupling', 'key':'trigcouple', 'type':'list', 'values':{'AC':'AC', 'DC':'DC', 'GND':'GND'}, 'value':'DC', 'action':self.updateCurrentSettings},
                {'name':'BW Limit.', 'key':'trigbandwidth', 'type':'list', 'values':{'20M':'20M', '100M':'100M', 'OFF':'OFF'}, 'value':'OFF', 'action':self.updateCurrentSettings},
                {'name':'Impedance', 'key':'trigimpedance', 'type':'list', 'values':{'1M':'OMEG', '50R':'FIFTy'}, 'value':'1M', 'action':self.updateCurrentSettings},
            ]},
            {'name':'Acquisition', 'key':'acquisition', 'type':'list', 'values':{'Normal':'NORM', 'High-Res':'HRES'}, 'value':'Normal', 'action':self.updateCurrentSettings},
        ])

    def currentSettings(self):
        # TODO: Delete these?
        self.XScale = self.visaInst.query_values(":TIMebase:SCALe?")
        self.XScale = self.XScale[0]
        self.XOffset = self.visaInst.query_values(":TIMebase:POSition?")
        self.XOffset = self.XOffset[0]
        self.YOffset = self.visaInst.query_values(":CHANnel1:OFFSet?")
        self.YOffset = self.YOffset[0]
        self.YScale = self.visaInst.query_values(":CHANnel1:SCALe?")
        self.YScale = self.YScale[0]

    def arm(self):
        self.visaInst.write(":RUN\n")
        result = "fake"
        while (result.startswith("WAIT") == False) and (result.startswith("RUN") == False):
            result = self.visaInst.query(":TRIGger:STATus?")
            time.sleep(0.1)
            logging.info('1Waiting...')

    def capture(self):
        # Wait?
        while self.visaInst.query("*OPC?\n") != "1":
            time.sleep(0.1)
            util.updateUI()
            logging.info('2Waiting...')

        # print command
        self.visaInst.write(":WAVeform:DATA?")
        data = self.visaInst.read_raw()

        # Find '#' which is start of frame
        start = data.find('#')

        if start < 0:
            raise IOError('Error in header')

        start += 1
        hdrlen = data[start]
        hdrlen = int(hdrlen)

        # print hdrlen

        start += 1
        datalen = data[start:(start + hdrlen)]
        datalen = int(datalen)
        # print datalen

        start += hdrlen

        # Each is two bytes
        wavdata = bytearray(data[start:(start + datalen)])

        self.datapoints = []

        for j in range(0, datalen, 2):
            data = wavdata[j] | (wavdata[j + 1] << 8)

            if (data & 0x8000):
                data += -65536

            self.datapoints.append(data)

        self.dataUpdated.emit(0, self.datapoints, 0, 0)
        return False
