"""
    Classes for generating GUI - Main window and Settings window
"""
import pcbnew

import json
import logging
import os
import random
import time
import wx

# Scale used for moving fps in test function
SCALE = 1000000


# Define class for displaying console_logger messages to wx.TextCtrl window:
class WxTextCtrlHandler(logging.Handler):
    def __init__(self, ctrl):
        logging.Handler.__init__(self)
        self.ctrl = ctrl

    def emit(self, record):
        s = self.format(record) + '\n'
        wx.CallAfter(self.ctrl.WriteText, s)


# GUI class
class PluginGui(wx.Frame):

    def __init__(self, title):
        super().__init__(parent=None, title=title, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)

        # Temp var used for moving fp left and right to test diff
        self.odd_even_var = 0

        self.initUI()
        self.Centre()
        self.Show()

    # --------------------------- User interface --------------------------- #
    def initUI(self):
        panel = wx.Panel(self)

        # Menu bar
        self.menubar = wx.MenuBar()
        self.file = wx.Menu()
        #settings = self.file.Append(wx.ID_SETUP, "&Settings\tCtrl+S", "Open setting window")
        load = self.file.Append(wx.ID_FILE, "&Load\tCtrl+L", "Load test board")
        move_objects = self.file.Append(wx.ID_ANY, "&Move objects\tCtrl+T")
        #self.Bind(wx.EVT_MENU, self.openSettings, settings)
        self.Bind(wx.EVT_MENU, self.loadBoard, load)
        self.Bind(wx.EVT_MENU, self.moveObjects, move_objects)
        self.menubar.Append(self.file, "File")
        self.SetMenuBar(self.menubar)

        # Console output
        text_log = wx.StaticText(panel, label="Log:", style=wx.ALIGN_LEFT)
        console = wx.TextCtrl(panel, wx.ID_ANY, size=(400, 200),
                              style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        # Console logger
        self.console_logger = logging.getLogger("console-gui")
        console_handler = WxTextCtrlHandler(console)
        self.console_logger.addHandler(console_handler)
        FORMAT_LONG = "%(asctime)s %(levelname)s %(message)s"
        FORMAT_SHORT = "%(levelname)s %(message)s"
        console_handler.setFormatter(logging.Formatter(FORMAT_SHORT))
        self.console_logger.setLevel(logging.INFO)


        # Buttons
        self.button_quit = wx.Button(panel, label="Quit")
        self.button_quit.Bind(wx.EVT_BUTTON, self.onButtonQuit)

        self.button_connect = wx.Button(panel, label="Connect")
        self.button_connect.Bind(wx.EVT_BUTTON, self.onButtonConnect)

        self.button_disconnect = wx.Button(panel, label="Disconnect")
        self.button_disconnect.Bind(wx.EVT_BUTTON, self.onButtonDisconnect)
        self.button_disconnect.Enable(False)

        self.button_send_message = wx.Button(panel, label="Send JSON")
        self.button_send_message.Bind(wx.EVT_BUTTON, self.onButtonSendMessage)
        self.button_send_message.Enable(False)

        self.button_scan_board = wx.Button(panel, label="Board to JSON")
        self.button_scan_board.Bind(wx.EVT_BUTTON, self.onButtonScanBoard)
        self.button_scan_board.Enable(True)

        self.button_get_diff = wx.Button(panel, label="Get diff")
        self.button_get_diff.Bind(wx.EVT_BUTTON, self.onButtonGetDiff)
        self.button_get_diff.Enable(True)

        # Socket control buttons
        socket_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        socket_button_sizer.Add(self.button_connect, 0)
        socket_button_sizer.Add(self.button_disconnect, 0)
        # socket_button_sizer.Add(self.button_send_message, 0)
        # Add Socket control buttons to static box
        socket_box = wx.StaticBoxSizer(wx.VERTICAL, panel, label="Socket")
        socket_box.Add(wx.StaticText(panel, label=""), 1, wx.ALL | wx.EXPAND)  # Blank space
        socket_box.Add(socket_button_sizer, 1, wx.CENTRE)  # Add button sizer as child of static box
        socket_box.Add(wx.StaticText(panel, label=""), 1, wx.ALL | wx.EXPAND)  # Blank space

        # Board control buttons
        board_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        board_button_sizer.Add(self.button_scan_board, 0)
        board_button_sizer.Add(self.button_get_diff, 0)
        board_button_sizer.Add(self.button_send_message, 0)
        # Add board control buttons to static box
        board_box = wx.StaticBoxSizer(wx.VERTICAL, panel, label="PCB")
        board_box.Add(wx.StaticText(panel, label=""), 1, wx.ALL | wx.EXPAND)  # Blank space
        board_box.Add(board_button_sizer, 1, wx.CENTRE)  # Add pcb control button sizer to static box
        board_box.Add(wx.StaticText(panel, label=""), 1, wx.ALL | wx.EXPAND)  # Blank space

        # Bottom buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # button_sizer.Add(self.button_scan_board, 0)
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(self.button_quit, 0, wx.ALIGN_LEFT, 20)

        # Main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(socket_box, 0, wx.ALL | wx.EXPAND, 5)  # Static box with start/stop buttons
        sizer.Add(board_box, 0, wx.ALL | wx.EXPAND, 5)  # Static box with pcb control buttons
        sizer.Add(text_log, 0, wx.ALL | wx.EXPAND, 0)  # Top text of vertical sizer
        sizer.Add(console, 1, wx.ALL | wx.EXPAND, 5)  # Add ctrl text
        sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND)  # Bottom buttons

        # Fit window to panel size
        panel.SetSizer(sizer)
        frameSizer = wx.BoxSizer()
        frameSizer.Add(panel, 0, wx.EXPAND)
        self.SetSizer(frameSizer)
        self.Fit()

    # --------------------------- UI Methods --------------------------- #
    def moveObjects(self, event):
        drws = self.brd.GetDrawings()
        for drw in drws:
            if "Circ" in drw.ShowShape():
                x = drw.GetX()
                if self.odd_even_var % 2 == 0:
                    drw.SetX(x + 1 * SCALE)
                    self.odd_even_var += 1
                else:
                    drw.SetX(x - 1 * SCALE)
                    self.odd_even_var += 1
                print(f"Moved circle X to {drw.GetX()}")

        fp = self.brd.GetFootprints()[0]
        y = fp.GetY()
        fp.SetY(y + 1 * SCALE)
        print(f"Moved FP Y to {fp.GetY()}")

        vias = []
        for track in self.brd.GetTracks():
            if "VIA" in str(type(track)):
                vias.append(track)
        via = vias[0]
        x = via.GetX()
        via.SetX(x + 1 * SCALE)
        print(f"Moved VIA to {via.GetX()}")

    def loadBoard(self, event):
        try:
            # Load test board
            dir_path = os.path.dirname(os.path.realpath(__file__))
            self.brd = pcbnew.LoadBoard(dir_path + "/test_pcbs/test_pcb.kicad_pcb")
            file_name = self.brd.GetFileName()
            pcb_id = file_name.split('.')[0].split('/')[-1]
            self.console_logger.log(logging.INFO, f"Loaded pcb: {pcb_id}")
        except Exception as e:
            self.console_logger.exception(e)

    def onButtonQuit(self, event):
        self.Close()