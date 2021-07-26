# -*- coding: utf-8 -*-
"""
Created on Sun Jul 19 06:54:04 2020
@author: Ravi raj purohit
## TARNSFERRED TO PYQT GUI 
"""
import time, datetime
import requests#, threading
import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow,\
                            QPushButton, QWidget, QFormLayout, \
                            QLineEdit, QToolBar, QStatusBar, \
                            QVBoxLayout, QTextEdit
import math
from twisted.internet import reactor
import numpy as np
import os
import _pickle as cPickle

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

Logo = resource_path("logo.png")
#1 EXTERNAL LIBRARIES
from binance_api import BinanceSocketManager
from binance_api import BinanceAPIException
from lib_pump_dump import AnotherWindow, AnotherWindowDynamicBTC,\
                            AnotherWindowDynamicFS, AnotherWindowDynamic, \
                            AnotherWindowConfig, AnotherWindowpnl, AnotherWindowtrade
BOT_START_TIME = time.time() #in ms
frame_title = "Binance bot- Alpha"  
#%% POST TREATMENT MODULE
class currency_container:
    def __init__(self, currencyArray, candle_len=10, mode = 'last_price'): 
        # v is quote volue (BTC), q is base value (USDT)
        self.symbol = currencyArray['s']
        initial_timestamp = time.time()
        self.time_stamp = initial_timestamp
        self.time_stamp_reset = initial_timestamp
        self.volume24hr = 0.0

        if mode == 'market':
            key = 'p'
        elif mode == 'last_price':
            key = 'c'
            keyV = "v"
            self.volume24hr = float(currencyArray[keyV])
        elif mode == 'bid':
            key = 'b'
        elif mode == 'ask':
            key = 'a'
        self.bid_price = float(currencyArray[key])
        self.price_time = [1.0 * float(currencyArray[key]) for _ in range(candle_len)]

        if mode == 'bid_ask':
            self.bid_price = (float(currencyArray['b']) + float(currencyArray['a'])) /2.
            self.price_time = [1.0 * (float(currencyArray['b']) + float(currencyArray['a'])) /2. for _ in range(candle_len)]
        self.time_stamp_period = [1.0 * initial_timestamp for _ in range(candle_len)]
        ### single price changes for different candles
        self.percent_chgsP = 0.0
        self.profit_percentP = 0.0

