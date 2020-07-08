#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import re, serial, time, datetime, numpy, random, sys, os, configparser, sqlite3

from instruments import K2000M

class Logger_K2000M:
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''	
	def __init__(self):
		# Initial read of the config file
		self.config = configparser.ConfigParser()

		self.config.read("config.ini")
		self.cwd = self.config.get("Settings","cwd")
		self.port = self.config.get("Settings","k2000mport")
		self.baud = int(self.config.get("Settings","k2000mbaud"))
		eol = self.config.get("Settings","k2000meol")
		# Replace the CR and LF characters with valid UTF-8
		self.eol = eol.replace("CR","\r").replace("LF","\n")

		self.txtfile = ''.join([self.cwd,os.sep,"logfiles",os.sep,"k2000m.txt"])
		self.dbfile = ''.join([self.cwd,os.sep,"logfiles",os.sep,"k2000m.db"])
		
		self.conn = sqlite3.connect(self.dbfile)
		self.cursor_k2000m = self.conn.cursor()
		self.cursor_k2000m.execute(''.join(["CREATE TABLE IF NOT EXISTS k2000m (sensor REAL, absolutetime TEXT, epoch REAL)"]))
		
	def run(self):
		########################################################
		while True:
			try:
				instr = K2000M.K2000M(self.port, self.baud, self.eol, False)
				print(instr.return_id())
				instr.set_dc_voltage()
			except Exception as e: # catch error and ignore it
				if hasattr(self,"instr"):
					instr.close()
				print(''.join(["Fault while reading instrument port ",self.port,":\n",str(e)]))
				time.sleep(5)
			else:
				while True:
					# Create a header in the case that files get deleted from the folder
					if not os.path.isfile(self.txtfile):
						with open(self.txtfile, 'a') as thefile:
							thefile.write("Col1: Sensor [V]")
							thefile.write("\tCol2: Absolute time (Y:M:D - H:M:S)")
							thefile.write("\tCol3: Absolute time (epoch) [sec]\n")
					
					if not os.path.isfile(self.dbfile):
						# Then create it again for new inputs
						self.conn = sqlite3.connect(self.dbfile)
						self.cursor_k2000m = self.conn.cursor()
						self.cursor_k2000m.execute(''.join(["CREATE TABLE IF NOT EXISTS k2000m (sensor REAL, absolutetime TEXT, epoch REAL)"]))
						
					try:
						try:
							# Read and store the data reading
							val = instr.return_val()
						except Exception as e:
							print(''.join(["Fault during port communication:\n",str(e)]))
							break
						
						# Read the wait_time from the config file at each data reading
						self.config.read("config.ini")
						self.wait_time = float(self.config.get("Settings","wait_time"))
						
						# save to a TXT file
						with open(self.txtfile, 'a') as thefile:
							thefile.write("%s" %format(val,"013.10f"))
							thefile.write("\t%s" %time.strftime("%Y %b %d - %H:%M:%S"))
							thefile.write("\t%s\n" %format(time.time(),"016.3f"))
						
						# save to a DB file
						self.cursor_k2000m.execute(''.join(["INSERT INTO k2000m VALUES (",str(val),",'",time.strftime("%Y %b %d - %H:%M:%S"),"',",str(time.time()),")"]))
						# Save (commit) the changes
						self.conn.commit()
						
						time.sleep(self.wait_time)
					except Exception as e:
						instr.close()
						print(''.join(["Fault during the data storage process:\n",str(e)]))
						break





def main():
	
	k2000m = Logger_K2000M()
	k2000m.run()


if __name__ == '__main__':
	
	main()
	
	
