#!/usr/bin/env python3

import sys
import re
import traceback
import logging
from collections import namedtuple
from datetime import datetime
from time import time

from PyQt4.QtGui import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                         QPushButton, QTextEdit,
                         QTableView, QAbstractItemView,
                         QStandardItemModel, QStandardItem,
                         QTabWidget, QMenuBar, QAction)
from PyQt4.QtCore import Qt, QSize

from pyxie import Proxy
import modifier
from config import config


log = None

class StreamTableView(QTableView):


    def __init__(self, parent):

        QTableView.__init__(self)

        self.parent = parent

    def selectionChanged(self, selected, deselected):

        indexes = selected.indexes()

        timestamp = indexes[-1].data()
        self.parent.show_traffic(timestamp)


class PyxieGui(QWidget):


    def __init__(self):

        QWidget.__init__(self)

        self.proxy = Proxy(config, self)

        self.init_ui()
        self.init_data()

    def init_ui(self):

        self.setWindowTitle('Pyxie')

        tabs = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()

        menu_bar = QMenuBar()
        file_menu = menu_bar.addMenu('&File')

        open = QAction("Exit", self) 
        save = QAction("Save", self) 
        build = QAction("Build", self) 
        exit = QAction("Quit", self) 

        file_menu.addAction(open)
        file_menu.addAction(save)
        file_menu.addAction(build)
        file_menu.addAction(exit)

        stream_labels = ['client ip', 'client port', 
                         'server ip', 'server port',
                         'protocol', 'created']

        # set up the stream tab
        self.streammodel = QStandardItemModel()
        self.streammodel.setHorizontalHeaderLabels(stream_labels)
        
        self.streamtable = StreamTableView(self)
        self.streamtable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.streamtable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.streamtable.setModel(self.streammodel)
        
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

        self.show()

    def init_data(self):

        pass
                
    def show_traffic(self, timestamp):

        self.streamdump.setText(timestamp)

    def insert_stream(self, stream):

        Stream = namedtuple('Stream', 
                           ['client_ip', 'client_port', 
                            'server_ip', 'server_port',
                            'protocol', 'timestamp'])

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


    # The following section defines events triggered by Proxy objects

    def onConnectionEstablished(self, stream):

        self.insert_stream(stream)

    def onTrafficReceived(self, traffic):

        print(traffic)


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
    window.resize(800, 600)
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
