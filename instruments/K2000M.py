#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 19:40:35 2018

@author: Vedran Furtula
"""


import sys, serial, argparse, time, re, random, visa, os
import numpy as np
import matplotlib.pyplot as plt


class K2000M:
	
	def __init__(self, my_serial, baud, eol, testmode):
		# activate the serial. CHECK the serial port name!
		self.testmode = testmode
		if self.testmode:
			print("Testmode: K2000M port opened")
			self.isopen = True
		elif not self.testmode:
			if "ASRL" in my_serial:
				rm = visa.ResourceManager()
				print("Ports: ", rm.list_resources())
				self.ser = rm.open_resource(my_serial, baud_rate = baud, read_termination = eol)
			elif "COM" in my_serial:
				rm = visa.ResourceManager()
				print("Ports: ", rm.list_resources())
				self.ser = rm.open_resource(my_serial, baud_rate = baud, read_termination = eol)
			elif "GPIB" in my_serial:
				rm = visa.ResourceManager()
				print("Ports: ", rm.list_resources())
				self.ser = rm.open_resource(my_serial)
				
			self.isopen = True
			print("K2000M serial port:", my_serial)
			time.sleep(1)
			
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
	# K2000M functions
	####################################################################
	
	def return_id(self):
		if self.testmode:
			return "Testmode: return_id K2000M"
		elif not self.testmode:
			val = self.ser.query("*idn?")
			return val
		
	def set_dc_voltage(self):
		if self.testmode:
			return "Testmode: set_dc_voltage K2000M"
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			self.ser.write(":conf:volt:dc")
			self.ser.write(":volt:dc:nplc 3")
			#self.ser.write(":volt:dc:rang:upp 15") #possibly bad resolution
			self.ser.write(":volt:dc:rang:auto once")
			time.sleep(1)
	
	def set_dc_current(self):
		if self.testmode:
			return "Testmode: set_dc_current K2001M"
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			self.ser.write(":conf:curr:dc")
			self.ser.write(":curr:dc:nplc 3")
			#self.ser.write(":curr:dc:rang:upp 15") #possibly bad resolution
			self.ser.write(":curr:dc:rang:auto once")
			time.sleep(1)

	def return_val(self,*argv):
		if self.testmode:
			if argv:
				#time.sleep(random.uniform(0,1))
				return argv[0]+random.uniform(-1,1)
			else:
				#time.sleep(random.uniform(0,1))
				return random.uniform(-1,1)
		elif not self.testmode:
			#read digitized voltage value from the analog port number (dev)
			while True:
				val = self.ser.query(":read?")
				val = val.split(',')[0]
				if self.is_number(val):
					#print("return_reffreq: ", val)
					return float(val)
				else:
					self.ser.clear()
					print("Bad value returned from K2000M (read command):", val)
					
	def is_open(self):
		return self.isopen
	
	def close(self):
		if self.testmode:
			print("Testmode: Keithley 2000M port flushed and closed")
			self.isopen=False
		elif not self.testmode:
			self.ser.clear()
			self.ser.close()
			print("Status: Keithley 2000M port flushed and closed")
			self.isopen=False



def test():
	
	# call the Keithley port
	model_K2000M = K2000M("COM5", 19200, "\r\n", False)
	print(model_K2000M.return_id())
	model_K2000M.set_dc_voltage()
	for i in range(5):
		print(model_K2000M.return_val())
	model_K2000M.close()
	

	
if __name__ == "__main__":
	
	test()


