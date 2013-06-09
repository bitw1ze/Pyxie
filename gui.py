#!/usr/bin/env python3

import sys
import re
import logging
import string
from datetime import datetime
from time import time
from threading import Lock
from queue import PriorityQueue

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

    def onTrafficSend(self, data):

        pass


class PyxieListener(PyxieBaseListener, QObject):


    def __init__(self, ui):

        QObject.__init__(self)
        self.ui = ui

    def onConnectionEstablished(self, stream):

        self.emit(SIGNAL("onConnectionEstablished"), stream)

    def onTrafficReceive(self, traffic):

        self.emit(SIGNAL("onTrafficReceive"), traffic)

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

        QObject.connect(self.listener, 
                        SIGNAL('onTrafficReceive'), 
                        self.put_traffic_history)
        QObject.connect(self.listener, 
                        SIGNAL('onConnectionEstablished'),
                        self.put_stream)

    def init_widgets(self):

        tabs = QTabWidget(self)
        tab1 = QWidget(self)
        tab2 = QWidget(self)

        menu_bar = QMenuBar(self)
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
        self.stream_dump = QTextEdit(self)

        # create buttons
        self.proxy_btn = QPushButton('Proxy Stopped')
        self.proxy_btn.setCheckable(True)
        self.proxy_btn.clicked[bool].connect(self.toggle_proxy)
        
        # add widgets to stream tab
        stream_tab = QVBoxLayout(tab1)
        stream_tab.addWidget(self.proxy_btn)
        stream_tab.addWidget(self.streamtable)
        stream_tab.addWidget(self.stream_dump)

        # create buttons and add them to hbox widget
        intercept_btn = QPushButton('Intercept', self)
        intercept_btn.setCheckable(True)
        intercept_btn.clicked[bool].connect(self.toggle_intercept)

        forward_btn = QPushButton('Forward', self)
        forward_btn.clicked[bool].connect(self.forward_traffic)

        drop_btn = QPushButton('Drop', self)
        drop_btn.clicked[bool].connect(self.drop_traffic)

        intercept_buttons = QHBoxLayout()
        intercept_buttons.addWidget(intercept_btn)
        intercept_buttons.addWidget(forward_btn)
        intercept_buttons.addWidget(drop_btn)

        # create textedit area where traffic goes
        self.intercept_dump = QTextEdit(self)

        # add widgets to stream tab
        intercept_tab = QVBoxLayout(tab2)
        intercept_tab.addLayout(intercept_buttons)
        intercept_tab.addWidget(self.intercept_dump)

        # add tabs to the tabs widget
        tabs.addTab(tab1, "Streams")
        tabs.addTab(tab2, "Intercept")

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(menu_bar)
        main_layout.addWidget(tabs)

        self.setLayout(main_layout)

    def init_data(self):

        self.interception_on = False
        self.intercept_lock = Lock()
        self.latest_traffic = None
                
    def show_traffic_history(self, stream_id):

        conversation = [h.payload for h in self.stream_history[stream_id]]
        dump = str(b''.join(conversation), 'utf8', 'ignore')
        self.stream_dump.setText(utils.printable_ascii(dump))

    def put_stream(self, stream):

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

    def put_traffic_history(self, traffic):

        self.stream_history[traffic.stream.stream_id].append(traffic)
        # TODO: call modifiers with entire record instead of just payload
        payload = self.call_modifiers(traffic.payload)

        if self.interception_on:
            self.intercept_lock.acquire()
            self.latest_traffic = traffic
            self.intercept_dump.setText(str(payload, 'utf8', 'ignore'))
        else:
            traffic.stream.unpause(payload)

    def toggle_proxy(self, active):

        if active:
            self.proxy_btn.setText("Starting Proxy")

            try:
                self.proxy.start()
            except:
                self.proxy_btn.setText("Proxy Failed")
                self.proxy_btn.setChecked(False)
                return

            while not self.proxy.running:
                pass

            self.proxy_btn.setText("Proxy Running")

        else:
            self.proxy.stop()
            self.proxy_btn.setText("Proxy Stopped")

    def toggle_intercept(self, active):

        if self.interception_on:
            self.forward_traffic()

        self.interception_on = not self.interception_on

    def forward_traffic(self):

        if self.interception_on and self.latest_traffic:
            payload = self.intercept_dump.toPlainText()
            self.intercept_dump.setText("")
            self.intercept_lock.release()
            stream = self.latest_traffic.stream
            self.latest_traffic = None
            stream.unpause(payload)

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

def main():

    global log

    timestamp = str(int(time()))
    logfile = config['logfile'].replace("^:TS:^", timestamp)
    log = init_logger(filename=logfile, level=logging.DEBUG)

    app = QApplication(sys.argv)
    window = PyxieGui()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
