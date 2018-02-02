#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2014, NewAE Technology Inc
# All rights reserved.
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

from collections import OrderedDict
from usb import USBError
from Crypto.Cipher import AES

from ._base import TargetTemplate
from chipwhisperer.common.utils import pluginmanager
from simpleserial_readers.cwlite import SimpleSerial_ChipWhispererLite
from chipwhisperer.common.utils.parameter import Parameter, setupSetParam


class Rhme2016Serial(TargetTemplate):
    _name = "Rhme2016 Serial"

    def __init__(self):
        TargetTemplate.__init__(self)

        ser_cons = pluginmanager.getPluginsInDictFromPackage("chipwhisperer.capture.targets.simpleserial_readers", True, False)
        self.ser = ser_cons[SimpleSerial_ChipWhispererLite._name]

        self.keylength = 16
        self.textlength = 16
        self.outputlength = 16
        self.input = ""

        self._challenges = OrderedDict()
        self._challenges['Piece of SCAke'] = {
            'key': 'AF 23 D5 45 A0 EA E6 A0 74 65 96 CA CE 51 F0 F7',
            'trigger': True,
            'extra': [
                ['OpenADC', 'Trigger Setup', 'Total Samples', 4000],
                ['OpenADC', 'Trigger Setup', 'Offset', 4000],
            ]
        }
        self._challenges['Still not SCAry'] = {
            'key': '89 32 D0 B8 10 16 85 14 53 4B 93 BE 48 2C DF 21',
            'trigger': False,
            'extra': [
                ['OpenADC', 'Trigger Setup', 'Total Samples', 24400],
                ['OpenADC', 'Trigger Setup', 'Offset', 0],
            ]
        }
        self._challenges['eSCAlate'] = {
            'key': '1C 7B 3F 97 83 A4 72 55 DB 68 B2 D6 E1 9A 9D D2',
            'trigger': False,
            'extra': [
                ['OpenADC', 'Trigger Setup', 'Total Samples', 24400],
                ['OpenADC', 'Trigger Setup', 'Offset', 0],
            ]
        }
        self._challenge = 'Piece of SCAke'
        self._trigger = False

        self.params.addChildren([
            {'name':'Connection', 'type':'list', 'key':'con', 'values':ser_cons, 'get':self.getConnection, 'set':self.setConnection},
            {'name':'Key Length (Bytes)', 'type':'list', 'values':[8, 16, 32], 'get':self.keyLen, 'set':self.setKeyLen},
            {'name':'Input Length (Bytes)', 'type':'list', 'values':[1, 2, 4, 8, 16, 32], 'default':16, 'get':self.textLen, 'set':self.setTextLen},
            {'name':'Output Length (Bytes)', 'type':'list', 'values':[8, 16, 32], 'default':16, 'get':self.outputLen, 'set':self.setOutputLen},
            {'name':'Load Key Command', 'key':'cmdkey', 'type':'str', 'value':'k$KEY$\\n'},
            {'name':'Load Input Command', 'key':'cmdinput', 'type':'str', 'value':''},
            {'name':'Go Command','key':'cmdgo', 'type':'str', 'value':'e$TEXT$'},
            {'name':'Output Format', 'key':'cmdout', 'type':'str', 'value':'$RESPONSE$'},
            {'name':'Challenge', 'key':'challenge', 'type':'list', 'values':self._challenges.keys(), 'get':self.getChallenge, 'set':self.setChallenge},
        ])

        self.setConnection(self.ser, blockSignal=True)

    @setupSetParam("Challenge")
    def setChallenge(self, challenge):
        self._challenge = challenge
        self.updateChallengeParams()

    def getChallenge(self):
        return self._challenge

    def updateChallengeParams(self):
        try:
            settings = self._challenges[self._challenge]
            self._trigger = settings['trigger']
            if self._trigger:
                Parameter.setParameter(['CW Extra Settings', 'Trigger Pins', 'Target IO4 (Trigger Line)', True])
                Parameter.setParameter(['CW Extra Settings', 'Target IOn GPIO Mode', 'Target IO4: GPIO', 'Disabled'])
                Parameter.setParameter(['CW Extra Settings', 'Target IOn Pins', 'Target IO4', 'High-Z'])
            else:
                Parameter.setParameter(['CW Extra Settings', 'Target IOn Pins', 'Target IO4', 'GPIO'])
                Parameter.setParameter(['CW Extra Settings', 'Target IOn GPIO Mode', 'Target IO4: GPIO', 'Low'])
            ## Apply settings
            Parameter.setParameter(['Generic Settings', 'Basic', 'Key', 'Fixed'])
            Parameter.setParameter(['Generic Settings', 'Basic', 'Fixed Encryption Key', settings['key']])
            if 'extra' in settings:
                for p in settings['extra']:
                    Parameter.setParameter(p)
        except:
            pass

    @setupSetParam("Key Length")
    def setKeyLen(self, klen):
        """ Set key length in bytes """
        self.keylength = klen

    def keyLen(self):
        """ Return key length in bytes """
        return self.keylength

    @setupSetParam("Input Length")
    def setTextLen(self, tlen):
        """ Set plaintext length. tlen given in bytes """
        self.textlength = tlen

    def textLen(self):
        """ Return plaintext length in bytes """
        return self.textlength

    @setupSetParam("Output Length")
    def setOutputLen(self, tlen):
        """ Set plaintext length in bytes """
        self.outputlength = tlen

    def outputLen(self):
        """ Return output length in bytes """
        return self.outputlength

    def getConnection(self):
        return self.ser

    @setupSetParam("Connection")
    def setConnection(self, con):
        self.ser = con
        self.params.append(self.ser.getParams())

        self.ser.connectStatus.setValue(False)
        self.ser.connectStatus.connect(self.connectStatus.emit)
        self.ser.selectionChanged()

    def _con(self, scope = None):
        if not scope or not hasattr(scope, "qtadc"): Warning("You need a scope with OpenADC connected to use this Target")

        self.outstanding_ack = False

        self.ser.con(scope)
        #self.ser.write("x")
        self.ser.flush()

    def close(self):
        if self.ser != None:
            self.ser.close()

    def init(self):
        self.ser.flush()
        self.outstanding_ack = False
        self.updateChallengeParams()

    def setModeEncrypt(self):
      self.findParam('cmdgo').setValue('e$TEXT$')

    def setModeDecrypt(self):
      self.findParam('cmdgo').setValue('d$TEXT$')

    def convertVarToString(self, var):
        if isinstance(var, str):
            return var

        sep = ""
        s = sep.join(["%02x"%b for b in var])
        return s

    def runCommand(self, cmdstr, flushInputBefore=True):
        if self.connectStatus.value()==False:
            raise Warning("Can't write to the target while disconected. Connect to it first.")

        if cmdstr is None or len(cmdstr) == 0:
            return

        varList = [("$KEY$",self.key, "Hex Encryption Key"),
                   ("$TEXT$",self.input, "Input Plaintext"),
                   ("$EXPECTED$", self.getExpected(), "Expected Ciphertext")]

        newstr = cmdstr

        #Find variables to insert
        for v in varList:
            if v[1] is not None:
                newstr = newstr.replace(v[0], self.convertVarToString(v[1]).decode('hex'))

        #This is dumb
        newstr = newstr.replace("\\n", "\n")
        newstr = newstr.replace("\\r", "\r")

        #print newstr
        try:
            if flushInputBefore:
                self.ser.flushInput()
            if self._trigger:
                self.ser.write(newstr)
            else:
                self.ser.write(newstr[:-1])
                Parameter.setParameter(['CW Extra Settings', 'Target IOn GPIO Mode', 'Target IO4: GPIO', 'High'])
                self.ser.write(newstr[-1])
        except USBError:
            self.dis()
            raise Warning("Error in the target. It may have been disconnected.")
        except Exception as e:
            self.dis()
            raise e

    def loadEncryptionKey(self, key):
        self.key = key
        #if self.key:
        #    self.runCommand(self.findParam('cmdkey').getValue())

    def loadInput(self, inputtext):
        self.input = inputtext
        #self.runCommand(self.findParam('cmdinput').getValue())

    def isDone(self):
        return True

    def readOutput(self):
        dataLen = self.outputlength

        fmt = self.findParam('cmdout').getValue()
        #This is dumb
        fmt = fmt.replace("\\n", "\n")
        fmt = fmt.replace("\\r", "\r")

        if len(fmt) == 0:
            return None

        if fmt.startswith("$GLITCH$"):

            try:
                databytes = int(fmt.replace("$GLITCH$",""))
            except ValueError:
                databytes = 64


            self.newInputData.emit(self.ser.read(databytes))
            return None

        dataLen += len(fmt.replace("$RESPONSE$", ""))
        expected = fmt.split("$RESPONSE$")

        #Read data from serial port
        response = self.ser.read(self.outputlength, timeout=500)
        if not self._trigger:
            Parameter.setParameter(['CW Extra Settings', 'Target IOn GPIO Mode', 'Target IO4: GPIO', 'Low'])

        if len(response) < dataLen:
            logging.warning('Response length from target shorter than expected (%d<%d): "%s".' % (len(response), dataLen, response))
            return None

        #Go through...skipping expected if applicable
        #Check expected first

        #Is a beginning part
        if len(expected[0]) > 0:
            if response[0:len(expected[0])] != expected[0]:
                print("Sync Error: %s"%response)
                print("Hex Version: %s" % (" ".join(["%02x" % ord(t) for t in response])))

                return None

        startindx = len(expected[0])

        #Is middle part?
        data = bytearray(self.outputlength)
        if len(expected) == 2:
            for i in range(0, self.outputlength):
                data[i] = ord(response[i + startindx])

            startindx += self.outputlength

        #Is end part?
        if len(expected[1]) > 0:
            if response[startindx:startindx+len(expected[1])] != expected[1]:
                print("Sync Error: %s"%response)
                return None

        return data

    def go(self):
        self.runCommand(self.findParam('cmdgo').getValue())

    def checkEncryptionKey(self, kin):
        blen = self.keyLen()

        if len(kin) < blen:
            logging.warning('Padding key...')
            newkey = bytearray(kin)
            newkey += bytearray([0]*(blen - len(kin)))
            return newkey
        elif len(kin) > blen:
            logging.warning('Truncating key...')
            return kin[0:blen]

        return kin

    def checkPlaintext(self, text):
        blen = self.textLen()

        if len(text) < blen:
            logging.warning('Padding plaintext...')
            newtext = bytearray(text)
            newtext += bytearray([0] * (blen - len(text)))
            return newtext
        elif len(text) > blen:
            logging.warning('Truncating plaintext...')
            return text[0:blen]
        return text

    def getExpected(self):
        serialCmd = self.findParam('cmdgo').getValue()
        if serialCmd.startswith('e'):
            return bytearray(AES.new(str(self.key)).encrypt(str(self.input)))
        if serialCmd.startswith('d'):
            return bytearray(AES.new(str(self.key)).decrypt(str(self.input)))
        return None

    @property
    def key_len(self):
        """The length of the key (in bytes)"""
        return self.keyLen()

    @key_len.setter
    def key_len(self, length):
        self.setKeyLen(length)

    @property
    def input_len(self):
        """The length of the input to the crypto algorithm (in bytes)"""
        return self.textLen()

    @input_len.setter
    def input_len(self, length):
        self.setTextLen(length)

    @property
    def output_len(self):
        """The length of the output expected from the crypto algorithm (in bytes)"""
        return self.textLen()

    @output_len.setter
    def output_len(self, length):
        return self.setOutputLen(length)

    @property
    def key_cmd(self):
        """The command used to send the key to the target.

        See init_cmd for details about special strings.

        Getter: Return the current key command

        Setter: Set a new key command
        """
        return self.findParam("Load Key Command").getValue()

    @key_cmd.setter
    def key_cmd(self, cmd):
        self.findParam("Load Key Command").setValue(cmd)

    @property
    def input_cmd(self):
        """The command used to send the text input to the target.

        See init_cmd for details about special strings.

        Getter: Return the current text input command

        Setter: Set a new text input command
        """
        return self.findParam("Load Input Command").getValue()

    @input_cmd.setter
    def input_cmd(self, cmd):
        self.findParam("Load Input Command").setValue(cmd)

    @property
    def go_cmd(self):
        """The command used to tell the target to start the operation.

        See init_cmd for details about special strings.

        Getter: Return the current text input command

        Setter: Set a new text input command
        """
        return self.findParam("Go Command").getValue()

    @go_cmd.setter
    def go_cmd(self, cmd):
        self.findParam("Go Command").setValue(cmd)

    @property
    def output_cmd(self):
        """The expected format of the output string.

        The output received from the target is compared to this string after
        capturing a trace. If the format doesn't match, an error is logged.

        This format string can contain two special strings:
        - "$RESPONSE$": If the format contains $RESPONSE$, then this part of
          the received text is converted to the output text (ciphertext or
          similar). The length of this response string is given in outputLen()
          and set by setOutputLen().
        - "$GLITCH$": If the format starts with $GLITCH$, then all output is
          redirected to the glitch explorer.

        Getter: Return the current output format

        Setter: Set a new output format
        """
        return self.findParam("Output Format").getValue()

    @output_cmd.setter
    def output_cmd(self, cmd):
        self.findParam("Output Format").setValue(cmd)

    @property
    def challenge(self):
        return self.getChallenge()

    @challenge.setter
    def challenge(self, chal):
        self.setChallenge(chal)

    @property
    def baud(self):
        """The current baud rate of the serial connection.

        This property is only compatible with the ChipWhisperer-Lite serial
        connection - using it with a different connection raises an
        AttributeError.

        Getter: Return the current baud rate.

        Setter: Set a new baud rate. Valid baud rates are any integer in the
                range [500, 2000000].
        """
        if isinstance(self.ser, SimpleSerial_ChipWhispererLite):
            return self.ser.baud()
        else:
            raise AttributeError("Can't access baud rate unless using CW-Lite serial port")

    @baud.setter
    def baud(self, new_baud):
        if isinstance(self.ser, SimpleSerial_ChipWhispererLite):
            self.ser.setBaud(new_baud)
        else:
            raise AttributeError("Can't access baud rate unless using CW-Lite serial port")

    def _dict_repr(self):
        d = OrderedDict()
        d['key_len'] = self.key_len
        d['input_len'] = self.input_len
        d['output_len'] = self.output_len

        d['key_cmd']  = self.key_cmd
        d['input_cmd']   = self.input_cmd
        d['go_cmd']   = self.go_cmd
        d['output_cmd'] = self.output_cmd

        d['challenge'] = self.challenge

        d['baud']     = self.baud
        return d

