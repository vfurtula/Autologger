#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 09:06:01 2018

@author: Vedran Furtula
"""


import re, serial, time, numpy, random, sys, os, configparser, itertools, scipy.interpolate, datetime, sqlite3, pandas
from quantiphy import Quantity
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import pyqtgraph.exporters

from PyQt5.QtCore import QObject, QThreadPool, QTimer, QRunnable, pyqtSignal, pyqtSlot, QByteArray, Qt
from PyQt5.QtGui import QFont, QFrame, QMovie, QPixmap
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLCDNumber, QMessageBox, QGridLayout, QHeaderView,
														 QLabel, QLineEdit, QComboBox, QFrame, QTableWidget, QTableWidgetItem, QDialog,
														 QVBoxLayout, QHBoxLayout, QApplication, QMenuBar, QPushButton, QAbstractScrollArea,
														 QFileSystemModel, QTreeView, QTabWidget)






class WorkerSignals(QObject):
	# Create signals to be used
	update_k2000m = pyqtSignal()
	update_k2001m = pyqtSignal()
	update_a34972a = pyqtSignal()
	critical = pyqtSignal(object)
	finished = pyqtSignal()
		
		
		
		
		
		
class Worker_K2000M(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''	
	def __init__(self,*argv):
		super(Worker_K2000M, self).__init__()
		# constants
		self.cwd = argv[0]
		
		self.k2000m_db = ''.join([self.cwd,os.sep,"logfiles",os.sep,"k2000m.db"])
		self.abort_flag = False
		self.update_flag = True

		self.signals = WorkerSignals()
	
	def readyForUpdate(self,bool_):
		self.update_flag=bool_

	def abort(self):
		self.abort_flag=True
		
	@pyqtSlot()
	def run(self):
		########################################################
		stamp = os.stat(self.k2000m_db).st_mtime
		self.signals.update_k2000m.emit()
		while True:
			if self.abort_flag:
				break
			
			try:
				cached_stamp = os.stat(self.k2000m_db).st_mtime
			except Exception as e:
				self.signals.critical.emit(''.join(["Could not get timestamp from the file ",self.k2000m_db,"\n",str(e)]))
				time.sleep(5)
			
			if stamp != cached_stamp and self.update_flag:
				# Emit a signal that the text file has changed
				self.signals.update_k2000m.emit()
				stamp = cached_stamp
				#print("Time stamp: ", stamp)
			time.sleep(0.1)
				
		self.signals.finished.emit()
		
		
		
class Worker_K2001M(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''	
	def __init__(self,*argv):
		super(Worker_K2001M, self).__init__()
		# constants
		self.cwd = argv[0]
		
		self.k2001m_db = ''.join([self.cwd,os.sep,"logfiles",os.sep,"k2001m.db"])
		self.abort_flag = False
		self.update_flag = True

		self.signals = WorkerSignals()
	
	def readyForUpdate(self,bool_):
		self.update_flag=bool_

	def abort(self):
		self.abort_flag=True
		
	@pyqtSlot()
	def run(self):
		########################################################
		stamp = os.stat(self.k2001m_db).st_mtime
		self.signals.update_k2001m.emit()
		while True:
			if self.abort_flag:
				break
			
			try:
				cached_stamp = os.stat(self.k2001m_db).st_mtime
			except Exception as e:
				self.signals.critical.emit(''.join(["Could not get timestamp from the file ",self.k2001m_db,"\n",str(e)]))
				time.sleep(5)
			
			if stamp != cached_stamp and self.update_flag:
				# Emit a signal that the text file has changed
				self.signals.update_k2001m.emit()
				stamp = cached_stamp
			time.sleep(0.1)
				
		self.signals.finished.emit()
		
		
		
class Worker_A34972A(QRunnable):
	'''
	Worker thread
	:param args: Arguments to make available to the run code
	:param kwargs: Keywords arguments to make available to the run code
	'''	
	def __init__(self,*argv):
		super(Worker_A34972A, self).__init__()
		# constants
		self.cwd = argv[0]
		
		self.a34972a_db = ''.join([self.cwd,os.sep,"logfiles",os.sep,"a34972a.db"])
		self.abort_flag = False
		self.update_flag = True

		self.signals = WorkerSignals()

	def readyForUpdate(self,bool_):
		self.update_flag=bool_

	def abort(self):
		self.abort_flag=True
		
	@pyqtSlot()
	def run(self):
		########################################################
		stamp = os.stat(self.a34972a_db).st_mtime
		self.signals.update_a34972a.emit()
		while True:
			if self.abort_flag:
				break
			
			try:
				cached_stamp = os.stat(self.a34972a_db).st_mtime
			except Exception as e:
				self.signals.critical.emit(''.join(["Could not get timestamp from the file ",self.a34972a_db,"\n",str(e)]))
				time.sleep(5)
				
			if stamp != cached_stamp and self.update_flag:
				# Emit a signal that the text file has changed
				self.signals.update_a34972a.emit()
				stamp = cached_stamp
			time.sleep(0.1)
				
		self.signals.finished.emit()
		
		
		
		
		
		
		
		
		
		
class Run_gui(QMainWindow):
	
	
	def __init__(self):
		super().__init__()
		
		# Initial read of the config file
		self.config = configparser.ConfigParser()
		try:
			self.config.read(''.join(["config.ini"]))
			
			self.cwd = self.config.get("Settings","cwd")
			self.points = int(self.config.get("Settings","points"))
			self.wait_time = float(self.config.get("Settings","wait_time"))
			self.chnls = self.config.get("Settings","a34972achnls").split(",")
			self.datahist = self.config.get("Settings","datahist")
			
		except configparser.NoOptionError as e:
			QMessageBox.critical(self, "Message","".join(["Main FAULT while reading the config.ini file\n",str(e)]))
			raise
		
		# Setup the GUI
		self.setupUi()
		
		
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
		
		
	def setupUi(self):
		
		self.runstopButton = QPushButton("Plot data",self)
		self.runstopButton.setFixedWidth(175)
		self.clearButton = QPushButton("Clear plots",self)
		self.clearButton.setFixedWidth(175)

		cwd_lbl = QLabel("Working directory",self)
		self.cwdEdit = QLineEdit(self.cwd,self)
		self.cwdEdit.textChanged.connect(self.on_text_changed)
		#self.cwdEdit.setFixedWidth(325)
		
		##############################################
		
		schroll_lbl = QLabel("Time pts",self)
		self.combo0 = QComboBox(self)
		mylist0=["50","100","200","300","400","500"]
		self.combo0.addItems(mylist0)
		self.combo0.setCurrentIndex(mylist0.index(str(self.points)))
		
		##############################################
		
		waittime_lbl = QLabel("Wait time[s]*",self)
		self.combo1 = QComboBox(self)
		mylist1=["1.0","5.0","10.0","30.0","60.0","120.0","180.0","240.0","300.0"]
		self.combo1.addItems(mylist1)
		self.combo1.setCurrentIndex(mylist1.index(str(self.wait_time)))
		waittime_lbl2 = QLabel("* setting different Wait time parameter will change data logging frequency",self)
		waittime_lbl2.setStyleSheet("color: red")

		##############################################

		datahist_lbl = QLabel("Data history",self)
		self.combo2 = QComboBox(self)
		mylist2=["from start","last year","last month","last week","last day","last hour"]
		self.combo2.addItems(mylist2)
		self.combo2.setCurrentIndex(mylist2.index(str(self.datahist)))

		##############################################
		
		chnls_lbl = QLabel("A34972A chnls",self)
		self.chnlsEdit = QLineEdit(','.join([i for i in self.chnls]),self)
		self.chnlsEdit.textChanged.connect(self.on_text_changed)
		#self.chnlsEdit.setFixedWidth(325)
		
		##############################################
		
		# set graph  and toolbar to a new vertical group vcan
		self.win = pg.GraphicsWindow()
		self.p1 = self.win.addPlot()
		self.win.nextRow()
		
		self.p2 = self.win.addPlot()
		self.win.nextRow()
		
		self.p3 = []
		for i in range(len(self.chnls)):
			self.p3.extend([ self.win.addPlot() ])
			self.win.nextRow()
			
		##############################################
		
		self.k2000m_val = QLabel("Keithley 2000M [V]:\t\t\nsensor U -> -------",self)
		self.k2001m_val = QLabel("Keithley 2001M [A]:\t\t\nsensor I -> -------",self)
		self.a34972a_lbl = QLabel("Agilent 34972A [V]:\t\t",self)
		#self.a34972a_date = QLabel("-------",self)
		# Reduce the empty space between the sensor reading lines
		a34972a_emptylns = QLabel(''.join(["\n" for i in range(12)]),self)

		self.a34972a_vals = []
		for i in range(len(self.chnls)):
			self.a34972a_vals.extend([ QLabel("",self) ])

		self.k2000m_val.setStyleSheet("color: blue")
		self.k2001m_val.setStyleSheet("color: red")
		self.a34972a_lbl.setStyleSheet("color: black")
		#self.a34972a_date.setStyleSheet("color: black")

		##############################################

		self.helpButton = QPushButton("Canvas help",self)
		#self.helpButton.setFixedWidth(175)

		##############################################
		
		# SET ALL VERTICAL COLUMNS TOGETHER
		hbox1 = QHBoxLayout()
		hbox1.addWidget(cwd_lbl)
		hbox1.addWidget(self.cwdEdit)

		hbox2 = QHBoxLayout()
		hbox2.addWidget(chnls_lbl)
		hbox2.addWidget(self.chnlsEdit)

		hbox3 = QHBoxLayout()
		hbox3.addWidget(schroll_lbl)
		hbox3.addWidget(self.combo0)
		hbox3.addWidget(waittime_lbl)
		hbox3.addWidget(self.combo1)
		hbox3.addWidget(datahist_lbl)
		hbox3.addWidget(self.combo2)
		hbox3.addWidget(self.runstopButton)
		hbox3.addWidget(self.clearButton)
		
		vbox0 = QVBoxLayout()
		vbox0.addLayout(hbox1)
		vbox0.addLayout(hbox2)
		vbox0.addLayout(hbox3)
		vbox0.addWidget(waittime_lbl2)
		vbox0.addWidget(self.win)
		
		vbox1 = QVBoxLayout()
		vbox1.addWidget(self.helpButton)
		vbox1.addWidget(self.k2000m_val)
		vbox1.addWidget(self.k2001m_val)
		self.vbox1_1 = QVBoxLayout()
		self.vbox1_1.addWidget(self.a34972a_lbl)
		for i in range(len(self.chnls)):
			self.vbox1_1.addWidget(self.a34972a_vals[i])
		#self.vbox1_1.addWidget(self.a34972a_date)
		#self.vbox1_1.addWidget(a34972a_emptylns)
		
		vbox2 = QVBoxLayout()
		vbox2.addLayout(vbox1)
		vbox2.addLayout(self.vbox1_1)
		
		hbox0 = QHBoxLayout()
		hbox0.addLayout(vbox0)
		hbox0.addLayout(vbox2)
		
		self.threadpool = QThreadPool()
		print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
		self.isRunning=False
		
		w = QWidget()
		w.setLayout(hbox0)
		self.setCentralWidget(w)
		self.setWindowTitle("Data aqusition plotter")
		self.setGeometry(100, 100, 1200, 900)
		self.show()
		
		# Create PLOT no 1 widget here
		# create plot and add it to the figure canvas
		self.curve1=self.p1.plot(pen='b')
		self.p1.getAxis('left').setLabel("U", units="V", color='blue')
		self.p1.hideAxis("bottom")
		self.p1.enableAutoRange()
		self.p1.setDownsampling(mode='peak')
		self.p1.setClipToView(True)
		
		# Create PLOT no 2 widget here
		# create plot and add it to the figure
		self.curve2=self.p2.plot(pen='r')
		self.p2.getAxis('left').setLabel("I", units="A", color='red')
		self.p2.hideAxis("bottom")
		self.p2.enableAutoRange()
		self.p2.setDownsampling(mode='peak')
		self.p2.setClipToView(True)

		# Create PLOT no 3 widget here
		# create plot and add it to the figure canvas
		self.curves=[]
		colors = itertools.cycle(["r", "b", "g", "y", "m", "c", "w"])
		colors_ = itertools.cycle(["red", "blue", "green", "yellow", "magenta", "cyan", "white"])
		#colors = itertools.cycle([tuple(int(i) for i in numpy.array(cm.jet(i))[:-1]*255) for i in numpy.arange(20,250,len(self.guv_channels))])
		for i in range(len(self.chnls)):
			mycol = next(colors)
			mycol_ = next(colors_)
			self.curves.append(self.p3[i].plot(pen=pg.mkPen(mycol,width=1), symbol='s', symbolPen=mycol, symbolBrush=mycol, symbolSize=3))
			self.a34972a_vals[i].setText( ''.join(["sensor @",self.chnls[i][2:]," -> -------"]) )
			self.a34972a_vals[i].setStyleSheet( ''.join(["color: ",mycol_]) )
			
			# Use automatic downsampling and clipping to reduce the drawing load
			if i==len(self.chnls)-1:
				self.p3[i].getAxis('bottom').setLabel("Selected time points", units="", color='white')
				self.p3[i].getAxis('bottom').setTicks([])
			else:
				self.p3[i].hideAxis('bottom')
			self.p3[i].getAxis('left').setLabel(''.join(["@",self.chnls[i][2:]]), units="", color=mycol_)
			self.p3[i].enableAutoRange()
			self.p3[i].setDownsampling(mode='peak')
			self.p3[i].setClipToView(True)
		
		# Initialize and set titles and axis names for both plots
		self.clear_vars_graphs()
		self.combo0.activated[str].connect(self.onActivated0)
		self.combo1.activated[str].connect(self.onActivated1)
		self.combo2.activated[str].connect(self.onActivated2)
		
		# run or cancel the main script
		self.runstopButton.clicked.connect(self.runstop)
		self.helpButton.clicked.connect(self.help)
		self.clearButton.clicked.connect(self.set_clear)
		self.clearButton.setEnabled(False)
		
		
	def on_text_changed(self):
		
		self.runstopButton.setText("*Plot data*")
		#self.runstopButton.setEnabled(True)
		
	def onActivated0(self, text):
		
		self.points = int(str(text))

	def onActivated1(self, text):

		self.wait_time = float(str(text))
		self.runstopButton.setText("*Plot data*")
	
	def onActivated2(self, text):

		self.datahist = str(text)
		self.runstopButton.setText("*Plot data*")
	
	def get_last_time(self, datahist):

		if datahist=="from start":
			time_ = time.time()-time.time()
		elif datahist=="last year":
			time_ = time.time()-60*60*24*365
		elif datahist=="last month":
			time_ = time.time()-60*60*24*30
		elif datahist=="last week":
			time_ = time.time()-60*60*24*7
		elif datahist=="last day":
			time_ = time.time()-60*60*24
		elif datahist=="last hour":
			time_ = time.time()-60*60
		
		return time_ 

	def set_cancel(self):
		
		if hasattr(self,"worker_k2000m"):
			self.worker_k2000m.abort()
		if hasattr(self,"worker_k2001m"):
			self.worker_k2001m.abort()
		if hasattr(self,"worker_a34972a"):
			self.worker_a34972a.abort()
		self.clearButton.setEnabled(True)
		self.runstopButton.setText("Plot data")
		
	def set_clear(self):
		
		self.clear_vars_graphs()
		self.clearButton.setEnabled(False)
		self.clearButton.setText("Cleared")
		
		
	def clearLayout(self,layout):
		while layout.count() > 0:
			item = layout.takeAt(0)
			if not item:
				continue
			w = item.widget()
			if w:
				w.deleteLater()
					
					
	def reset_a34972a_widgets(self):
		
		# remove a34972a widgets from vbox1_1
		self.clearLayout(self.vbox1_1)
		
		for i in range(len(self.chnls)):
			self.win.removeItem(self.p3[i])
			
		# read in new channels from the text editor
		self.chnls = str(self.chnlsEdit.text()).split(',')
		
		# add new number of required plots
		self.p3 = []
		for i in range(len(self.chnls)):
			self.p3.extend([ self.win.addPlot() ])
			self.win.nextRow()
		
		# add new number of required QLabels that have been recently cleared from the layout
		self.a34972a_vals = []
		for i in range(len(self.chnls)):
			self.a34972a_vals.extend([ QLabel("",self) ])
		
		self.a34972a_lbl = QLabel("Agilent 34972A [V]:\t\t\t",self)
		self.a34972a_lbl.setStyleSheet("color: black")
		
		# now refill the a34972a widgets with the new QLabels 
		self.vbox1_1.addWidget(self.a34972a_lbl)
		for i in range(len(self.chnls)):
			self.vbox1_1.addWidget(self.a34972a_vals[i])
		
		# Recreate PLOT no 2 widget here
		# Recreate plot and add it to the figure canvas
		self.curves=[]
		colors = itertools.cycle(["r", "b", "g", "y", "m", "c", "w"])
		colors_ = itertools.cycle(["red", "blue", "green", "yellow", "magenta", "cyan", "white"])
		#colors = itertools.cycle([tuple(int(i) for i in numpy.array(cm.jet(i))[:-1]*255) for i in numpy.arange(20,250,len(self.guv_channels))])
		for i in range(len(self.chnls)):
			mycol = next(colors)
			mycol_ = next(colors_)
			self.curves.append(self.p3[i].plot(pen=pg.mkPen(mycol,width=1), symbol='s', symbolPen=mycol, symbolBrush=mycol, symbolSize=3))
			self.a34972a_vals[i].setText( ''.join(["sensor @",self.chnls[i][2:]," -> -------"]) )
			self.a34972a_vals[i].setStyleSheet( ''.join(["color: ",mycol_]) )
			
			# Use automatic downsampling and clipping to reduce the drawing load
			# Use automatic downsampling and clipping to reduce the drawing load
			if i==len(self.chnls)-1:
				self.p3[i].getAxis('bottom').setLabel("Selected time points", units="", color='white')
				self.p3[i].getAxis('bottom').setTicks([])
			else:
				self.p3[i].hideAxis('bottom')
			self.p3[i].getAxis('left').setLabel(''.join(["@",self.chnls[i][2:]]), units="", color=mycol_)
			self.p3[i].enableAutoRange()
			self.p3[i].setDownsampling(mode='peak')
			self.p3[i].setClipToView(True)
			
			
	def runstop(self):
		# Check that all channels from the string are valid
		for i in str(self.chnlsEdit.text()).split(','):
			if not i[0:2] == "at":
				QMessageBox.critical( self, 'Message', ''.join(["All A34972A channels should start with letters at"]) )
				return
			elif not self.is_number(i[2:]):
				QMessageBox.critical( self, 'Message', ''.join(["All A34972A channels should end with a three digits channel number f.ex. at112"]) )
				return
		
		# Check that the specified path exists
		self.cwd = str(self.cwdEdit.text())
		if not os.path.isdir(self.cwd):
			QMessageBox.warning( self, 'Message', ''.join(["The specified directory ->\n",self.cwd,"\nis not anywhere on this computer!"]) )
			return
		
		sender=self.sender()
		
		if sender.text() in ["Plot data","*Plot data*"]:
			if self.chnls != str(self.chnlsEdit.text()).split(','):
				self.reset_a34972a_widgets()
			# Save the current path to the config file
			if sender.text() == "*Plot data*":
				self.config.set("Settings","cwd", self.cwd )
				self.config.set("Settings","wait_time", str(self.wait_time) )
				self.config.set("Settings","datahist", self.datahist )
				self.config.set("Settings","a34972achnls", ','.join([i for i in self.chnls])  )
				with open("config.ini", "w") as configfile:
					self.config.write(configfile)
			# Run the plotter function
			self.set_run()
		elif sender.text()=="STOP plotting":
			self.set_cancel()
		
		
	def set_run(self):
		
		if not os.path.isfile(''.join([self.cwd,os.sep,"logfiles",os.sep,"k2000m.db"])):
			QMessageBox.warning( self, 'Message', ''.join(["The file -> k2000m.db\nis not found in the specified path ->\n",self.cwd,os.sep,"logfiles"]) )
		
		db = ''.join([self.cwd,os.sep,"logfiles",os.sep,"k2000m.db"])
		self.conn_k2000m = sqlite3.connect(db)
		self.cursor_k2000m = self.conn_k2000m.cursor()
		
		self.worker_k2000m = Worker_K2000M(self.cwd)
		self.worker_k2000m.signals.update_k2000m.connect(self.update_k2000m)
		self.worker_k2000m.signals.critical.connect(self.critical)
		self.worker_k2000m.signals.finished.connect(self.finished)
		# Execute
		self.threadpool.start(self.worker_k2000m)
			
		if not os.path.isfile(''.join([self.cwd,os.sep,"logfiles",os.sep,"k2001m.db"])):
			QMessageBox.warning( self, 'Message', ''.join(["The file -> k2001m.db\nis not found in the specified path ->\n",self.cwd,os.sep,"logfiles"]) )
		
		db = ''.join([self.cwd,os.sep,"logfiles",os.sep,"k2001m.db"])
		self.conn_k2001m = sqlite3.connect(db)
		self.cursor_k2001m = self.conn_k2001m.cursor()
	
		self.worker_k2001m = Worker_K2001M(self.cwd)
		self.worker_k2001m.signals.update_k2001m.connect(self.update_k2001m)
		self.worker_k2001m.signals.critical.connect(self.critical)
		self.worker_k2001m.signals.finished.connect(self.finished)
		# Execute
		self.threadpool.start(self.worker_k2001m)

		if not os.path.isfile(''.join([self.cwd,os.sep,"logfiles",os.sep,"a34972a.db"])):
			QMessageBox.warning( self, 'Message', ''.join(["The file -> a34972a.db\nis not found in the specified path ->\n",self.cwd,os.sep,"logfiles"]) )
		
		db = ''.join([self.cwd,os.sep,"logfiles",os.sep,"a34972a.db"])
		self.conn_a34972a = sqlite3.connect(db)
		self.cursor_a34972a = self.conn_a34972a.cursor()
	
		self.worker_a34972a = Worker_A34972A(self.cwd)
		self.worker_a34972a.signals.update_a34972a.connect(self.update_a34972a)
		self.worker_a34972a.signals.critical.connect(self.critical)
		self.worker_a34972a.signals.finished.connect(self.finished)
		# Execute
		self.threadpool.start(self.worker_a34972a)

		##############################################################
		
		self.runstopButton.setEnabled(True)
		self.runstopButton.setText("STOP plotting")
		
		self.clearButton.setEnabled(False)
		self.combo0.setEnabled(False)
		self.combo1.setEnabled(False)
		self.combo2.setEnabled(False)
		self.cwdEdit.setEnabled(False)
		self.chnlsEdit.setEnabled(False)
		self.isRunning=True
		
	##############################################################

	def	help(self):
		help = HelpWindow()
		help.exec()


	def critical(self,mystr):
		
		QMessageBox.critical( self, 'Message', mystr)
		
		
	def update_k2000m(self):
		# Lock the thread for further updates
		self.worker_k2000m.readyForUpdate(False)
		# READ ALL the K2000M data in order to make a plot
		time_s = time.time()
		try:
			self.cursor_k2000m.execute("SELECT sensor, absolutetime, epoch FROM k2000m "+" WHERE epoch >= "+str(self.get_last_time(self.datahist))+" ORDER BY epoch ASC")
			rows = self.cursor_k2000m.fetchall()
		except Exception as e:
			print("Fault during SQL fetching the data in the file k2000m.db ->\n",str(e))
		else:
			volt_k2000m=[]
			absdate=[]
			epoch=[]
			for i in rows:
				volt_k2000m.extend([i[0]])
				absdate.extend([i[1]])
				epoch.extend([i[2]])
					
			############################################################
			# Get indexed data points in order to reduce data points to make faster plots
			if len(volt_k2000m)>self.points:
				#INTERPOLATION method
				#fun = scipy.interpolate.interp1d(numpy.arange(len(volt_k2000m)),volt_k2000m)
				#x_new = numpy.linspace(0,len(volt_k2000m)-1,self.points)
				#volt_k2000m = fun(x_new)
				#LINSPACE method
				indcs = [int(tal) for tal in numpy.linspace(0,len(volt_k2000m)-1,self.points)]
				volt_k2000m = [volt_k2000m[i] for i in indcs]

			if len(volt_k2000m)>0:
				self.k2000m_val.setText( ''.join(["Keithley 2000M [V]:\t\nsensor U -> ",Quantity(volt_k2000m[-1],"V").render(prec=2),"\n\u0394time: ", str(datetime.timedelta(seconds=round(epoch[-1]-epoch[0])))," (",str(len(epoch)),"; ",Quantity(time.time()-time_s,"s").render(prec=2),")"]))
			self.curve1.setData(volt_k2000m)
		# Open the thread for updates
		self.worker_k2000m.readyForUpdate(True)


	def update_k2001m(self):
		# Lock the thread for further updates
		self.worker_k2001m.readyForUpdate(False)
		# READ ALL the K2001M data in order to make a plot
		time_s = time.time()
		try:
			self.cursor_k2001m.execute("SELECT sensor, absolutetime, epoch FROM k2001m "+" WHERE epoch >= "+str(self.get_last_time(self.datahist))+" ORDER BY epoch ASC")
			rows = self.cursor_k2001m.fetchall()
		except Exception as e:
			print("Fault during SQL fetching the data in the file k2001m.db ->\n",str(e))
		else:
			volt_k2001m=[]
			absdate=[]
			epoch=[]
			for i in rows:
				volt_k2001m.extend([i[0]])
				absdate.extend([i[1]])
				epoch.extend([i[2]])
					
			############################################################
			# Get indexed data points in order to reduce data points to make faster plots
			if len(volt_k2001m)>self.points:
				#INTERPOLATION method
				#fun = scipy.interpolate.interp1d(numpy.arange(len(volt_k2001m)),volt_k2001m)
				#x_new = numpy.linspace(0,len(volt_k2001m)-1,self.points)
				#volt_k2001m = fun(x_new)
				#LINSPACE method
				indcs = [int(tal) for tal in numpy.linspace(0,len(volt_k2001m)-1,self.points)]
				volt_k2001m = [volt_k2001m[i] for i in indcs]

			if len(volt_k2001m)>0:
				self.k2001m_val.setText( ''.join(["Keithley 2001M [A]:\t\nsensor I -> ",Quantity(volt_k2001m[-1],"A").render(prec=2),"\n\u0394time: ", str(datetime.timedelta(seconds=round(epoch[-1]-epoch[0])))," (",str(len(epoch)),"; ",Quantity(time.time()-time_s,"s").render(prec=2),")"]) )
			self.curve2.setData(volt_k2001m)
		# Open the thread for updates
		self.worker_k2001m.readyForUpdate(True)


	def update_a34972a(self):
		# Lock the thread for further updates
		self.worker_a34972a.readyForUpdate(False)
		# READ ALL the A34972A data in order to make a plot
		time_s = time.time()
		try:
			volt_a34972a=[]
			absdate=[]
			epoch=[]
			for chnl in self.chnls:
				df = pandas.read_sql("SELECT sensor, absolutetime, epoch FROM "+chnl+" WHERE epoch >= "+str(self.get_last_time(self.datahist))+" ORDER BY epoch ASC", self.conn_a34972a)
				# Convert Pandas objects to regular arrays
				volt_a34972a.append(numpy.array(df["sensor"]))
				absdate.append(numpy.array(df["absolutetime"]))
				epoch.append(numpy.array(df["epoch"]))
		except Exception as e:
			print("Fault during SQL fetching the data in the file a34972a.db ->\n",str(e))
		else:
			# Get indexed data points in order to reduce data points to make faster plots
			volt_a34972a_ = []
			for i in range(len(self.chnls)):
				if len(volt_a34972a[i])>self.points:
					#LINSPACE method
					indcs = [int(tal) for tal in numpy.linspace(0,len(volt_a34972a[i])-1,self.points)]
				else:
					#LINSPACE method
					indcs = range(len(volt_a34972a[i]))
				#LINSPACE method
				volt_a34972a_.append([ volt_a34972a[i][ii] for ii in indcs ])
				# Set the text and full date for the latest reading
				if len(volt_a34972a[i])>0:
					self.a34972a_vals[i].setText( ''.join(["sensor @", self.chnls[i][2:], " -> ",Quantity(volt_a34972a_[i][-1],"V").render(prec=2),"\n\u0394time: ", str(datetime.timedelta(seconds=round(epoch[i][-1]-epoch[i][0])))," (",str(len(epoch[i])),"; ",Quantity(time.time()-time_s,"s").render(prec=2),")"]) )

			############################################################
			# PLOT the data in different curves
			for i in range(len(self.chnls)):
				self.curves[i].setData(volt_a34972a_[i])
		# Open the thread for updates
		self.worker_a34972a.readyForUpdate(True)


	def finished(self):
		
		# Wait for all the threads to finish
		self.threadpool.waitForDone()
		####################################
		if hasattr(self,'conn_k2000m'):
			self.conn_k2000m.close()
		if hasattr(self,'conn_k2001m'):
			self.conn_k2001m.close()
		if hasattr(self,'conn_a34972a'):
			self.conn_a34972a.close()
		####################################
		self.isRunning=False
		self.combo0.setEnabled(True)
		self.combo1.setEnabled(True)
		self.combo2.setEnabled(True)
		self.cwdEdit.setEnabled(True)
		self.chnlsEdit.setEnabled(True)
		self.clearButton.setEnabled(True)
		self.clearButton.setText("Clear plots")
			
			
	def clear_vars_graphs(self):
		
		# PLOT 2 initial canvas settings
		self.curve1.clear()
		self.curve2.clear()
		for i in range(len(self.chnls)):
			self.curves[i].clear()
		
			
	def closeEvent(self, event):
		reply = QMessageBox.question(self, 'Message', "Quit the plotter now?", QMessageBox.Yes | QMessageBox.No)
		if reply == QMessageBox.Yes:
			if self.isRunning:
				QMessageBox.warning(self, 'Message', "Run in progress. Cancel the scan then quit!")
				event.ignore()
				return
			
			event.accept()
		else:
		  event.ignore() 



###################
###################
###################



class HelpWindow(QDialog):

	def __init__(self):
		super().__init__()
		self.title = "Help window explaining canvas items"
		self.top = 200
		self.left = 500
		self.width = 400
		self.height = 300
		self.InitWindow()

	def	InitWindow(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		vbox = QVBoxLayout()
		labelImage = QLabel(self)
		pixmap = QPixmap("Data_aqusition_plotter.png")
		labelImage.setPixmap(pixmap)
		vbox.addWidget(labelImage)
		self.setLayout(vbox)
		
		# re-adjust/minimize the size of the e-mail dialog
		# depending on the number of attachments
		#vbox.setSizeConstraint(vbox.SetFixedSize)

	def closeEvent(self,event):
			
		event.accept()


#########################################
#########################################
#########################################
	
	
def main():
	
	app = QApplication(sys.argv)
	ex = Run_gui()
	ex.set_run()
	#sys.exit(app.exec())

	# avoid message 'Segmentation fault (core dumped)' with app.deleteLater()
	app.exec()
	app.deleteLater()
	sys.exit()
	
	
if __name__ == '__main__':
	
	main()
	
	
