#!/usr/bin/env python3

import sys
import re
import traceback
from collections import namedtuple
from datetime import datetime
from time import time

from PyQt4.QtGui import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                         QPushButton, QTextEdit,
                         QTableView, QAbstractItemView,
                         QStandardItemModel, QStandardItem,
                         QTabWidget, QMenuBar, QAction)
from PyQt4.QtCore import Qt, QSize

import pyxie
import modifier
import config


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

        self.pyxie_listener = PyxieListener()

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
                         'created']

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

        Stream = namedtuple('Stream', ['client_ip', 'client_port', 
                                       'server_ip', 'server_port',
                                       'timestamp'])

        time1 = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
        time2 = datetime.fromtimestamp(time()+1).strftime('%Y-%m-%d %H:%M:%S')
        stream1 = Stream('192.168.12.44', 25712, '69.44.13.172', 443, time1)
        stream2 = Stream('192.168.12.44', 25712, '69.44.13.172', 443, time2)
        
        self.insert_stream(stream1)
        self.insert_stream(stream2)

    def show_traffic(self, timestamp):

        self.streamdump.setText(timestamp)

    def insert_stream(self, stream):

        items = []
        for val in stream:
            item = QStandardItem(str(val))
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            items.append(item)

        self.streammodel.appendRow(items)
        self.streamtable.resizeColumnsToContents()

    def toggle_proxy(self, active):

        if active:
            self.proxy_btn.setText("Starting Proxy")

            try:
                pyxie.start(self.pyxie_listener)
            except:
                self.proxy_btn.setText("Proxy Failed")
                self.proxy_btn.setChecked(False)
                traceback.print_exc()
                return

            while not pyxie.running:
                pass

            self.proxy_btn.setText("Proxy Running")

        else:
            pyxie.stop()
            self.proxy_btn.setText("Proxy Stopped")

    def toggle_intercept(self, active):

        pass

    def forward_traffic(self):

        pass

    def drop_traffic(self):

        pass

class PyxieListener:

    def __init__(self):

        pass

    def onConnectionEstablished(self, stream):

        print(stream)

    def onTrafficReceived(self, traffic):

        print(traffic)


def mod1(data):

    return re.sub(r'Accept-Encoding:.*\r\n', '', data.decode('utf8', 'ignore')).encode('utf8')

def main():

    config.modifiers.append(modifier.CustomModifier(mod1))

    app = QApplication(sys.argv)
    window = PyxieGui()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    sys.exit(main())
