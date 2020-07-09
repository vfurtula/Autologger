# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 19:40:35 2018

@author: Vedran Furtula
"""


import sys, serial, argparse, time, re, random, visa
import numpy as np
import matplotlib.pyplot as plt



class A34972A:
	
	def __init__(self, my_serial, testmode):
		# activate the serial. CHECK the serial port name!
		
		self.testmode = testmode
		if self.testmode:
			print("Testmode: Agilent34972A port opened")
			self.isopen = True
		elif not self.testmode:
			if "ASRL" in my_serial:
				rm = visa.ResourceManager()
				self.ser = rm.open_resource(my_serial, baud_rate = 9600, read_termination = "\n")
			elif "COM" in my_serial:
				rm = visa.ResourceManager()
				#print(rm.list_resources())
				self.ser = rm.open_resource(my_serial, baud_rate = 9600, read_termination = "\n")
			else:
				rm = visa.ResourceManager()
				self.ser = rm.open_resource(my_serial)
			
			self.isopen = True
			print("Agilent34972A port:", my_serial)
			time.sleep(1)
		#self.ser=serial.Serial(my_serial,baudrate=19200,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
		#print("Agilent 34972A serial port:", my_serial))
		#time.sleep(1)

  ############################################################
	# Check input if a number, ie. digits or fractions such as 3.141
	# Source: http://www.pythoncentral.io/how-to-check-if-a-string-is-a-number-in-python-including-unicode/
	def is_number(self,s):
		try:
			float(s)
			return True
		except ValueError:
			pass

		try:
			import unicodedata
			unicodedata.numeric(s)
			return True
		except (TypeError, ValueError):
			pass
		
		return False
	
	####################################################################
	# K2001A functions
	####################################################################
	
	def return_id(self):
		if self.testmode:
			return "Testmode: return_id Agilent 34972A"
		elif not self.testmode:
			val = self.ser.query("*idn?")
			return val
	
	
	def set_dc_voltage(self):
		if self.testmode:
			return "Testmode: set_dc_voltage Agilent 34972A"
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			self.ser.write(":conf:volt[:dc]")
			time.sleep(0.5)
	
	def return_voltage(self,argv):
		if self.testmode:
			return [float(format(i+random.uniform(-0.05,0.05),"010.6f")) for i in range(len(argv))]
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			vals = []
			for i in argv:
				val = self.ser.query( ''.join(["meas:volt:dc? 1,0.003,(@",i,")"]) )
				while not self.is_number(val):
					val = self.ser.query( ''.join(["meas:volt:dc? 1,0.003,(@",i,")"]) )
					time.sleep(0.01)
				else:
					vals.extend([ float(val) ])
			return vals
			
			
	def is_open(self):
		return self.isopen
		
		
	def close(self):
		if self.testmode:
			print("Testmode: Agilent 34972A port flushed and closed")
			self.isopen=False
		elif not self.testmode:
			#self.ser.close()
			print("Status: Agilent 34972A port flushed and closed")
			self.isopen=False
		
		
def main():
  
	# call the sr510 port
	model_510 = A34972A('USB0::0x0957::0x2007::MY49017249::0::INSTR', True)
	
	print(model_510.return_id())
	
	for i in range(10):
		print(model_510.return_voltage([1,2,3]))
		time.sleep(1)
	
if __name__ == "__main__":
	
  main()
  


