#!/usr/bin/env python3

import sys
import re
import traceback
import logging
import string
from datetime import datetime
from time import time
from threading import Lock

from PyQt4.QtGui import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                         QPushButton, QTextEdit, QTableView, QAbstractItemView,
                         QStandardItemModel, QStandardItem,
                         QTabWidget, QMenuBar, QAction, QDesktopWidget)
from PyQt4.QtCore import QObject, Qt, SIGNAL

import modifier
import utils
from pyxie import Proxy
from config import config


log = None


class PyxieBaseListener:


    def onTrafficReceive(self, data):

        pass

    def onConnectionEstablished(self, data):

        pass

    def onTrafficModify(self, data):

        pass

    def onTrafficSend(self, data):

        pass


class PyxieListener(PyxieBaseListener, QObject):


    def __init__(self, ui):

        QObject.__init__(self)
        self.ui = ui

    def onConnectionEstablished(self, stream):

        self.latest_stream = stream
        self.emit(SIGNAL("onConnectionEstablished()"))

    def onTrafficReceive(self, data):

        self.ui.lock.acquire()
        self.latest_traffic = data
        self.emit(SIGNAL("onTrafficReceive()"))

    def onTrafficModify(self, data):

        return self.ui.call_modifiers(data)

    def onTrafficSend(self, data):

        pass



class StreamTableView(QTableView):


    def __init__(self, parent):

        QTableView.__init__(self)

        self.parent = parent

    def selectionChanged(self, selected, deselected):

        try:
            stream_id = selected.indexes()[0].row()
            self.parent.show_traffic_history(stream_id)

        except IndexError as e:
            return


class PyxieGui(QWidget):


    def __init__(self, width=800, height=600):

        QWidget.__init__(self)

        self.listener = PyxieListener(self)
        self.proxy = Proxy(config=config, listener=self.listener)
        self.stream_history = []
        self.modifiers = config['modifiers']

        self.init_window(width, height)
        self.init_widgets()
        self.init_signals()
        self.init_data()

    def init_window(self, width, height):

        self.setWindowTitle('Pyxie')
        self.resize(width, height)
        qr = self.frameGeometry()
        qr.moveCenter(QDesktopWidget().availableGeometry().center())
        self.move(qr.topLeft())
        #self.showMaximized()
        self.show()

    def init_signals(self):

        self.lock = Lock()

        QObject.connect(self.listener, SIGNAL('onTrafficReceive()'), 
                self.insert_traffic_into_history)
        QObject.connect(self.listener, SIGNAL('onConnectionEstablished()'),
                self.insert_stream)

    def init_widgets(self):

        tabs = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()

        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu('&File')

        open = QAction("Exit", self) 
        save = QAction("Save", self) 
        exit = QAction("Quit", self) 

        file_menu.addAction(open)
        file_menu.addAction(save)
        file_menu.addAction(exit)

        stream_labels = ['client ip', 'client port', 
                         'server ip', 'server port',
                         'protocol', 'created']

        # set up the stream tab
        self.streammodel = QStandardItemModel()
        self.streammodel.setHorizontalHeaderLabels(stream_labels)
        
        self.streamtable = StreamTableView(self)
        self.streamtable.setModel(self.streammodel)
        self.streamtable.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # create textedit area where traffic goes
        self.streamdump = QTextEdit()

        # create buttons
        self.proxy_btn = QPushButton('Proxy Stopped')
        self.proxy_btn.setCheckable(True)
        self.proxy_btn.clicked[bool].connect(self.toggle_proxy)
        
        # add widgets to the main layout
        stream_tab = QVBoxLayout(tab1)
        stream_tab.addWidget(self.proxy_btn)
        stream_tab.addWidget(self.streamtable)
        stream_tab.addWidget(self.streamdump)

        # set up intercept tab
        intercept_btn = QPushButton('Intercept', self)
        intercept_btn.setCheckable(True)
        intercept_btn.clicked[bool].connect(self.toggle_intercept)

        forward_btn = QPushButton('Forward', self)
        intercept_btn.clicked[bool].connect(self.forward_traffic)

        drop_btn = QPushButton('Drop', self)
        intercept_btn.clicked[bool].connect(self.drop_traffic)

        intercept_buttons = QHBoxLayout()
        intercept_buttons.addWidget(intercept_btn)
        intercept_buttons.addWidget(forward_btn)
        intercept_buttons.addWidget(drop_btn)

        self.traffic_dump = QTextEdit() 

        intercept_vbox = QVBoxLayout()
        intercept_vbox.addLayout(intercept_buttons)
        intercept_vbox.addWidget(self.traffic_dump)

        intercept_tab = QWidget(tab2)
        intercept_tab.setLayout(intercept_vbox)

        tabs.addTab(tab1, "Streams")
        tabs.addTab(tab2, "Intercept")

        main_layout = QVBoxLayout()
        main_layout.addWidget(menu_bar)
        main_layout.addWidget(tabs)

        self.setLayout(main_layout)

    def init_data(self):

        pass
                
    def show_traffic_history(self, stream_id):

        dump = str(b''.join(self.stream_history[stream_id]), 'utf8', 'ignore')
        self.streamdump.setText(utils.printable_ascii(dump))

    def insert_stream(self):

        stream = self.listener.latest_stream
        self.stream_history.append([])

        client_ip, client_port = stream.client.getpeername()
        server_ip, server_port = stream.server.getpeername()
        proto = stream.proto_name
        ts = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')

        vals = [client_ip, client_port, server_ip, server_port, proto, ts]
        items = []

        for val in vals:
            item = QStandardItem(str(val))
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items.append(item)

        self.streammodel.appendRow(items)
        self.streamtable.resizeColumnsToContents()

    def insert_traffic_into_history(self):

        data = self.listener.latest_traffic
        stream_id = int(data.stream_id)
        payload = data.payload
        self.stream_history[stream_id].append(payload)
        self.lock.release()

    def toggle_proxy(self, active):

        if active:
            self.proxy_btn.setText("Starting Proxy")

            try:
                self.proxy.start()
            except:
                self.proxy_btn.setText("Proxy Failed")
                self.proxy_btn.setChecked(False)
                traceback.print_exc()
                return

            while not self.proxy.running:
                pass

            self.proxy_btn.setText("Proxy Running")

        else:
            self.proxy.stop()
            self.proxy_btn.setText("Proxy Stopped")

    def toggle_intercept(self, active):

        pass

    def forward_traffic(self):

        pass

    def drop_traffic(self):

        pass

    def call_modifiers(self, data):

        modified = data
        for m in self.modifiers:
            modified = m.modify(modified)
        return modified
    

def init_logger(filename=None, level=logging.WARNING):

    """Initializes and returns a Logger object"""

    log = logging.getLogger('pyxie')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    if filename:
        fhdlr = logging.FileHandler(filename)
        fhdlr.setFormatter(formatter)
        log.addHandler(fhdlr) 

    chdlr = logging.StreamHandler()
    chdlr.setFormatter(formatter)
    log.addHandler(chdlr)
    
    log.setLevel(level)
    return log

def mod1(data):

    return re.sub(r'Accept-Encoding:.*\r\n', '', 
            data.decode('utf8', 'ignore')).encode('utf8')

def main():

    global log

    config['modifiers'].append(modifier.CustomModifier(mod1))
    timestamp = str(int(time()))
    logfile = config['logfile'].replace("^:TS:^", timestamp)
    log = init_logger(filename=logfile, level=logging.DEBUG)

    app = QApplication(sys.argv)
    window = PyxieGui()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
