# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 22:05:44 2021

@author: opd32
"""
import matplotlib
matplotlib.use('Qt5Agg')
matplotlib.rcParams.update({'font.size': 14})
import numpy as np
import time, datetime

from bs4 import BeautifulSoup
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QSettings
import inspect
# from distutils.util import strtobool
from PyQt5.QtWidgets import QComboBox,\
    QPushButton, QWidget, QFormLayout, QLineEdit, QVBoxLayout,\
        QCheckBox, QProgressBar
        
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from binance.client import Client

#% MAIN GUI
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, subplot=2):
        fig = Figure(figsize=(width, height), dpi=dpi)
        if subplot == 1:
            self.axes = fig.add_subplot(111)
        else:
            self.axes = fig.add_subplot(211)
            self.axes1 = fig.add_subplot(212)
        super(MplCanvas, self).__init__(fig)
        
class AnotherWindow(QWidget):
    def __init__(self, binance_api=None, exchange=None):
        super().__init__()
        app_icon = QtGui.QIcon()
        app_icon.addFile('logo.png', QtCore.QSize(16,16))
        self.setWindowIcon(app_icon)
        self._exchange = exchange
        self.api = binance_api
        if exchange == "FUTURES":
            info = self.api.futures_exchange_info()
        elif exchange == "SPOT":
            info = self.api.get_exchange_info()
            
        self.cb_strategy = QComboBox()
        self.cb_strategy.addItem("1m")
        self.cb_strategy.addItem("5m")
        self.cb_strategy.addItem("15m")
        self.cb_strategy.addItem("30m")
        
        self.cb_strategy1 = QComboBox()
        for s in info['symbols']:
            self.cb_strategy1.addItem(s['symbol'])

        self.coin_name = QLineEdit() # auto_sell_spinbox
        self.bin = QLineEdit() # stop_loss_spinbox
        self.candles = QLineEdit() # stop_loss_spinbox
        
        self.coin_name.setText("none")
        self.bin.setText("180")
        self.candles.setText("1500")
        # button for load config file
        self.btn_config = QPushButton('Plot')
        self.btn_config.clicked.connect(self.plot_pc)
        
        self.layout = QVBoxLayout()
        # self.layout.setSpacing(0)
        # self.layout.setMargin(0)
        # a figure instance to plot on
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)        
        # set the layout
        self.layout.addWidget(self.toolbar, 0)
        self.layout.addWidget(self.canvas, 100)
        
        formLayout = QFormLayout()
        formLayout.addRow('COIN symbol (exhaustive list):', self.cb_strategy1)
        formLayout.addRow('COIN symbol (or manual):', self.coin_name)
        formLayout.addRow('Time interval:', self.cb_strategy)
        formLayout.addRow('Bin length (in integer):', self.bin)
        formLayout.addRow('Nb of candles (in integer):', self.candles)
        formLayout.addRow(self.btn_config)      
        
        self.layout.addLayout(formLayout, 0)
        self.setLayout(self.layout)
        
    def plot_pc(self):
        self.canvas.figure.clf() 
        
        self.time_interval = self.cb_strategy.currentText()
        self.candles_use = int(self.candles.text())
        self.binn = int(self.bin.text())
        
        if self.coin_name.text() == "none":
            self.listcoin = [self.cb_strategy1.currentText()]
        else:
            self.listcoin = self.coin_name.text().split(',')
        # create an axis
        ax = self.figure.add_subplot(111)
        # discards the old graph
        ax.clear()
        
        for j1, coin in enumerate(self.listcoin):
            if self._exchange == "FUTURES":
                trades= self.api.futures_klines(symbol=coin, interval=self.time_interval, limit=self.candles_use)
            elif self._exchange == "SPOT":
                trades= self.api.get_klines(symbol=coin, interval=self.time_interval, limit=self.candles_use)
            
            ## candle stats
            sign = []
            for d in trades:
                if (float(d[4]) - float(d[1])):
                    sign.append(1)
                else:
                    sign.append(-1)
            percentT = [100*(float(d[2]) - float(d[3]))/float(d[2]) for i, d in enumerate(trades)]
            percentT1 = [100*sign[i]*(float(d[4]) - float(d[1]))/float(d[4]) for i, d in enumerate(trades)]
            # matplotlib histogram
            ax.hist(percentT,
                      bins = self.binn, density =True, label=coin+" Candle high-low change(%)",alpha = 0.5)
            ax.hist(percentT1,
                      bins = self.binn, density =True, label=coin+" Candle close-open change(%)",alpha = 0.5)  
            ax.axvline(np.mean(percentT), color='k', linestyle='dashed', linewidth=2)
        ax.legend(loc=4)    
        ax.set_xlabel(r'Price changes')
        ax.set_ylabel(r'Probability')
        ax.grid(linestyle='--', linewidth=0.5)
        self.canvas.draw()

class AnotherWindowDynamic(QWidget):
    def __init__(self, binance_api=None, exchange=None):
        super().__init__()
        app_icon = QtGui.QIcon()
        app_icon.addFile('logo.png', QtCore.QSize(16,16))
        self.setWindowIcon(app_icon)
        self._exchange = exchange
        self.api = binance_api
        if exchange == "FUTURES":
            info = self.api.futures_exchange_info()
        elif exchange == "SPOT":
            info = self.api.get_exchange_info()
        
        self.cb_strategy1 = QComboBox()
        for s in info['symbols']:
            self.cb_strategy1.addItem(s['symbol'])
            
        self.cb_strategy2 = QComboBox()
        self.cb_strategy2.addItem("Trades")
        if self._exchange == "FUTURES":
            self.cb_strategy2.addItem("Liquidation")

        self.candles = QLineEdit() # stop_loss_spinbox
        self.data_limit = QLineEdit() # stop_loss_spinbox
        self.interval = QLineEdit() # stop_loss_spinbox
        self.volume24 = QLineEdit() # stop_loss_spinbox
        self.volume24.setReadOnly(True)
        
        self.candles.setText("50")
        self.data_limit.setText("1000")
        self.interval.setText("1000")
        
        # button for load config file
        self.btn_config = QPushButton('Plot')
        self.btn_config.clicked.connect(self.plot_pc)
        
        self.btn_stop = QPushButton('Stop the plot')
        self.btn_stop.clicked.connect(self.plot_btn_stop)
        
        self.btn_config.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        layout = QVBoxLayout()
        # a figure instance to plot on
        # self.figure = Figure()
        # self.canvas = FigureCanvas(self.figure)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
             
        # set the layout
        layout.addWidget(self.toolbar, 0)
        layout.addWidget(self.canvas, 100)
        
        formLayout = QFormLayout()
        formLayout.addRow('COIN symbol (exhaustive list):', self.cb_strategy1)
        formLayout.addRow('Info to plot:', self.cb_strategy2)
        formLayout.addRow('Moving window size (in integer):', self.data_limit)
        formLayout.addRow('Nb of trades (in integer):', self.candles)
        formLayout.addRow('Plot update time (in ms integer):', self.interval)
        formLayout.addRow('24 hour volume (in USDT):', self.volume24)
        formLayout.addRow(self.btn_stop, self.btn_config)
        
        layout.addLayout(formLayout, 0)
        self.setLayout(layout)
        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
        
    def plot_btn_stop(self):
        self.timer.stop()
        self.btn_config.setEnabled(True)
        self.btn_stop.setEnabled(False)
    
    def update_plot(self):
        # Drop off the first y element, append a new one.
        self.canvas.axes.cla()  # Clear the canvas.
        if self.cb_strategy2.currentText() != "Trades" and self._exchange == "FUTURES":
            self.canvas.axes.plot(self.xdata, self.ydatalb, lw=5, c='g', label=self.listcoin[0]+" Liquidation BUY (SHORTS)")
            self.canvas.axes.plot(self.xdata, self.ydatals, lw=5, c='r', label=self.listcoin[0]+" Liquidation SELL (LONGS)")
        else:
            self.canvas.axes.plot(self.xdata, self.ydata, lw=5, c='b', label=self.listcoin[0]+" (BUY-SELL)")
            self.canvas.axes.scatter(self.xdata, self.ydata1, s=10, c='g', label=self.listcoin[0]+" (BUY)")
            self.canvas.axes.scatter(self.xdata, self.ydata2, s=10, c='r', label=self.listcoin[0]+" (SELL)")
        self.canvas.axes.axhline(y=0, lw=1, c='k')
        self.canvas.axes.set_ylabel(self.listcoin[0]+' Volume in USDT)')
        # self.canvas.axes.set_xlabel(r'Time (multiple of interval)')
        self.canvas.axes.grid(linestyle='--', linewidth=0.5)
        self.canvas.axes.legend(loc=0)
        self.canvas.axes.set_xlim([self.xlinn,self.count+5])
        if self.count > 10:
            if self.cb_strategy2.currentText() != "Trades":
               self.canvas.axes.set_ylim([np.min((self.ydatalb,self.ydatals)),\
                                           np.max((self.ydatalb,self.ydatals))])
            else:
                self.canvas.axes.set_ylim([np.min((self.ydata,self.ydata1,self.ydata2)),\
                                            np.max((self.ydata,self.ydata1,self.ydata2))])
            
        self.canvas.axes1.cla()  # Clear the canvas.
        self.canvas.axes1.plot(self.xdata, self.ydata3, c='b', label=self.listcoin[0]+" price")
        self.canvas.axes1.axhline(y=0, lw=1, c='k')
        self.canvas.axes1.set_ylabel(r'Current Price')
        self.canvas.axes1.set_xlabel(r'Time (multiple of interval)')
        self.canvas.axes1.grid(linestyle='--', linewidth=0.5)
        # self.canvas.axes1.legend(loc=0,prop={'size':4})
        self.canvas.axes1.set_xlim([self.xlinn,self.count+5])
        if self.count > 10:
            self.canvas.axes1.set_ylim([np.min(self.ydata3),np.max(self.ydata3)])
        # Trigger the canvas to update and redraw.
        self.canvas.draw()
                
    def plot_pc(self):
        # self.starttime = int(time.time() * 1000)
        self.btn_config.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.xdata = 0
        self.ydata = 0
        self.ydata1 = 0
        self.ydata2 = 0
        self.ydata3 = 0
        self.ydatalb = 0
        self.ydatals = 0
        self.xlinn = 0

        self.candles_use = int(self.candles.text())
        self.nb_data = int(self.data_limit.text())
        self.listcoin = [self.cb_strategy1.currentText()]
        
        self.count = 0
        self.count_plt = []
        self.bms = []
        self.lb = []
        self.ls = []
        self.bmsr = []
        self.bb = []
        self.ss = []
        self.temp1 = []
        
        self.update_plot()
        
        self.timer.setInterval(int(self.interval.text()))
        self.timer.timeout.connect(self.plot_pcv1)
        self.timer.start()

    def plot_pcv1(self):
        if self._exchange == "FUTURES":
            trades= self.api.futures_recent_trades(symbol=self.listcoin[0], limit=self.candles_use)
            # TODO liquidation stream no longer possible; should start a socket for feed
            # liq = self.api.futures_liquidation_orders(symbol=self.listcoin[0], limit=self.candles_use)
            # # deal with liquidation data
            # temp_buy = [[float(d['executedQty']),float(d['price'])] for d in liq \
            #         if ([float(d['executedQty']),float(d['price'])] not in self.temp1) and (d['side']=="BUY")]
            
            # temp_sell = [[float(d['executedQty']),float(d['price'])] for d in liq \
            #         if ([float(d['executedQty']),float(d['price'])] not in self.temp1) and (d['side']=="SELL")]

            
            # for i_ in range(len(temp_buy)):
            #     self.temp1.append(temp_buy[i_])
            # for i_ in range(len(temp_sell)):
            #     self.temp1.append(temp_sell[i_])
            
            # liq_b = np.sum(np.array([t[0]*t[1] for t in temp_buy]))
            # liq_s = np.sum(np.array([t[0]*t[1] for t in temp_sell]))

            liq_b = None
            liq_s = None
        elif self._exchange == "SPOT":
            trades= self.api.get_recent_trades(symbol=self.listcoin[0], limit=self.candles_use)
            liq_b = None
            liq_s = None
             
        indices = [d['isBuyerMaker'] for d in trades]
        trades_quantity = [float(d['qty'])*float(d['price']) for d in trades] ## in USDT
        price_recent = [float(d['price']) for d in trades] ## in USDT
        indices = np.array(indices)
        trades_quantity = np.array(trades_quantity)
        price_recent = np.average(np.array(price_recent))
        
        if (self.count == 0) or (self.count%3000 == 0):
            if self._exchange == "FUTURES":
                dt = self.api.futures_ticker(symbol=self.listcoin[0])
            elif self._exchange == "SPOT":
                dt = self.api.get_ticker(symbol=self.listcoin[0])
            
            volume24 = float(dt['volume'])*float(dt['weightedAvgPrice']) ## In USDT in millions
            self.volume24.setText(str(volume24))
        
        selling = np.sum(trades_quantity[np.where(indices==True)[0]])
        buying  = np.sum(trades_quantity[np.where(indices==False)[0]])

        if self.count - self.nb_data <0:
            self.xlinn = 0
        else:
            self.xlinn = self.count - self.nb_data
            
        self.count_plt.append(self.count)
        self.bms.append(buying-selling)
        self.bb.append(buying)
        self.bmsr.append(price_recent)
        self.ss.append(selling)
        self.lb.append(liq_b)
        self.ls.append(liq_s)

        self.xdata  = self.count_plt
        self.ydata  = self.bms
        self.ydata1  = self.bb
        self.ydata2  = self.ss
        self.ydata3  = self.bmsr
        self.ydatalb  = self.lb
        self.ydatals  = self.ls
        self.update_plot()
        self.count = self.count + 1

        ## remove some data to free up RAM
        if len(self.count_plt) > 2*self.nb_data:
            self.count_plt = self.count_plt[-self.nb_data:]
            self.bms = self.bms[-self.nb_data:]
            self.bmsr = self.bmsr[-self.nb_data:]
            self.bb = self.bb[-self.nb_data:]
            self.ss = self.ss[-self.nb_data:]
            self.lb = self.lb[-self.nb_data:]
            self.ls = self.ls[-self.nb_data:]

class AnotherWindowDynamicBTC(QWidget):
    got_signal = QtCore.pyqtSignal(dict)
    
    def __init__(self, display_text=None):
        super().__init__()
        app_icon = QtGui.QIcon()
        app_icon.addFile('logo.png', QtCore.QSize(16,16))
        self.setWindowIcon(app_icon)
        
        self.display_ = display_text
        from selenium.webdriver.firefox.options import Options
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-gpu')
        
        self.cb_strategy1 = QComboBox()
        self.cb_strategy1.addItem('BTC/USD')
        self.cb_strategy1.addItem('ETH/USD')
        self.cb_strategy1.addItem('DOGE/USD')
        self.cb_strategy1.currentIndexChanged.connect(self.temp_but)
        
        self.cb_strategy2 = QComboBox()
        self.cb_strategy2.addItem("Trades")
        self.cb_strategy2.addItem("Liquidation")
        
        self.data_limit = QLineEdit() # stop_loss_spinbox
        self.interval = QLineEdit() # stop_loss_spinbox
        self.save_file = QLineEdit() # stop_loss_spinbox
        self.lots_data = QLineEdit()
        
        self.lots_data.setText("1e5,1e5,50,100,2")
        self.data_limit.setText("1000")
        self.interval.setText("1000")
        self.save_file.setText("BTC_stats")
        # button for load config file
        self.btn_config = QPushButton('Plot')
        self.btn_config.clicked.connect(self.plot_pc)
        
        self.btn_stop = QPushButton('Stop the plot')
        self.btn_stop.clicked.connect(self.plot_btn_stop)
        
        self.btn_config.setEnabled(True)
        self.btn_stop.setEnabled(False)

        self.b1 = QCheckBox("Bitmex")
        self.b1.setChecked(True)
        self.b2 = QCheckBox("Bybit")
        self.b2.setChecked(True)
        self.b3 = QCheckBox("Deribit")
        self.b3.setChecked(True)
        self.b4 = QCheckBox("Kraken")
        self.b4.setChecked(True)
        self.b5 = QCheckBox("Binance futures")
        self.b5.setChecked(True)
        self.b6 = QCheckBox("FTX futures")
        self.b6.setChecked(True)
        self.b7 = QCheckBox("Coinbase PRO")
        self.b7.setChecked(True)
        self.b8 = QCheckBox("Bitstamp")
        self.b8.setChecked(True)
        self.b9 = QCheckBox("Binance")
        self.b9.setChecked(True)
        self.b10 = QCheckBox("FTX")
        self.b10.setChecked(True)
        
        layout = QVBoxLayout()
        # a figure instance to plot on
        # self.figure = Figure()
        # self.canvas = FigureCanvas(self.figure)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
             
        # set the layout
        layout.addWidget(self.toolbar, 0)
        layout.addWidget(self.canvas, 100)
        
        formLayout = QFormLayout()
        formLayout.addRow('COIN symbol (Multiple exchanges):', self.cb_strategy1)
        formLayout.addRow(self.b1, self.b2)
        formLayout.addRow(self.b3, self.b4)
        formLayout.addRow(self.b5, self.b6)
        formLayout.addRow(self.b7, self.b8)
        formLayout.addRow(self.b9, self.b10)
        formLayout.addRow('Info to plot:', self.cb_strategy2)
        formLayout.addRow('Moving window size (in integer):', self.data_limit)
        formLayout.addRow('Plot update time (in ms integer):', self.interval)
        formLayout.addRow('Threshold, investment, safety, trades for LONG/SHORT:', self.lots_data)
        formLayout.addRow('save file:', self.save_file)
        formLayout.addRow(self.btn_stop, self.btn_config)
        
        layout.addLayout(formLayout, 0)
        
        self.setLayout(layout)
        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
    
    def temp_but(self):
        if self.cb_strategy1.currentText() == 'DOGE/USD':
            self.b2.setEnabled(False)
            self.b2.setChecked(False)
            self.b3.setEnabled(False)
            self.b3.setChecked(False)
            self.b4.setEnabled(False)
            self.b4.setChecked(False)
            self.b7.setEnabled(False)
            self.b7.setChecked(False)
            self.b8.setEnabled(False)
            self.b8.setChecked(False)
        else:
            self.b1.setEnabled(True)
            self.b2.setEnabled(True)
            self.b3.setEnabled(True)
            self.b4.setEnabled(True)
            self.b7.setEnabled(True)
            self.b8.setEnabled(True)
            self.b5.setEnabled(True)
            self.b6.setEnabled(True)
            self.b9.setEnabled(True)
            self.b10.setEnabled(True)
        
    def closeEvent(self, event):
        try:
            self.driver.close()
            self.driver.quit()
        except:
            pass
        self.timer.stop()
        self.close()
        
    def plot_btn_stop(self):
        try:
            self.driver.close()
            self.driver.quit()
        except:
            pass
        self.timer.stop()
        self.btn_config.setEnabled(True)
        self.cb_strategy1.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        self.b1.setEnabled(True)
        self.b2.setEnabled(True)
        self.b3.setEnabled(True)
        self.b4.setEnabled(True)
        self.b7.setEnabled(True)
        self.b8.setEnabled(True)
        self.b5.setEnabled(True)
        self.b6.setEnabled(True)
        self.b9.setEnabled(True)
        self.b10.setEnabled(True)
    
    def update_plot(self):
        # Drop off the first y element, append a new one.
        self.canvas.axes.cla()  # Clear the canvas.
        if self.cb_strategy2.currentText() == 'Trades':
            self.canvas.axes.plot(self.xdata, self.ydata, lw=5, c='b', label="(BUY-SELL)")
            self.canvas.axes.scatter(self.xdata, self.ydata1, s=10, c='g', label="(BUY)")
            self.canvas.axes.scatter(self.xdata, self.ydata2, s=10, c='r', label="(SELL)")
        elif self.cb_strategy2.currentText() == 'Liquidation':
            self.canvas.axes.plot(self.xdata, self.ydatalb, lw=5, c='g', label="Liquidation BUY (SHORTS)")
            self.canvas.axes.plot(self.xdata, self.ydatals, lw=5, c='r', label="Liquidation SELL (LONGS)")
        self.canvas.axes.axhline(y=0, lw=1, c='k')
        self.canvas.axes.set_ylabel(r'Volume in USDT')
        self.canvas.axes.grid(linestyle='--', linewidth=0.5)
        self.canvas.axes.legend(loc=0)
        self.canvas.axes.set_xlim([self.xlinn,self.count+5])
        if self.count > 10:
            if self.cb_strategy2.currentText() == 'Trades':
                self.canvas.axes.set_ylim([np.min((self.ydata,self.ydata1,self.ydata2)),\
                                            np.max((self.ydata,self.ydata1,self.ydata2))])
            else:
                self.canvas.axes.set_ylim([np.min((self.ydatalb,self.ydatals)),\
                                           np.max((self.ydatalb,self.ydatals))])
            
        self.canvas.axes1.cla()  # Clear the canvas.
        self.canvas.axes1.plot(self.xdata, self.ydata3, lw=5, c='b')
        self.canvas.axes1.axhline(y=0, lw=1, c='k')
        self.canvas.axes1.set_ylabel(r'Current Weighted Price')
        self.canvas.axes1.set_xlabel(r'Time (multiples of interval)')
        self.canvas.axes1.grid(linestyle='--', linewidth=0.5)
        self.canvas.axes1.set_xlim([self.xlinn,self.count+5])
        if self.count > 10:
            self.canvas.axes1.set_ylim([np.min(self.ydata3),np.max(self.ydata3)])
        # Trigger the canvas to update and redraw.
        self.canvas.draw()
                
    def plot_pc(self):
        import functools
        from selenium import webdriver
        try:        
            url='https://coinlobster.com/combined.html'
            flag = 0x08000000  # No-Window flag
            webdriver.common.service.subprocess.Popen = functools.partial(
                                                        webdriver.common.service.subprocess.Popen, 
                                                        creationflags=flag)
            self.driver = webdriver.Firefox(options=self.options)
            self.driver.get(url)
            time.sleep(5) ## allows to load page
        except:
            return
        
        self.b1.setEnabled(False)
        self.b2.setEnabled(False)
        self.b3.setEnabled(False)
        self.b4.setEnabled(False)
        self.b5.setEnabled(False)
        self.b6.setEnabled(False)
        self.b7.setEnabled(False)
        self.b8.setEnabled(False)
        self.b9.setEnabled(False)
        self.b10.setEnabled(False)
        
        self.btn_config.setEnabled(False)
        self.cb_strategy1.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        select = self.driver.find_element_by_id('selected-pair-option')
        select.click()
        time.sleep(2)
        coin_consider = self.cb_strategy1.currentText()
        a = select.parent.find_elements_by_tag_name('a')
        time.sleep(2)
        if coin_consider == 'BTC/USD':
            a[5].click() # FOR BTC/USD
            self.save_file.setText("BTC_stats")
        elif coin_consider == 'ETH/USD':
            a[6].click() # FOR ETH/USD
            self.save_file.setText("ETH_stats")
        elif coin_consider == 'DOGE/USD':
            a[7].click()
            self.save_file.setText("DOGE_stats")
        
        time.sleep(2)
        
        select1 = self.driver.find_element_by_id('futures-exchanges-list')
        i = select1.parent.find_elements_by_tag_name('i')
        
        if coin_consider == 'BTC/USD' or coin_consider == 'ETH/USD':
            if self.b1.isChecked() == False:
                i[5].click() #BITMEX DOGE
            if self.b2.isChecked() == False:
                i[6].click() # BYBIT
            if self.b3.isChecked() == False:
                i[7].click() # DERIBIT
            if self.b4.isChecked() == False:
                i[8].click() # Kraken futures
            if self.b5.isChecked() == False:
                i[9].click() # Binance futures DOGE
            if self.b6.isChecked() == False:
                i[10].click() # Ftx futures DOGE
            if self.b7.isChecked() == False:
                i[11].click() # Coinbase PRO
            if self.b8.isChecked() == False:
                i[12].click() # Bitstamp
            if self.b9.isChecked() == False:
                i[13].click() # Binance DOGE
            if self.b10.isChecked() == False:
                i[14].click() # Ftx DOGE
            ## save some ram
            i[15].click() # Close plots
            i[16].click() # Close Piechart
            i[17].click() # Close Weighted average price
        elif coin_consider == 'DOGE/USD':
            if self.b1.isChecked() == False:
                i[5].click() #BITMEX DOGE
            if self.b5.isChecked() == False:
                i[6].click() # Binance futures DOGE
            if self.b6.isChecked() == False:
                i[7].click() # Ftx futures DOGE
            if self.b9.isChecked() == False:
                i[8].click() # Binance DOGE
            if self.b10.isChecked() == False:
                i[9].click() # Ftx DOGE
            ## save some ram
            i[10].click() # Close plots
            i[11].click() # Close Piechart
            i[12].click() # Close Weighted average price
        
        ct = time.time()
        now = datetime.datetime.fromtimestamp(ct)
        c_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename_ = self.save_file.text() + "_" + c_time
        self.save_file.setText(filename_)
        
        exc = ['binance', 'binancefutures', 'bitmex', 'bitstamp', 'bybit',
               'coinbasepro', 'deribit', 'ftx', 'ftxfutures', 'krakenfutures']
        
        str1 = [i+"_BTC_bought" for i in exc]
        str2 = [i+"_BTC_sold" for i in exc]
        str3 = [i+"_liquidations_(LONGS)" for i in exc]
        str4 = [i+"_liquidations_(SHORTS)" for i in exc]
        
        str1 = ' '.join(str1)
        str2 = ' '.join(str2)
        str3 = ' '.join(str3)
        str4 = ' '.join(str4)
        big_string = " " + str1 + " " + str2 + " " + str3 + " " + str4 + " \n"
        with open(self.save_file.text()+".txt", "w") as myfile:
            myfile.write("#Date_Time BTC_average_price(USDT) BTC_bought(USDT) BTC_sold(USDT)"+\
                         " Total_liquidations_(SHORTS) Total_liquidations_(LONGS)"+big_string)
        
        self.xdata = 0
        self.ydata = 0
        self.ydata1 = 0
        self.ydata2 = 0
        self.ydata3 = 0
        self.xlinn = 0
        self.ydatalb = 0
        self.ydatals = 0
        
        self.nb_data = int(self.data_limit.text())
        
        self.count = 0
        self.count_plt = []
        self.bms = []
        self.bmsr = []
        self.bb = []
        self.ss = []
        self.lb = []
        self.ls = []
        self.temp1 = []
        
        self.update_plot()
        
        self.timer.setInterval(int(self.interval.text()))
        self.timer.timeout.connect(self.plot_pcv1)
        self.timer.start()

    def plot_pcv1(self):
        
        #↕ split the content of the liq details
        tempp = self.lots_data.text()
        tempp = tempp.split(',')
        
        content = self.driver.page_source
        soup = BeautifulSoup(content, features="html.parser")

        ## Get the whole table (doing trades only)
        trades = soup.find('tbody', {'id':"trades"})
        table_tr_sell = trades.find_all('tr', {"class": "trade-detail text-danger"})
        data_sold = []
        exchange_sold = []
        for row in table_tr_sell:
            img = row.find('img')
            exchange_sold.append(img['src'].split('/')[-1].split('.')[0].split('-')[0])
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            temp = [float(ele.replace(',','')) for ele in cols[:2] if ele] #:2 to not consider time
            data_sold.append(temp[0] * temp[1]) # Get rid of empty values
            
        table_tr_buy = trades.find_all('tr', {"class": "trade-detail text-success"})    
        data_buy = []
        exchange_buy = []
        for row in table_tr_buy:
            img = row.find('img')
            exchange_buy.append(img['src'].split('/')[-1].split('.')[0].split('-')[0])
            cols = row.find_all('td')
            cols = [ele.text.strip()  for ele in cols]
            temp = [float(ele.replace(',','')) for ele in cols[:2] if ele] #:2 to not consider time
            data_buy.append(temp[0] * temp[1]) # Get rid of empty values
        data_buy = np.array(data_buy)
        data_sold = np.array(data_sold)
        
        selling = np.sum(data_sold)
        buying  = np.sum(data_buy)
        # orderbook = soup.find('tbody', {'id':"orderbook"})
        # table_ob = orderbook.find_all('tr')
        
        liquidations = soup.find('tbody', {'id':"liquidations"})   
        ## LONGS GETTING LIQUIDATED
        liquidations_sell = liquidations.find_all('tr', {"class": "liquidation-detail text-danger"})
        exchange_red = []
        data_red = []
        for row in liquidations_sell:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            temp = [float(ele.replace(',','')) for ele in cols[:2] if ele] #:2 to not consider time
            if temp in self.temp1:
                continue
            else:
                img = row.find('img')
                exchange_red.append(img['src'].split('/')[-1].split('.')[0].split('-')[0])
                self.temp1.append(temp)
            data_red.append(temp[0] * temp[1]) # Get rid of empty values
        ## SHORTS GETTING LIQUIDATED
        liquidations_buy = liquidations.find_all('tr', {"class": "liquidation-detail text-success"})  
        exchange_green = []
        data_green = []
        for row in liquidations_buy:
            cols = row.find_all('td')
            cols = [ele.text.strip()  for ele in cols]
            temp = [float(ele.replace(',','')) for ele in cols[:2] if ele] #:2 to not consider time
            if temp in self.temp1:
                continue
            else:
                img = row.find('img')
                exchange_green.append(img['src'].split('/')[-1].split('.')[0].split('-')[0])
                self.temp1.append(temp)
            data_green.append(temp[0] * temp[1]) # Get rid of empty values
        data_green = np.array(data_green)
        data_red = np.array(data_red)
        
        liq_red = np.sum(data_red)
        liq_green  = np.sum(data_green)
        
        # TODO (Preliminary version)
        #### make a filter here and send signal via dict to the Qmainwindow for the bot
        #### to change strategy based on the BTC dynamic
        emit_dictionary = False
        if liq_red > float(tempp[0]) and self.count > 20:
            emit_dictionary = {"direction": "SHORT", "investment": float(tempp[2]), \
                               "safety": float(tempp[3]), "limtrades":int(tempp[4])}
        if liq_green > float(tempp[1]) and self.count > 20:
            emit_dictionary = {"direction": "LONG", "investment": float(tempp[2]), \
                               "safety": float(tempp[3]), "limtrades":int(tempp[4])}
        if emit_dictionary:
            self.got_signal.emit(emit_dictionary)
        
        recent_price = soup.find('h1', {'id':"weighted-mid"})
        price_recent = float(recent_price.text.strip().replace(',',''))
        
        ## sort based on exchanges
        exc = ['binance', 'binancefutures', 'bitmex', 'bitstamp', 'bybit',
               'coinbasepro', 'deribit', 'ftx', 'ftxfutures', 'krakenfutures']
        list_exc_sold = [[] for i in range(len(exc))]
        list_exc_buy = [[] for i in range(len(exc))]
        list_exc_red = [[] for i in range(len(exc))]
        list_exc_green = [[] for i in range(len(exc))]
        for ind_, exe_ in enumerate(exc):
            list_exc_sold[ind_].append(np.sum(data_sold[np.where(np.array(exchange_sold)==exe_)[0]]))
            list_exc_buy[ind_].append(np.sum(data_buy[np.where(np.array(exchange_buy)==exe_)[0]]))
            if len(data_red) > 0:
                list_exc_red[ind_].append(np.sum(data_red[np.where(np.array(exchange_red)==exe_)[0]]))
            if len(data_green) > 0:
                list_exc_green[ind_].append(np.sum(data_green[np.where(np.array(exchange_green)==exe_)[0]]))
        
        str1 = [str(round(i[0],0)) for i in list_exc_sold]
        str2 = [str(round(i[0],0)) for i in list_exc_buy]
        str3 = []
        for i in list_exc_red:
            if len(i) > 0:
                str3.append(str(round(i[0],0)))
            else:
                str3.append(str(0))
                
        str4 = []
        for i in list_exc_green:
            if len(i) > 0:
                str4.append(str(round(i[0],0)))
            else:
                str4.append(str(0))        
        
        str1 = ' '.join(str1)
        str2 = ' '.join(str2)
        str3 = ' '.join(str3)
        str4 = ' '.join(str4)
        big_string = " " + str1 + " " + str2 + " " + str3 + " " + str4 + " \n"
        ct = time.time()
        now = datetime.datetime.fromtimestamp(ct)
        c_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        with open(self.save_file.text()+".txt", "a") as myfile:
            myfile.write(c_time+ " "+str(round(price_recent, 0))+" "+ str(round(buying, 0)) +\
                         " "+ str(round(selling,0))+" "+ str(round(liq_green,0))+\
                             " "+ str(round(liq_red,0))+ big_string)

        if (self.count - self.nb_data) < 0:
            self.xlinn = 0
        else:
            self.xlinn = self.count - self.nb_data
        
        self.count_plt.append(self.count)
        self.bms.append(buying-selling)
        self.bb.append(buying)
        self.bmsr.append(price_recent)
        self.ss.append(selling)
        self.lb.append(liq_green)
        self.ls.append(liq_red)
        
        self.xdata  = self.count_plt
        self.ydata  = self.bms
        self.ydata1  = self.bb
        self.ydata2  = self.ss
        self.ydata3  = self.bmsr
        self.ydatalb  = self.lb
        self.ydatals  = self.ls
        self.update_plot()
        
        self.count = self.count + 1
        
        ## remove some data to free up RAM
        if len(self.count_plt) > 2*self.nb_data:
            # ind_tem = len(self.temp1)//2
            # self.temp1 = self.temp1[-ind_tem:]
            self.count_plt = self.count_plt[-self.nb_data:]
            self.bms = self.bms[-self.nb_data:]
            self.bmsr = self.bmsr[-self.nb_data:]
            self.bb = self.bb[-self.nb_data:]
            self.ss = self.ss[-self.nb_data:]
            self.lb = self.lb[-self.nb_data:]
            self.ls = self.ls[-self.nb_data:]

class AnotherWindowDynamicFS(QWidget):
    got_text = QtCore.pyqtSignal(dict)
    def __init__(self, binance_api=None):
        super().__init__()
        app_icon = QtGui.QIcon()
        app_icon.addFile('logo.png', QtCore.QSize(16,16))
        self.setWindowIcon(app_icon)
        
        self.api = binance_api
        info = self.api.futures_exchange_info()
        
        self.coins = []
        self.cb_strategy1 = QComboBox()
        for s in info['symbols']:
            self.coins.append(s['symbol'])
            self.cb_strategy1.addItem(s['symbol'])

        self.progress = QProgressBar()
        # self.progress.setGeometry(0, 0, 300, 25)
        self.progress.setMaximum(len(self.coins))
        
        self.interval = QComboBox()
        for s in ["5m","15m","30m","1h","2h","4h","6h","12h","1d"]:
            self.interval.addItem(s)
        self.interval.setCurrentText("15m") 
         
        self.candles = QLineEdit() # stop_loss_spinbox
        self.candles.setText("10")
        # button for load config file
        self.btn_config = QPushButton('Plot')
        self.btn_config.clicked.connect(self.plot_pc)
        
        self.btn_config1 = QPushButton('Print stats (takes time)')
        self.btn_config1.clicked.connect(self.plot_pc1)
        
        layout = QVBoxLayout()
        # a figure instance to plot on
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100, subplot=1)
        self.toolbar = NavigationToolbar(self.canvas, self)
        # set the layout
        layout.addWidget(self.toolbar, 0)
        layout.addWidget(self.canvas, 100)
        formLayout = QFormLayout()
        formLayout.addRow('COIN symbol (exhaustive list):', self.cb_strategy1)
        formLayout.addRow('Nb of trades (in integer MAX 30):', self.candles)
        formLayout.addRow('Data update time:', self.interval)
        formLayout.addRow(self.btn_config1, self.btn_config)
        formLayout.addRow(self.progress)
        layout.addLayout(formLayout, 0)
        self.setLayout(layout)
        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()

    def update_plot(self):
        # Drop off the first y element, append a new one.
        self.canvas.axes.cla()  # Clear the canvas.
        self.canvas.axes.plot(self.xdata, self.ydata, lw=5, c='r', ls="dashed", label="top_LongShortAccountRatio")
        self.canvas.axes.plot(self.xdata2, self.ydata2, lw=5, c='r', label="global_LongShortAccountRatio")
        self.canvas.axes.plot(self.xdata1, self.ydata1, lw=5, c='g', label="top_LongShortPositionRatio")
        self.canvas.axes.plot(self.xdata3, self.ydata3, lw=5, c='b', label="buy_sell_volume_ratio")
        self.canvas.axes.axhline(y=0, lw=1, c='k')
        self.canvas.axes.set_ylabel(self.listcoin[0])
        # self.canvas.axes.set_xlabel(r'Time (multiple of interval)')
        self.canvas.axes.grid(linestyle='--', linewidth=0.5)
        self.canvas.axes.legend(loc=0)
        # self.canvas.axes.set_xticklabels(self.xdata, rotation=90)
        self.canvas.axes.tick_params(axis='x', labelrotation=90)
        # self.canvas.axes.set_ylim([np.min((self.ydata,self.ydata1,self.ydata2,self.ydata3)),\
        #                                     np.max((self.ydata,self.ydata1,self.ydata2,self.ydata3))])
        # Trigger the canvas to update and redraw.
        self.canvas.draw()
    
    def plot_pc1(self):
        self.btn_config1.setEnabled(False)   
        emit_dictionary = {}
        emit_dictionary['coin'] = []
        emit_dictionary['TimeFrame'] = []
        emit_dictionary['topLongShortAccountRatio'] = []
        emit_dictionary['topLongShortPositionRatio'] = []
        emit_dictionary['globalLongShortAccountRatio'] = []
        emit_dictionary['takerlongshortRatio'] = []
        count = 0
        for s in self.coins:
            trades1 = self.api.futures_topLongShortAccountRatio(symbol=s,
                                                                period=self.interval.currentText(),
                                                                limit=1)
            trades2 = self.api.futures_topLongShortPositionRatio(symbol=s,
                                                                 period=self.interval.currentText(),
                                                                 limit=1)
            trades3 = self.api.futures_globalLongShortAccountRatio(symbol=s,
                                                                   period=self.interval.currentText(),
                                                                   limit=1)
            trades4 = self.api.futures_takerlongshortRatio(symbol=s,
                                                           period=self.interval.currentText(),
                                                           limit=1)
            ### get order book data
            long_short_ratio1 = np.array([float(d['longShortRatio']) for d in trades1]) ## in CRYPTO
            long_short_ratio2 = np.array([float(d['longShortRatio']) for d in trades2]) ## in CRYPTO
            long_short_ratio3 = np.array([float(d['longShortRatio']) for d in trades3]) ## in CRYPTO
            buy_sell_ratio = np.array([float(d['buySellRatio']) for d in trades4]) ## in CRYPTO
            emit_dictionary['coin'].append(s)
            emit_dictionary['TimeFrame'].append(self.interval.currentText())
            emit_dictionary['topLongShortAccountRatio'].append(long_short_ratio1)
            emit_dictionary['topLongShortPositionRatio'].append(long_short_ratio2)
            emit_dictionary['globalLongShortAccountRatio'].append(long_short_ratio3)
            emit_dictionary['takerlongshortRatio'].append(buy_sell_ratio)
            count = count + 1
            self.progress.setValue(count)
            # TODO
        self.got_text.emit(emit_dictionary)
        self.btn_config1.setEnabled(True)
            
    def plot_pc(self):
        self.btn_config.setEnabled(False)
        candles_use = int(self.candles.text())
        self.listcoin = [self.cb_strategy1.currentText()]
        trades1 = self.api.futures_topLongShortAccountRatio(symbol=self.listcoin[0],
                                                            period=self.interval.currentText(),
                                                            limit=candles_use)
        trades2 = self.api.futures_topLongShortPositionRatio(symbol=self.listcoin[0],
                                                             period=self.interval.currentText(),
                                                             limit=candles_use)
        trades3 = self.api.futures_globalLongShortAccountRatio(symbol=self.listcoin[0],
                                                               period=self.interval.currentText(),
                                                               limit=candles_use)
        trades4 = self.api.futures_takerlongshortRatio(symbol=self.listcoin[0],
                                                       period=self.interval.currentText(),
                                                       limit=candles_use)
        ### get order book data
        long_short_ratio1 = np.array([float(d['longShortRatio']) for d in trades1]) ## in CRYPTO
        long_short_ratio2 = np.array([float(d['longShortRatio']) for d in trades2]) ## in CRYPTO
        long_short_ratio3 = np.array([float(d['longShortRatio']) for d in trades3]) ## in CRYPTO
        buy_sell_ratio = np.array([float(d['buySellRatio']) for d in trades4]) ## in CRYPTO
        
        long_short_ratio1ts = np.array([float(d['timestamp']) for d in trades1]) ## in CRYPTO
        long_short_ratio2ts = np.array([float(d['timestamp']) for d in trades2]) ## in CRYPTO
        long_short_ratio3ts = np.array([float(d['timestamp']) for d in trades3]) ## in CRYPTO
        buy_sell_ratiots = np.array([float(d['timestamp']) for d in trades4])
        
        date_x = []
        for i in range(len(long_short_ratio1ts)):
            date = datetime.datetime.fromtimestamp(long_short_ratio1ts[i] / 1e3)
            date_x.append(date.strftime("%Y-%m-%d %H-%M"))
        date_x1 = []
        for i in range(len(long_short_ratio2ts)):
            date = datetime.datetime.fromtimestamp(long_short_ratio2ts[i] / 1e3)
            date_x1.append(date.strftime("%Y-%m-%d %H-%M"))
        date_x2 = []
        for i in range(len(long_short_ratio3ts)):
            date = datetime.datetime.fromtimestamp(long_short_ratio3ts[i] / 1e3)
            date_x2.append(date.strftime("%Y-%m-%d %H-%M"))
        date_x3 = []
        for i in range(len(buy_sell_ratiots)):
            date = datetime.datetime.fromtimestamp(buy_sell_ratiots[i] / 1e3)
            date_x3.append(date.strftime("%Y-%m-%d %H-%M"))
            
        self.xdata  = date_x
        self.xdata1  = date_x1
        self.xdata2  = date_x2
        self.xdata3  = date_x3
        self.ydata  = long_short_ratio1
        self.ydata1  = long_short_ratio2
        self.ydata2  = long_short_ratio3
        self.ydata3  = buy_sell_ratio
        self.update_plot()
        self.btn_config.setEnabled(True)

class AnotherWindowConfig(QWidget):#QWidget QScrollArea
    got_password = QtCore.pyqtSignal(dict)
    
    def __init__(self, binance_api=None, state=0):
        super().__init__()
        
        app_icon = QtGui.QIcon()
        app_icon.addFile('logo.png', QtCore.QSize(16,16))
        self.setWindowIcon(app_icon)
        self.settings = QSettings("config_data","ConfigGUI")
        
        if binance_api == None:
            self.api = None
        else:
            self.api = binance_api

        # Binance module        
        self.enablebinance = QComboBox()
        self.enablebinance.addItem("True")
        self.enablebinance.addItem("False")
        self.keybinance = QLineEdit("binancekey") # 
        self.secretbinance = QLineEdit("binancesecret") #         
        self.keybinance.setText("0ho01k67q0KNSwAD8Ii0kcksi41ilHsAOEH3j15gBH9L6aRTZwH7PDRIXlOvOVRY")
        self.secretbinance.setText("GEdHDdyxEUlS1vzkM56sYyYUYdo9cvc75RP3PNpf9aTlRGJWkNlv1Jdh2bd76Gs2")
        # Telegram module
        self.enabletelegram = QComboBox()
        self.enabletelegram.addItem("True")
        self.enabletelegram.addItem("False")  
        self.botToken = QLineEdit("telegrambottoken") # 
        self.botchatid = QLineEdit("telegrambotid") #         
        self.botToken.setText("1354996834:AAHYrMPuIeJS6J_VXCQVcUa7RWtg0enVh8g")
        self.botchatid.setText("1185448229")
        
        # Live trade module (coins and blacklist)
        self.enabletrade = QComboBox()
        self.enabletrade.addItem("True")
        self.enabletrade.addItem("False")
        
        self.coinsinit = QLineEdit("coins") # 
        self.blacklist = QLineEdit("blacklist") # 
        self.coinsinit.setText("all")
        self.blacklist.setText("none")
        
        self.cb_priceanalysis = QComboBox()
        self.cb_priceanalysis.addItem("last_price")
        self.cb_priceanalysis.addItem("market")
        self.cb_priceanalysis.addItem("bid")
        self.cb_priceanalysis.addItem("ask")
        self.cb_priceanalysis.addItem("bid_ask")
        self.cb_priceanalysis.addItem("liquidation")

        self.cb_strategy1 = QLineEdit("candle")
        self.cb_strategy1.setText("70")
        self.cb_strategy2 = QLineEdit("candleinterval")
        self.cb_strategy2.setText("5")
        # order data
        self.investment = QLineEdit("investment") # stop_loss_spinbox
        self.leverage = QLineEdit("leverage") # stop_loss_spinbox
        self.addfunds = QLineEdit("addfunds") # stop_loss_spinbox
        self.investment.setText("30")
        self.leverage.setText("9")
        self.addfunds.setText("50")
        
        self.limtrade = QLineEdit("limtrades") # auto_sell_spinbox
        self.safetypercent = QLineEdit("safetydrop") # stop_loss_spinbox
        self.limtradecoin = QLineEdit("percoinlimtrades") # stop_loss_spinbox
        self.profit = QLineEdit("profit") # stop_loss_spinbox
        self.trailing = QLineEdit("ttp") # stop_loss_spinbox
        self.limtrade.setText("9")
        self.safetypercent.setText("4.5")
        self.limtradecoin.setText("4")
        self.profit.setText("1.4")
        self.trailing.setText("0.2")
        
        self.enableprofit = QComboBox()
        self.enableprofit.addItem("True")
        self.enableprofit.addItem("False")
        
        self.is_exchange_market = True
        self.cb_exchange = QComboBox()
        self.cb_exchange.addItem("Binance Futures")
        self.cb_exchange.addItem("Binance Spot")
        self.cb_exchange.currentIndexChanged.connect(self.selectionchange_exchange)
        
        self.cb_mode = QComboBox()
        self.cb_mode.addItem("Manual")
        self.cb_mode.addItem("Automatic")
        
        self.is_order_market = True
        self.cb_strategy = QComboBox()
        self.cb_strategy.addItem("LONG")
        self.cb_strategy.addItem("SHORT")
        self.cb_strategy.currentIndexChanged.connect(self.selectionchange_strategy)
        
        self.cb_strategybase = QComboBox()
        self.cb_strategybase.addItem("USDT")
        self.cb_strategybase.addItem("BTC")
        self.cb_strategybase.addItem("BNB")
        self.cb_strategybase.addItem("ETH")
        self.cb_strategybase.addItem("USD")
        self.cb_strategybase.addItem("EUR")
        
        # button for load config file
        self.btn_config = QPushButton('Apply new settings')
        self.btn_config.clicked.connect(self.read_config_dynamic)
        close_button = QPushButton("Cancel")
        close_button.clicked.connect(self.close)

        self.layout = QVBoxLayout() # QGridLayout()

        formLayout = QFormLayout()
        # formLayout.setVerticalSpacing(5)
        formLayout.addRow('BINANCE SETTINGS', QLineEdit().setReadOnly(True))
        formLayout.addRow('Exchange type:', self.cb_exchange)
        formLayout.addRow('Order strategy:', self.cb_strategy)
        formLayout.addRow('Base Currency:', self.cb_strategybase)
        formLayout.addRow('Enable BINANCE:', self.enablebinance)
        formLayout.addRow('BINANCE key:', self.keybinance)
        formLayout.addRow('BINANCE secret:', self.secretbinance)
        # formLayout.setVerticalSpacing(5)
        formLayout.addRow('TELEGRAM SETTINGS', QLineEdit().setReadOnly(True))
        formLayout.addRow('Enable Telegram:', self.enabletelegram)
        formLayout.addRow('Telegram bot token:', self.botToken)
        formLayout.addRow('Telegram chat id:', self.botchatid)
        # formLayout.setVerticalSpacing(5)
        formLayout.addRow('TRADE SETTINGS', QLineEdit().setReadOnly(True))
        formLayout.addRow('Live trade:', self.enabletrade)
        formLayout.addRow('Coins to trade:', self.coinsinit)
        formLayout.addRow('Blacklist:', self.blacklist)
        formLayout.addRow('Price analysis method:', self.cb_priceanalysis)
        formLayout.addRow('Time to analyze (in sec):', self.cb_strategy1)
        formLayout.addRow('Time interval (in sec):', self.cb_strategy2)
        formLayout.addRow('Maximum allowed trades (per account):', self.limtrade)
        formLayout.addRow('Maximum allowed trades (per coin for safety):', self.limtradecoin)
        # formLayout.setVerticalSpacing(5)
        formLayout.addRow('Trade mode:', self.cb_mode)
        formLayout.addRow('PROFIT SETTINGS',QLineEdit().setReadOnly(True))
        formLayout.addRow('Take profit:', self.enableprofit)
        formLayout.addRow('Closing profit (in %):', self.profit)
        formLayout.addRow('Trailing profit (in  %):', self.trailing)
        # formLayout.setVerticalSpacing(5)
        formLayout.addRow('ORDER SETTINGS',QLineEdit().setReadOnly(True))
        formLayout.addRow('Initial Investment (USDT):', self.investment)
        formLayout.addRow('Add funds (safety in USDT):', self.addfunds)
        formLayout.addRow('Safety drops (%):', self.safetypercent)
        formLayout.addRow('Leverage to use:', self.leverage)
        # formLayout.setVerticalSpacing(5)
        formLayout.addRow(close_button, self.btn_config)

        self.layout.addLayout(formLayout)
        self.setLayout(self.layout)

        if state > 0:
            self._gui_restore()

    def _gui_save(self):
      # Save geometry
        for name, obj in inspect.getmembers(self):
          # if type(obj) is QComboBox:  # this works similar to isinstance, but missed some field... not sure why?
          if isinstance(obj, QComboBox):
              index = obj.currentIndex()  # get current index from combobox
              text = obj.itemText(index)  # get the text for current index
              self.settings.setValue(name, text)  # save combobox selection to registry
          if isinstance(obj, QLineEdit):
              value = obj.text()
              self.settings.setValue(name, value)  # save ui values, so they can be restored next time
        self.settings.sync()
        
    def _gui_restore(self):
        # Restore geometry  
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                index = obj.currentIndex()  # get current region from combobox
                value = (self.settings.value(name))
                if value == "":
                    continue
                index = obj.findText(value)  # get the corresponding index for specified string in combobox
          
                if index == -1:  # add to list if not found
                      obj.insertItems(0, [value])
                      index = obj.findText(value)
                      obj.setCurrentIndex(index)
                else:
                      obj.setCurrentIndex(index)  # preselect a combobox value by index
            if isinstance(obj, QLineEdit):
                value = (self.settings.value(name))#.decode('utf-8'))  # get stored value from registry
                obj.setText(value)  # restore lineEditFile
        self.settings.sync()
    
    def selectionchange_exchange(self,i):        		
        if self.cb_exchange.currentText() == "Binance Futures":
            self.is_exchange_market = True
        elif self.cb_exchange.currentText() == "Binance Spot":
            self.is_exchange_market = False

    def selectionchange_strategy(self, i):
        if self.cb_strategy.currentText() == "LONG":
            self.is_order_market = True
        elif self.cb_strategy.currentText() == "SHORT":
            self.is_order_market = False 
    
    def read_config_dynamic(self):
        self._gui_save()
        
        self.text1 = []
        
        self.basecurrency = self.cb_strategybase.currentText()
        
        candlesP = int(self.cb_strategy1.text())
        interval = int(self.cb_strategy2.text())
        self.candlesP = [int(i) for i in range(1, candlesP, interval)]

        if self.api == None:
            if self.enablebinance.currentText() == "True":
                bin_key = self.keybinance.text()
                bin_secret = self.secretbinance.text()
                self.api = Client(bin_key, bin_secret)
            elif self.enablebinance.currentText() == "False":
                bin_key = self.keybinance.text()
                bin_secret = self.secretbinance.text()
                self.api = None
        else:
            bin_key = self.keybinance.text()
            bin_secret = self.secretbinance.text()
            
        if self.enabletelegram.currentText() == "True":
            self.enabledT = True
        elif self.enabletelegram.currentText() == "False":
            self.enabledT = False
                
        if self.enabletrade.currentText() == "True":
            self.live_trade = True
        elif self.enabletrade.currentText() == "False":
            self.live_trade = False
            
        if self.enableprofit.currentText() == "True":
            self.take_profit = "true"
        elif self.enableprofit.currentText() == "False":
            self.take_profit = "false"

        self.bot_chatID = self.botchatid.text()
        self.bot_token = self.botToken.text()
        self.lim_trades = int(self.limtrade.text())

        self.profit_percent = float(self.profit.text())
        self.take_profit_trailing = float(self.trailing.text())
        self.safety_trade_percent = float(self.safetypercent.text())
        self.usdt_addfunds = float(self.addfunds.text())
        self.usdt_invest = float(self.investment.text())
        self.leverage = int(self.leverage.text())
        
        ## get all list of coins in Binance futures:
        if self.is_exchange_market:
            info = self.api.futures_exchange_info()
        else:
            info = self.api.get_exchange_info()
        
        all_coins =  [x['symbol'] for x in info['symbols'] if x['symbol'][-len(self.basecurrency):] == self.basecurrency]
        
        self.lim_trades_per_coin = {}
        self.trade_per_coin = {}
        for i in all_coins:
            self.lim_trades_per_coin[i] = int(self.limtradecoin.text())
            self.trade_per_coin[i] = int(0)
            
        if self.take_profit_trailing > 0.0:
            self.ttp = 'true'
        else:
            self.ttp = 'false'

        ## verify how many coins are provided
        if 'all' in self.coinsinit.text():
            self.coins = all_coins
        else:
            self.coins = [i for i in self.coinsinit.text().split(',')]
        ## verify how many coins are blacklisted    
        black_list = self.blacklist.text().split(",")
        if 'none' in black_list:
            self.black_list = ['none']
        else:
            self.black_list = [i for i in black_list]
            msg = ''
            for i in self.black_list:
                msg = msg + '; '+i
            self.text1.append("The following pair(s) are backlisted: "+msg)
            
        msg = ''
        for i in self.coins:
            if i in self.black_list:
                continue
            msg = msg + ', '+i
            
        self.text1.append("The following pair(s) (with base currency of "+self.basecurrency+\
                          ") will be traded (provided their volume is above given threshold) "+msg)
        if not 'none' in self.black_list:
            for i in self.black_list:
                if i in self.coins:
                    self.coins.remove(i)
        self.text1.append("Bot configuration loaded successfully")

        # create a dictionary and emit the signal
        emit_dictionary = {"binance_client": self.api,
                            "binance_key": bin_key,
                            "binance_secret": bin_secret,
                            "text1": self.text1,
                            "enabledT": self.enabledT,
                            "live_trade": self.live_trade,
                            "take_profit": self.take_profit,
                            "bot_chatID": self.bot_chatID,
                            "bot_token": self.bot_token,
                            "ttp": self.ttp,
                            "lim_trades": self.lim_trades,
                            "profit_percent": self.profit_percent,
                            "take_profit_trailing": self.take_profit_trailing,
                            "safety_trade_percent": self.safety_trade_percent,
                            "usdt_addfunds": self.usdt_addfunds,
                            "usdt_invest": self.usdt_invest,
                            "leverage": self.leverage,
                            "lim_trades_per_coin": self.lim_trades_per_coin,
                            "trade_per_coin": self.trade_per_coin,
                            "coins": self.coins,
                            "black_list": self.black_list,
                            "price_analysis_mode": self.cb_priceanalysis.currentText(),
                            "candlesP": self.candlesP,
                            "is_exchange_market": self.is_exchange_market,
                            "is_order_market": self.is_order_market,
                            "basecurrency": self.basecurrency,
                            "mode_analysis": self.cb_mode.currentText()}
        self.got_password.emit(emit_dictionary)
        self.close() # close the window
        