class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)
        QMainWindow.__init__(self)
        
        app_icon = QtGui.QIcon()
        app_icon.addFile('logo.png', QtCore.QSize(16,16))
        self.setWindowIcon(app_icon)
        
        self.nb_trades = 0
        self.list_of_trades = []
        try:
            with open("active_trade.pickle", "rb") as input_file:
                self.trades_completed = cPickle.load(input_file)
        except:
            self.trades_completed = {}
        # TODO dump trades_completed and load to keep track
        self.new_list = {}
        self.indicator = 'none'
        self.enabledT = False
        self.api = None
        self.state = 0
        self._sockets = {}
        self.popup_cnt = 0
        self.popup_cnt1 = 0
        self.running = False
        
        self.setWindowTitle(frame_title)
        # self._createMenu()
        self._createToolBar()
        self._createStatusBar()
        # Add box layout, add table to box layout and add box layout to widget
        self.layout = QVBoxLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.layout)
        self._createDisplay() ## display screen
        self.setDisplayText(frame_title)
        self.setDisplayText("GUI initialized! \nPlease configure bot settings first\n")
        self._formLayout() ## buttons and layout
        self.popups = []
        
        self.timer1temp = QtCore.QTimer()
        self.timer1temp.setInterval(int(5000))
        self.timer1temp.timeout.connect(self.update_)
        self.timer1temp.start()
    
    def update_(self,):
        with open("active_trade.pickle", "wb") as output_file:
            cPickle.dump(self.trades_completed, output_file)
    
    def closeEvent(self, event):
        # Return stdout to defaults.
        try:
            reactor.stop()
            self.on_manual_sell()
        except:
            pass
        self.close
        QApplication.closeAllWindows()
        super().closeEvent(event)
        
    def _createDisplay(self):
        """Create the display."""
        # Create the display widget
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        # Add the display to the general layout
        self.layout.addWidget(self.display)

    def setDisplayText(self, text):
        self.display.append('%s'%text)
        self.display.moveCursor(QtGui.QTextCursor.End)
        self.display.setFocus()

    def _createMenu(self):
        self.menu = self.menuBar().addMenu("&Menu")
        self.menu.addAction('&Exit', self.close)

    def _createToolBar(self):
        self.tools = QToolBar()
        self.addToolBar(self.tools)
        self.trialtoolbar1 = self.tools.addAction('Price change plot', self.show_new_window)
        self.trialtoolbar2 = self.tools.addAction('Dynamic plot', self.show_new_window_dynamic)
        self.trialtoolbar4 = self.tools.addAction('Futures stat', self.show_new_window_dynamicFS)
        self.trialtoolbar3 = self.tools.addAction('Stats (several exchange)', self.show_new_window_dynamicBTC)
        self.trialtoolbar1.setEnabled(False)
        self.trialtoolbar2.setEnabled(False)
        self.trialtoolbar4.setEnabled(False)
        # self.trialtoolbar31.setEnabled(False)
    
    def show_new_window_nimpl(self):
        self.write_to_console("Functions not available as of now; in development", to_push=1)
        
    def show_new_windowtrade(self, trades_completed):
        w9 = AnotherWindowtrade(self.api, self.exchange, trades_completed)
        w9.show()
        self.popups.append(w9)
        
    def show_new_window(self):
        w = AnotherWindow(self.api, self.exchange)
        w.show()
        self.popups.append(w)
        
    def show_new_windowpnl(self):
        w123 = AnotherWindowpnl(self.api, self.exchange, BOT_START_TIME)
        w123.got_signal_socket.connect(self.postprocesspnl)
        w123.show()
        self.popups.append(w123)
        
    def show_new_window_dynamicBTC(self):
        w165 = AnotherWindowDynamicBTC(self.setDisplayText)
        w165.got_signal.connect(self.postprocessliq)
        w165.show()
        self.popups.append(w165)
    
    def show_new_window_dynamicFS(self):
        w1 = AnotherWindowDynamicFS(self.api)
        w1.got_text.connect(self.postprocessFS)
        w1.show()
        self.popups.append(w1)
        
    def show_new_window_dynamic(self):
        w175 = AnotherWindowDynamic(self.api, self.exchange)
        w175.show()
        self.popups.append(w175)
    
    def show_new_window_config(self):
        w2 = AnotherWindowConfig(self.api, state=self.state)
        w2.got_password.connect(self.postprocess)
        w2.show()
        self.state = self.state +1
        self.popups.append(w2)
    
    def postprocessFS(self, emit_dict):
        coins_ = np.array(emit_dict["coin"]).flatten()
        timeframe_ = np.array(emit_dict['TimeFrame']).flatten()
        trades1 = np.array(emit_dict['topLongShortAccountRatio']).flatten()
        trades2 = np.array(emit_dict['topLongShortPositionRatio']).flatten()
        trades3 = np.array(emit_dict['globalLongShortAccountRatio']).flatten()
        trades4 = np.array(emit_dict['takerlongshortRatio']).flatten()
        # every 5min and 1hour
        ind_ = trades1.argsort()[-5:][::-1]
        for i in ind_:
            line = coins_[i]+" has HIGHEST Long/Short ACCOUNT ratio in "+\
                                        timeframe_[0]+" timeframe with "+\
                                        str(trades1[i])
            self.write_to_console(line, to_push=1)
        self.write_to_console("\n", to_push=1)

        ind_ = trades2.argsort()[-5:][::-1]
        for i in ind_:
            line = coins_[i]+\
                                    " has HIGHEST Long/Short POSITION ratio in "+\
                                        timeframe_[0]+" timeframe with "+\
                                        str(trades2[i])
            self.write_to_console(line, to_push=1)
        self.write_to_console("\n", to_push=1)    

        ind_ = trades3.argsort()[-5:][::-1]
        for i in ind_:
            line = coins_[i]+\
                                    " has HIGHEST Long/Short GLOBAL ACCOUNT ratio in "+\
                                        timeframe_[0]+" timeframe with "+\
                                        str(trades3[i])
            self.write_to_console(line, to_push=1)
        self.write_to_console("\n", to_push=1)
        
        ind_ = trades4.argsort()[-5:][::-1]
        for i in ind_:
            line = coins_[i]+\
                                    " has HIGHEST BUY/SELL volume ratio in "+\
                                        timeframe_[0]+" timeframe with "+\
                                        str(trades4[i])
            self.write_to_console(line, to_push=1)
        self.write_to_console("\n", to_push=1)
            
    def postprocessliq(self, emit_dict):
        self.lim_trades = self.lim_trades + emit_dict["limtrades"]
        self.text1 = ["adding a shift in the market based on BTC movements"]
        self.usdt_addfunds = emit_dict["safety"]
        self.usdt_invest = emit_dict["investment"]
        if emit_dict["direction"] == "LONG":
            self.indicator = 'long'
            self.cb_strategy.setText("LONG")
        else:
            self.indicator = 'short'
            self.cb_strategy.setText("SHORT")
        self.cb_strategy.setReadOnly(True)
        # print status
        for line in self.text1:
            self.write_to_console(line, to_push=1)
    
    def postprocesspnl(self, emit_dict):
        symbol = emit_dict["signal"]
        if symbol == "SOS":
            tempp = self.api.futures_get_open_orders()
            ss = []
            for j in tempp:
                ss.append(j['symbol'])
            ss = np.unique(ss)    
            for i in ss:
                try:
                    _  = self.api.futures_cancel_all_open_orders(symbol=i)
                except:
                    pass
            line = "SOS Liquidation approaching; cancelling all open orders"
            self.write_to_console(line, to_push=1)
        else:
            try:
                _  = self.api.futures_cancel_all_open_orders(symbol=symbol)
            except:
                line = "No open orders exists for "+symbol
                self.write_to_console(line, to_push=1)
            
            try:
                self.trades_completed[symbol]["trade_status"] = "finished"
            except:
                line = symbol + " doesn't exist in trade database; not managed by bot"
                self.write_to_console(line, to_push=1)
            self.update_()
            self.stop_ticker_symbol(symbol)  
    
    def postprocess(self, emit_dict):
        self.text1 = emit_dict["text1"]
        self.live_trade = emit_dict["live_trade"]
        self.take_profit = emit_dict["take_profit"]
        self.enabledT = emit_dict["enabledT"]
        self.bot_chatID = emit_dict["bot_chatID"]
        self.bot_token = emit_dict["bot_token"]
        self.ttp = emit_dict["ttp"]
        self.lim_trades = emit_dict["lim_trades"]
        self.profit_percent = emit_dict["profit_percent"]
        self.take_profit_trailing = emit_dict["take_profit_trailing"]
        self.safety_trade_percent = emit_dict["safety_trade_percent"]
        self.usdt_addfunds = emit_dict["usdt_addfunds"]
        self.usdt_invest = emit_dict["usdt_invest"]
        self.leverage = emit_dict["leverage"]
        self.lim_trades_per_coin = emit_dict["lim_trades_per_coin"]
        self.trade_per_coin = emit_dict["trade_per_coin"]
        self.coins = emit_dict["coins"]
        self.black_list = emit_dict["black_list"]
        self.api = emit_dict["binance_client"]
        bin_key = emit_dict["binance_key"]
        bin_secret = emit_dict["binance_secret"]
        self.price_analysis_mode = emit_dict["price_analysis_mode"]
        self.candlesP = emit_dict["candlesP"]
        self.is_exchange_market = emit_dict["is_exchange_market"]
        self.is_order_market = emit_dict["is_order_market"]
        self.basecurrency = emit_dict["basecurrency"] 
        self.mode_analysis = emit_dict["mode_analysis"] 
        
        if self.mode_analysis == "Automatic":
            self.price_pd.setEnabled(False)
            self.price_dp.setEnabled(False)
        else:
            self.price_pd.setEnabled(True)
            self.price_dp.setEnabled(True)
            
        if self.is_exchange_market:
            self.exchange = "FUTURES"
            if self.is_order_market:
                self.indicator = 'long'
            else:
                self.indicator = 'short'
            self.cb_exchange.setText("Binance Futures")
        else:
            self.exchange = "SPOT"
            self.leverage = 1
            self.indicator = 'long' # only long is allowed in spot
            self.cb_exchange.setText("Binance Spot")
        self.cb_exchange.setReadOnly(True)
        
        if self.is_order_market:
            self.cb_strategy.setText("LONG")
        else:
            self.cb_strategy.setText("SHORT")
        self.cb_strategy.setReadOnly(True)
        
        self.base_currencys.setText(self.basecurrency)
        self.base_currencys.setReadOnly(True)
        
        self.temp01.setText(str(self.live_trade))
        self.temp01.setReadOnly(True)
        self.temp02.setText(str(self.enabledT))
        self.temp02.setReadOnly(True)
        
        if bin_key != None and bin_secret != None:
            self.api_key_entry.setText(bin_key)
            self.api_key_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self.api_key_entry.setReadOnly(True)
            self.api_secret_entry.setText(bin_secret)
            self.api_secret_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self.api_secret_entry.setReadOnly(True)
        # print status
        for line in self.text1:
            self.write_to_console(line, to_push=1)
            
    def _createStatusBar(self):
        self.status = QStatusBar()
        self.status.showMessage("Bot status will be shown here")
        self.setStatusBar(self.status)

    def _formLayout(self):
        self.formLayout = QFormLayout()
        
        self.temp01 = QLineEdit()
        self.temp02 = QLineEdit()
        
        self.cb_exchange = QLineEdit()
        self.cb_strategy = QLineEdit()
        self.base_currencys = QLineEdit()
        # button for binance exchange connection
        self.btn = QPushButton('Connect to Exchange')
        self.btn.clicked.connect(self.on_connect_api)
        # self.btn.setEnabled(False)
        
        # button for bot start
        self.btn_bstart = QPushButton('Start bot')
        self.btn_bstart.clicked.connect(self.on_pump)
        # button for bot stop
        self.btn_bstop = QPushButton('Stop bot')
        self.btn_bstop.clicked.connect(self.on_manual_sell)
        self.btn_bstop.setEnabled(False)
        
        self.btn_bstoptp = QPushButton('Stop TP')
        self.btn_bstoptp.clicked.connect(self.stop_tp_sockets)
        self.btn_bstoptp.setEnabled(False)

        self.btn_config_trial = QPushButton('Configure bot settings (static and dynamic)')
        self.btn_config_trial.clicked.connect(self.show_new_window_config)
        ## api key and secret Qline
        self.api_key_entry = QLineEdit()
        self.api_secret_entry = QLineEdit()
        self.price_pd = QLineEdit() # auto_sell_spinbox
        self.price_dp = QLineEdit() # stop_loss_spinbox
        self.price_pd.setText("1.2")
        self.price_dp.setText("10")
        
        self.formLayout.addRow(self.btn_config_trial)
        self.formLayout.addRow('Exchange type:', self.cb_exchange)
        self.formLayout.addRow('Order strategy:', self.cb_strategy)
        self.formLayout.addRow('Trading currency:', self.base_currencys)
        self.formLayout.addRow('Exchange API key:', self.api_key_entry)
        self.formLayout.addRow('Exchange API secret:', self.api_secret_entry)
        self.formLayout.addRow('Live trade:', self.temp01)
        self.formLayout.addRow('Telegram:', self.temp02)
        self.formLayout.addRow('', self.btn)
        self.formLayout.addRow('Price change for PUMP/DUMP (%):', self.price_pd)
        self.formLayout.addRow('Price change for DUMP/PUMP (%):', self.price_dp)
        self.formLayout.addRow(self.btn_bstop, self.btn_bstart)
        self.formLayout.addRow("stop trailing profit socket", self.btn_bstoptp)
        self.layout.addLayout(self.formLayout)
        
    # BOT FUNCTIONS
    def stop_tp_sockets(self):
        try:
            for symbol in self._sockets:
                bm61 = self._sockets[symbol]["socketmanager"]
                key61 = self._sockets[symbol]["key"]
                bm61.stop_socket(key61)
                bm61.close()
                self._sockets[symbol]["socketmanager"] = ""
                self._sockets[symbol]["key"] = ""
                self.write_to_console("Socket closed for "+symbol, to_push=1)
        except:
            self.write_to_console("Socket is empty", to_push=1)
        
    def write_to_console(self, line, to_push=0):
        self.setDisplayText(str(line.encode('utf-8','ignore'),errors='ignore'))
        if self.enabledT and to_push==1:
            percent=str(line.encode('utf-8','ignore'),errors='ignore')
            send_text='https://api.telegram.org/bot' + self.bot_token + '/sendMessage?chat_id=' + self.bot_chatID + '&parse_mode=Markdown&text=' + percent
            requests.get(send_text)
    
    def precision_and_scale(self, x):
        max_digits = 14
        int_part = int(abs(x))
        magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
        if magnitude >= max_digits:
            return (magnitude, 0)
        frac_part = abs(x) - int_part
        multiplier = 10 ** (max_digits - magnitude)
        frac_digits = multiplier + int(multiplier * frac_part + 0.5)
        while frac_digits % 10 == 0:
            frac_digits /= 10
        scale = int(math.log10(frac_digits))
        return scale
    
    def on_connect_api(self):
        try:
            if self.api == None:
                self.write_to_console("Missing API info. Load config first", to_push=1) 
                return

            if self.is_exchange_market:
                info = self.api.futures_exchange_info()
                ## QUANTITY precision for Trailing stop market orders
                self.price_precision = {}
                self.quantity_precision = {}
                for s in info['symbols']:        
                    symbol = s['symbol']
                    self.quantity_precision[symbol] = s["quantityPrecision"]
                    for jj in s["filters"]:
                        if jj["filterType"] == "PRICE_FILTER":
                            self.price_precision[symbol] = self.precision_and_scale(float(jj["tickSize"]))
            else:
                info = self.api.get_exchange_info()
                ## QUANTITY precision for Trailing stop market orders
                self.price_precision = {}
                self.quantity_precision = {}
                for s in info['symbols']:        
                    symbol = s['symbol']
                    for ij in s['filters']:
                        if ij['filterType'] == "PRICE_FILTER":
                            self.price_precision[symbol] = self.precision_and_scale(float(ij["minPrice"]))
                        if ij['filterType'] == "LOT_SIZE":                        
                            self.quantity_precision[symbol] = self.precision_and_scale(float(ij["minQty"]))
                            
            if self.mode_analysis == "Automatic":
                self.price_pd.setEnabled(False)
                self.price_dp.setEnabled(False)
            else:
                self.price_pd.setEnabled(True)
                self.price_dp.setEnabled(True)
                
            self.btn_bstart.setEnabled(True)
            self.btn_bstop.setEnabled(True)
            self.btn.setEnabled(False)
            self.write_to_console("Connected to "+self.exchange+" API successfully.", to_push=1)
            self.write_to_console("Plots are available now", to_push=1)
            self.trialtoolbar1.setEnabled(True)
            self.trialtoolbar2.setEnabled(True)
            self.trialtoolbar4.setEnabled(True)
            # self.trialtoolbar31.setEnabled(True)
            if self.popup_cnt == 0:
                self.show_new_windowpnl()
                self.show_new_windowtrade(self.trades_completed)
                self.popup_cnt = 1
        except:
            self.write_to_console("Missing API info.", to_push=1)   
        ## print trade stats in table
        
    def disable_pre_pump_options(self,):
        self.price_pd.setEnabled(False)
        self.price_dp.setEnabled(False)
        self.btn_bstart.setEnabled(False)
        self.btn_bstop.setEnabled(True)
        self.btn.setEnabled(False)
        
    def enable_pump_options(self,):
        self.price_pd.setEnabled(True)
        self.price_dp.setEnabled(True)
        self.btn_bstart.setEnabled(True)
        self.btn_bstop.setEnabled(False)
        self.btn.setEnabled(True)

    #### Button Behaviour ####
    def on_pump(self):
        ct = time.time()
        now = datetime.datetime.fromtimestamp(ct)
        c_time = now.strftime("%Y-%m-%d_%H-%M-%S")
        # c_time1 = now.strftime("%Y-%m-%d")
        self.filename_ = "trade_logs.txt"
        with open(self.filename_, "a") as myfile:
            myfile.write("# New trade logs @ "+ c_time +" \n")
        try:
            if self.popup_cnt1 == 0:
                self.popup_cnt1 = 1
                if self.is_exchange_market:
                    ### Checking to see if new threads for existing trades needed
                    if self.trades_completed != {}:
                        ## verify if position open
                        temp  = self.api.futures_position_information()
                        coins_symbol = [temp[i1]['symbol'] for i1 in range(len(temp)) \
                                        if float(temp[i1]['entryPrice']) != 0.0]
                            
                        for alt_coin in self.trades_completed:
                            if (self.trades_completed[alt_coin]["trade_status"] == "running") \
                                and (alt_coin in coins_symbol):
                                self.write_to_console("Retrieving previous trade for "+alt_coin, to_push=1)
                                ## start a socket manager to keep eye on the price movement
                                bm1 = BinanceSocketManager(self.api)
                                conn = bm1.start_symbol_mark_price_socket(symbol=alt_coin, \
                                                                          callback=self.sell_trailing_profit, fast=True)
                                self._sockets[alt_coin] = {"symbol": alt_coin, "socketmanager": bm1, "key": conn}
                                bm1.start()
                                time.sleep(.01)
                                self.write_to_console("Price socket started for "+alt_coin)
                                
                            if (self.trades_completed[alt_coin]["trade_status"] == "running") \
                                and (alt_coin not in coins_symbol):
                                _  = self.api.futures_cancel_all_open_orders(symbol=alt_coin)
                                self.trades_completed[alt_coin]["trade_status"] = "finished"
                                
                        self.write_to_console("Checking if any independent open orders are present.", to_push=1)
                        tempp = self.api.futures_get_open_orders()
                        ss = []
                        for j in tempp:
                            ss.append(j['symbol'])
                        ss = np.unique(ss)    
                        for i in ss:
                            if i not in coins_symbol:
                                _  = self.api.futures_cancel_all_open_orders(symbol=i)
                                line = "cancelling all open orders for "+i
                                self.write_to_console(line, to_push=1)
                    else:
                        self.write_to_console("No active trade found.", to_push=1)
                    
            self.disable_pre_pump_options()            
           
            try:
                percent = float(self.price_pd.text())
                percent1 = float(self.price_dp.text())
            except:
                self.write_to_console("Please fill the price change in numbers", to_push=1)
                return
            
            if (percent <= 0.0) or (percent1 <= 0.0):
                self.write_to_console("Price change percentage cannot be less than 0.", to_push=1)
                self.enable_pump_options()
                return
    
            self.write_to_console("Price based analysis started.", to_push=1)
            ### connect binance websocket
            self.bm = BinanceSocketManager(self.api)
            if (self.price_analysis_mode == "market"):
                self.conn_key = self.bm.start_all_mark_price_socket(self.process_message) #start_miniticker_socket
                self.btn_bstoptp.setEnabled(True)
            elif (self.price_analysis_mode == "last_price"):
                self.conn_key = self.bm.start_ticker_socket(self.process_message) #start_miniticker_socket
                self.btn_bstoptp.setEnabled(True)
            # elif (self.price_analysis_mode == "liquidation"):
            #     self.conn_key = self.bm.start_ticker_socket_allliq(self.process_message_liq)
            else:
                self.write_to_console("Not yet implemented, select last_price or market for price analysis in config!", to_push=1)
            self.bm.start()
            time.sleep(.01)
            self.write_to_console("Initialised successfully!", to_push=1)
            self.status.showMessage("Bot is running now!")
            
        except AttributeError:
            self.write_to_console("You need to connect to Binance before starting.", to_push=1)
            return
    
    def process_message_liq(self, msg): # TODO
        # sample stream OUTPUT
        # {'e': 'forceOrder', 'E': 1619351660699, 'o':
        # {'s': 'XRPUSDT', 'S': 'BUY', 'o': 'LIMIT',
        # 'f': 'IOC', 'q': '4386.3', 'p': '1.0775',
        # 'ap': '1.0711', 'X': 'FILLED',
        # 'l': '1536.7', 'z': '4386.3', 'T': 1619351660692}}
        print(msg)
    
    def on_manual_sell(self):
        self.enable_pump_options()
        self.write_to_console("Stopping the P and D detector for Price analysis", to_push=1)
        # reactor.stop()
        try: 
            self.bm.stop_socket(self.conn_key)
            self.bm.close()
        except:
            self.write_to_console("No socket is open.", to_push=1)
        self.status.showMessage("Bot is stopped now!")

    def limit_safety(self, alt_coin, units_old, statement, indicator_=None):
          statement.append("Placing Limit Safety Orders for "+alt_coin+"\n")
          # time.sleep(2)
          ## sleep for some seconds for the trade to be created
          leverage = self.leverage
          coin_trade = True
          merge_runningv1 = True
          
          loop_count = 0 ##0 to avoid forever loop
         
          while merge_runningv1:
              loop_count = loop_count + 1              
              if loop_count > 3:
                  merge_runningv1 = False

              try:
                  temp  = self.api.futures_position_information()
                  entry_price = [float(temp[i1]['entryPrice']) for i1 in range(len(temp)) \
                               if temp[i1]['symbol'] == alt_coin]
                  entry_price = entry_price[0]
              except:
                  statement.append("Error getting the entry price from Binance, trying again in 10seconds")
                  entry_price = 0.0
                  time.sleep(10)
                  continue

              if (coin_trade) and (entry_price > 0.0):
                  tab_cnt = 0                
                  ## scaled place safety order
                  if self.lim_trades_per_coin[alt_coin] > 1:
                      linspace = [self.usdt_invest + float(x)/(self.lim_trades_per_coin[alt_coin]-1)*\
                                  (self.usdt_addfunds-self.usdt_invest) \
                                      for x in range(self.lim_trades_per_coin[alt_coin])]
                  else:
                      linspace = [self.usdt_addfunds]
                 
                  nb_units = []
                  price_enter = []
                  units_price = []
                  ## first entry
                  nb_units.append(units_old)
                  price_enter.append(entry_price)
                  units_price.append(units_old*entry_price)  
                  for i in range(self.lim_trades_per_coin[alt_coin]):
                      if indicator_ == 'long':
                          entry_price1 = entry_price * (1 - ((self.safety_trade_percent/100.)*(i+1)))
                          type_ = "BUY"
                      elif indicator_ == 'short':
                          entry_price1 = entry_price * (1 + ((self.safety_trade_percent/100.)*(i+1)))
                          type_ = "SELL"
                     
                      if self.price_precision[alt_coin] == 0:
                          entry_price1 = int(entry_price1)
                      else:
                          entry_price1 = round(entry_price1, self.price_precision[alt_coin]) 
                      ### scaled safety trades
                      units = float(linspace[i]) / (entry_price1 / leverage)
                     
                      if self.quantity_precision[alt_coin] == 0:
                          units = int(units)
                      else:
                          units = round(units, self.quantity_precision[alt_coin]) 
                     
                      nb_units.append(units)
                      price_enter.append(entry_price1)
                      units_price.append(units*entry_price1)
                      
                      try:
                          _ = self.api.futures_create_order(symbol=alt_coin, side=type_, type="LIMIT", \
                                                            positionSide="BOTH", \
                                                            timeInForce="GTC", quantity=units, price=entry_price1)
                          tab_cnt = tab_cnt + 1
                      except:
                          statement.append("error during safety order placement \n")

                  if int(tab_cnt) == self.lim_trades_per_coin[alt_coin]:
                      self.trade_per_coin[alt_coin] = self.trade_per_coin[alt_coin] + 1
                      merge_runningv1 = False
                      coin_trade = False
                  else:
                      coin_trade = False
                      statement.append("Unkown error occured \n")
                      return statement
                     
                  qsd = ''
                  dsq = ''
                  for num, st in enumerate(linspace):
                      qsd = qsd+str(st)+'; '
                      u = nb_units[:num+2]
                      # p = price_enter[:num+2]
                      up = units_price[:num+2]
                      pr = sum(up)/sum(u) # sum(u*p)/sum(u)
                      dsq = dsq+str(round(pr,6))+'; '
                  statement.append("The entry price for "+alt_coin +" is "+str(entry_price)+"\n")
                  statement.append("Safety funds are added (with leverage of "+str(leverage)+\
                                   ") in the following order: "+qsd+"\n")

                  statement.append("The safety trades will bring the entry price for "+alt_coin +" to: "+dsq+"\n")
                  statement.append("Funds added to existing trade for "+alt_coin+"\n")
          statement.append("Exiting the sell Thread for "+alt_coin+"\n")
          return statement
      
    def _binance_buy_sell(self, alt_coin='BTCUSDT', current_value=0.0, \
                          statement=None, indicator_=None, ppercent=None):
        leverage = self.leverage
        ## we should probably add 0.5% price to the current price to account for a dump 
        try:
            if self.is_exchange_market:
                ## Making sure the trade being opened is CROSSED margin type
                temp_var = self.api.futures_change_margin_type(symbol=alt_coin, marginType="CROSSED")
                if temp_var['msg'] == 'success':
                    statement.append("Successfully updated the margin type to CROSSED for "+alt_coin+"\n")
        except:
            statement.append("Margin type is already set to CROSSED for "+alt_coin+"\n")
        ## change leverage of the coin
        
        try:
            if self.is_exchange_market:
                ## Making sure the trade being opened is CROSSED margin type
                temp_var = self.api.futures_change_leverage(symbol=alt_coin, leverage=int(leverage))
                statement.append("Successfully updated the leverage to "+str(temp_var["leverage"])+" for "+alt_coin+"\n")
        except:
            statement.append("Error during leverage setting for "+alt_coin+". PLEASE CHANGE MANUALLY \n")
        
        
        units = self.usdt_invest / (current_value / leverage)
        
        if self.quantity_precision[alt_coin] == 0:
            units = int(units)
        else:
            units = round(units, self.quantity_precision[alt_coin]) 
        
        if indicator_ == 'long':
            type_ = "BUY"
        elif indicator_ == 'short':
            type_ = "SELL"
        
        try: ## POSTING ORDERS IN BINANCE DIRECTLY
            if self.is_exchange_market:
                # Post order in futures
                data = self.api.futures_create_order(symbol=alt_coin, type="MARKET", quantity=units, \
                                                      positionSide="BOTH", side=type_)
                time.sleep(2)
                ## posting also limit safety orders for Futures
                if self.lim_trades_per_coin[alt_coin] > 0:
                    statement = self.limit_safety(alt_coin, units, statement, indicator_)
            else:
                # Post order in SPOT
                data = self.api.create_order(symbol=alt_coin, type="MARKET", quantity=units, \
                                                      side=type_)
        except BinanceAPIException as e:
            statement.append("Error in the Binance module while posting trades for "+alt_coin+"\n")
            statement.append(f"(Code {e.status_code}) {e.message}")
            return statement
        # time.sleep(2)
        
        # get order ID status    
        temp  = self.api.futures_position_information()
        entry_price_ = [[float(temp[i1]['entryPrice']),float(temp[i1]['positionAmt'])] \
                        for i1 in range(len(temp)) if temp[i1]['symbol'] == alt_coin]
        data["entry_price"] = entry_price_[0][0]
        data["entry_amount"] = entry_price_[0][1]
        data["units_total"] = entry_price_[0][1]
        
        if indicator_ == 'long':
            if ppercent == 0.0 or ppercent == None:
                sell_value = entry_price_[0][0] * (1 + (self.profit_percent/100.))
            else:
                sell_value = entry_price_[0][0] * (1 + (ppercent/100.))
            type_ = "SELL"
        elif indicator_ == 'short':
            if ppercent == 0.0 or ppercent == None:
                sell_value = entry_price_[0][0] * (1 - (self.profit_percent/100.))
            else:
                sell_value = entry_price_[0][0] * (1 - (ppercent/100.))
            type_ = "BUY"
            
        data["sell_value"] = sell_value
        data["type_"] = type_
        data["trade_time"] = time.time()
        data["count"] = 0
        data["ttp_activated"] = False
        data["old_price"] = 1e10
        data["trade_status"] = "running"
        data["safety_count"] = self.lim_trades_per_coin[alt_coin]
        
        self.trades_completed[alt_coin] = data
        self.update_()
        
        statement.append("New trade created in Binance for "+alt_coin+"\n")
        ## start a socket manager to keep eye on the price movement
        bm21 = BinanceSocketManager(self.api)
        conn21 = bm21.start_symbol_mark_price_socket(symbol=alt_coin, callback=self.sell_trailing_profit, fast=True)
        self._sockets[alt_coin] = {"symbol": alt_coin, "socketmanager": bm21, "key": conn21}
        bm21.start()
        time.sleep(.01)
        statement.append("Price socket started for "+alt_coin+"\n")
        return statement
    
    def stop_ticker_symbol(self, symbol):
        try:
            bm51 = self._sockets[symbol]["socketmanager"]
            key51 = self._sockets[symbol]["key"]
            bm51.stop_socket(key51)
            bm51.close()
            self._sockets[symbol]["socketmanager"] = ""
            self._sockets[symbol]["key"] = ""
            self.write_to_console("Socket closed for "+symbol, to_push=1)
        except:
            self.write_to_console("Socket is empty for "+symbol, to_push=1)
        
    def sell_trailing_profit(self, msg):
        
        symbol = msg["data"]['s']
        price = float(msg["data"]['p']) ## market price

        if self.trades_completed[symbol]["type_"] == "SELL" and self.trades_completed[symbol]["trade_status"]=="running":
            if price > self.trades_completed[symbol]["sell_value"]:
                if self.trades_completed[symbol]["count"] == 0:
                    temp  = self.api.futures_position_information()
                    entry_price_ = [[float(temp[i1]['entryPrice']),float(temp[i1]['positionAmt'])] \
                                    for i1 in range(len(temp)) if temp[i1]['symbol'] == symbol]
                    self.trades_completed[symbol]["units_total"] = entry_price_[0][1]
                    self.trades_completed[symbol]["count"] = 1
                    self.trades_completed[symbol]["ttp_activated"] = True
                    self.trades_completed[symbol]["old_price"] = np.copy(price)
                
                    if entry_price_[0][0] == 0:
                        _  = self.api.futures_cancel_all_open_orders(symbol=symbol)
                        ## stop the ticker stream
                        self.trades_completed[symbol]["trade_status"] = "finished"
                        self.update_()
                        self.stop_ticker_symbol(symbol)
                    
                if self.trades_completed[symbol]["ttp_activated"] and self.trades_completed[symbol]["trade_status"]=="running":
                    if price > self.trades_completed[symbol]["old_price"]*(1 + (self.take_profit_trailing/100.)):
                        self.trades_completed[symbol]["old_price"] = self.trades_completed[symbol]["old_price"]*(1 + (self.take_profit_trailing/100.))
                    
                    elif price < self.trades_completed[symbol]["old_price"] and self.trades_completed[symbol]["trade_status"]=="running":
                        self.trades_completed[symbol]["trade_status"] = "finished"
                        _ = self.api.futures_create_order(symbol=symbol, type="MARKET", 
                                                          quantity=self.trades_completed[symbol]["units_total"], \
                                                              positionSide="BOTH", side="SELL")
                        ## remove open orders from book
                        _  = self.api.futures_cancel_all_open_orders(symbol=symbol)
                        ## stop the ticker stream
                        self.update_()
                        self.stop_ticker_symbol(symbol)
                    
        elif self.trades_completed[symbol]["type_"] == "BUY" and self.trades_completed[symbol]["trade_status"]=="running":
            if price < self.trades_completed[symbol]["sell_value"]:
                if self.trades_completed[symbol]["count"] == 0:
                    temp  = self.api.futures_position_information()
                    entry_price_ = [[float(temp[i1]['entryPrice']),float(temp[i1]['positionAmt'])] \
                                    for i1 in range(len(temp)) if temp[i1]['symbol'] == symbol]
                    self.trades_completed[symbol]["units_total"] = abs(entry_price_[0][1])
                    self.trades_completed[symbol]["count"] = 1
                    self.trades_completed[symbol]["ttp_activated"] = True
                    self.trades_completed[symbol]["old_price"] = np.copy(price)
                
                    if entry_price_[0][0] == 0:
                        _  = self.api.futures_cancel_all_open_orders(symbol=symbol)
                        ## stop the ticker stream
                        self.trades_completed[symbol]["trade_status"] = "finished"
                        self.update_()
                        self.stop_ticker_symbol(symbol)
                    
                if self.trades_completed[symbol]["ttp_activated"] and self.trades_completed[symbol]["trade_status"]=="running":
                    if price < self.trades_completed[symbol]["old_price"]*(1 - (self.take_profit_trailing/100.)):
                        self.trades_completed[symbol]["old_price"] = self.trades_completed[symbol]["old_price"]*(1 - (self.take_profit_trailing/100.))
                    
                    elif price > self.trades_completed[symbol]["old_price"] and self.trades_completed[symbol]["trade_status"]=="running":
                        self.trades_completed[symbol]["trade_status"] = "finished"
                        _ = self.api.futures_create_order(symbol=symbol, type="MARKET", 
                                                          quantity=self.trades_completed[symbol]["units_total"], \
                                                      positionSide="BOTH", side="BUY")
                        ## remove open orders from book
                        _  = self.api.futures_cancel_all_open_orders(symbol=symbol)
                        ## stop the ticker stream
                        self.update_()
                        self.stop_ticker_symbol(symbol)

    def print_statement(self, c_time, symbol, flag1, volDiff1, volDiff, current_price, old_price, \
                        percent_chgsP, indicator_, ppercent):
        statement = []
        ## check open position counts (from Binance)
        coin_temp = []
        count = 10000000
        try:
            if self.is_exchange_market:
                temp  = self.api.futures_position_information()
                coin_temp = [temp[i1]['symbol'] for i1 in range(len(temp)) if float(temp[i1]['entryPrice']) != 0.0]
                count = len(coin_temp)
            statement.append("Current active smart trades in Binance is : "+str(count)+"\n")
        # TODO implement strategy for SPOT market
        except:
            statement.append("Problem collecting the open position history (Binance module); \
                              setting trade counts to 10000000 (i.e. cannot trade until Binance comes back online)\n")
        
        trade_log = False
        if symbol in coin_temp:
            statement.append("Order already open for this coin in Binance, doing nothing for "+symbol+"\n")
            
        elif (self.live_trade) and (count < self.lim_trades):
            self.nb_trades = self.nb_trades + 1
            statement = self._binance_buy_sell(alt_coin=symbol, \
                                                   current_value=current_price, \
                                                           statement=statement, \
                                                               indicator_=indicator_,\
                                                                   ppercent=ppercent)
            trade_log = True
                
        elif (count >= self.lim_trades):
            statement.append("Limit active trades in progress, will still continue with Safety for open trades")
            return
            
        sym = "SYM: " + symbol
        flag = "PRICE! ("+flag1+")"
        vDiff = "DIFF (%): " + str(round(volDiff, 2))
        pcci = "Old price: "+ str(old_price)
        pcci1 = "Current price: "+ str(current_price)
        curr_pd = "Current price change threshold: "+str(percent_chgsP)
        volval = ''
        if volDiff1 > 0.0:
            volval = "BUYING activity \n"
        elif volDiff1 < 0.0:
            volval = "SELLING activity \n"
            
        my_string = ' || '.join(map(str, [c_time, flag, sym, pcci, pcci1, curr_pd, vDiff, volval]))
        str_from_list = ''.join([data for ele in statement for data in ele])
        
        if trade_log:
            with open(self.filename_, "a") as myfile:
                myfile.write(my_string)
                myfile.write(str_from_list+" \n")
            
        self.write_to_console(str_from_list, to_push=1)
        self.write_to_console(my_string, to_push=1)
        
    def process_message(self, msg):
        if self.price_analysis_mode == "market":
            msg = msg["data"]
            
        ct = time.time()
        now = datetime.datetime.fromtimestamp(ct)
        c_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        for ijk in range(len(msg)):
            x = currency_container(msg[ijk], candle_len=len(self.candlesP), mode=self.price_analysis_mode)

            if (x.symbol not in self.coins) or x.symbol[-len(self.basecurrency):] != self.basecurrency:
                continue

            if x.symbol not in self.new_list:
                if self.mode_analysis == "Automatic":
                    if self.is_exchange_market:
                        trades= self.api.futures_klines(symbol=x.symbol, interval="1m", limit=1000)
                    else:
                        trades= self.api.get_klines(symbol=x.symbol, interval="1m", limit=1000)
                    ## candle stats
                    percentT = [100*(float(d[2]) - float(d[3]))/float(d[2]) for i, d in enumerate(trades)]
                    temp_ = [0.1 if np.mean(percentT) < 0.1 else np.mean(percentT)]
                    x.percent_chgsP = temp_[0]
                    x.profit_percentP = temp_[0]
                else:
                    x.percent_chgsP = float(self.price_pd.text())
                
                self.new_list[x.symbol] = x
                self.write_to_console("Gathering (only "+self.basecurrency+" pairs) "+x.symbol, to_push=1)
            
            else:
                stored_currency = self.new_list[x.symbol]
                
                indicator_ = np.copy(self.indicator) #Perm copy
                
                if ((ct - stored_currency.time_stamp) > 1):
                    stored_currency.time_stamp = ct 

                    for i in range(len(stored_currency.time_stamp_period)):
                        
                        if ((ct - stored_currency.time_stamp_period[i]) >= self.candlesP[i]):
                            
                            execute_trade = False
                            
                            priceDiff1 = ((x.bid_price - stored_currency.price_time[i]) / stored_currency.price_time[i]) * 100                              
                            # temp var to launch
                            if self.mode_analysis == "Automatic":
                                if indicator_ == 'long':
                                    pd_val = stored_currency.percent_chgsP
                                    dp_val = pd_val * 50 # some high value
                                else:
                                    dp_val = stored_currency.percent_chgsP
                                    pd_val = pd_val * 50 # some high value
                            else:
                                pd_val = self.price_pd.text()
                                dp_val = self.price_dp.text()
                                
                            if ((priceDiff1 < 0.0) and (abs(priceDiff1) > float(dp_val))) or \
                                ((priceDiff1 > 0.0) and (float(dp_val) > abs(priceDiff1) > float(pd_val))):
                                ## big DUMP or small PUMP (open a LONG)
                                if indicator_ == 'long':
                                    execute_trade = True
                                elif indicator_ == 'short':
                                    execute_trade = False
                                
                            elif ((priceDiff1 < 0.0) and (float(dp_val) > abs(priceDiff1) > float(pd_val))) or \
                                ((priceDiff1 > 0.0) and (abs(priceDiff1) > float(dp_val))):
                                ## small DUMP or big PUMP (open a SHORT)
                                if indicator_ == 'short':
                                    execute_trade = True
                                elif indicator_ == 'long':
                                    execute_trade = False

                            if execute_trade and self.running==False:
                                self.running = True
                                # process_temp = threading.Thread(target=self.print_statement, args=(c_time, stored_currency.symbol, \
                                #                                               str(self.candlesP[i])+" Sec", \
                                #                                               priceDiff1, abs(priceDiff1), \
                                #                                               x.bid_price,stored_currency.price_time[i],\
                                #                                               stored_currency.percent_chgsP, indicator_,
                                #                                               stored_currency.profit_percentP), daemon=True)
                                # process_temp.start()
                                self.print_statement(c_time, stored_currency.symbol, \
                                                    str(self.candlesP[i])+" Sec", \
                                                    priceDiff1, abs(priceDiff1), \
                                                    x.bid_price,stored_currency.price_time[i],\
                                                    stored_currency.percent_chgsP, indicator_,
                                                    stored_currency.profit_percentP)
                                stored_currency.time_stamp_period =  [ct for _ in range(len(self.candlesP))]
                                stored_currency.price_time =  [x.bid_price for _ in range(len(self.candlesP))]
                                self.running = False
                                
                            stored_currency.price_time[i] = x.bid_price
                            stored_currency.time_stamp_period[i] = ct   
                    stored_currency.volume24hr = x.volume24hr
                    
                if ((ct - stored_currency.time_stamp_reset) > 3600):
                    stored_currency.time_stamp_reset = ct
                    if self.mode_analysis == "Automatic":
                        if self.is_exchange_market:
                            trades= self.api.futures_klines(symbol=x.symbol, interval="1m", limit=1000)
                        else:
                            trades= self.api.get_klines(symbol=x.symbol, interval="1m", limit=1000)
                        ## candle stats
                        percentT = [100*(float(d[2]) - float(d[3]))/float(d[2]) for i, d in enumerate(trades)]
                        temp_ = [0.1 if np.mean(percentT) < 0.1 else np.mean(percentT)]
                        stored_currency.percent_chgsP = temp_[0]
                        stored_currency.profit_percentP = temp_[0]
                    else:
                        stored_currency.percent_chgsP = float(self.price_pd.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_()) 