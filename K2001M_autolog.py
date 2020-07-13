#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""

import re, serial, time, datetime, numpy, random, sys, os, configparser, sqlite3

from instruments import K2001M

class Logger_K2001M:
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
		self.port = self.config.get("Settings","k2001mport")
		self.baud = int(self.config.get("Settings","k2001mbaud"))
		eol = self.config.get("Settings","k2001meol")
		# Replace the CR and LF characters with valid UTF-8
		self.eol = eol.replace("CR","\r").replace("LF","\n")
		
		if not os.path.isdir(self.cwd):
			print("The directory in the config.ini file cwd = "+self.cwd+"\nis NOT a valid directory. Trying to load data into the current workig directory!")
			self.cwd = os.getcwd()
			self.config.set("Settings","cwd", self.cwd )
			with open("config.ini", "w") as configfile:
				self.config.write(configfile)
			print("SUCCESS! The directory in the config.ini file is now updated to cwd = "+self.cwd)
			
		if not os.path.isdir(''.join([self.cwd,os.sep,"logfiles"])):
			try:
				os.makedirs(''.join([self.cwd,os.sep,"logfiles"]), exist_ok=True)
			except Exception as e:
				print(''.join(["Could not create folder ->\n",self.cwd,os.sep,"logfiles\nError message returned ->\n",str(e)]))
				raise
			else:
				print(''.join(["New folder created ->\n",self.cwd,os.sep,"logfiles"]))
				
		self.txtfile = ''.join([self.cwd,os.sep,"logfiles",os.sep,"k2001m.txt"])
		self.dbfile = ''.join([self.cwd,os.sep,"logfiles",os.sep,"k2001m.db"])
		
		self.conn = sqlite3.connect(self.dbfile)
		self.cursor_k2001m = self.conn.cursor()
		self.cursor_k2001m.execute(''.join(["CREATE TABLE IF NOT EXISTS k2001m (sensor REAL, absolutetime TEXT, epoch REAL)"]))
		
		
	def run(self):
		########################################################
		while True:
			try:
				instr = K2001M.K2001M(self.port, self.baud, self.eol, False)
				print(instr.return_id())
				instr.set_dc_current()
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
						self.cursor_k2001m = self.conn.cursor()
						self.cursor_k2001m.execute(''.join(["CREATE TABLE IF NOT EXISTS k2001m (sensor REAL, absolutetime TEXT, epoch REAL)"]))
						
					try:
						try:
							# Read and store the data reading
							val = instr.return_val()
						except Exception as e: # catch error and ignore it
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
						self.cursor_k2001m.execute(''.join(["INSERT INTO k2001m VALUES (",str(val),",'",time.strftime("%Y %b %d - %H:%M:%S"),"',",str(time.time()),")"]))
						# Save (commit) the changes
						self.conn.commit()
						
						time.sleep(self.wait_time)
					except Exception as e: # catch error and ignore it
						instr.close()
						print(''.join(["Fault during the data storage process:\n",str(e)]))
						break





def main():
	
	k2001m = Logger_K2001M()
	k2001m.run()


if __name__ == '__main__':
	
	main()
	
	
