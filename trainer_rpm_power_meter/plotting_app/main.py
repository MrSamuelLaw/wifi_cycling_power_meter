#!./.venv/Scripts/python

from wifi_client import WifiClient, asyncio
from PySide2 import QtWidgets
from PySide2.QtCharts import QtCharts
from PySide2.QtGui import QPainter, QFont
from PySide2.QtCore import QObject, Signal, Slot, Qt
from time import sleep, time
from datetime import timedelta
from threading import Thread
from sys import exit


class PlotterPollerSignals(QObject):
    power_updated = Signal(float)
    connect_status_changed = Signal(bool)


class PlotterPoller(QObject, WifiClient):

    def __init__(self):
        self.signals = PlotterPollerSignals()
        WifiClient.__init__(self)
        self.power = 0

    def connect(self):
        # QObject and WifiClient both have connect methods,
        # thus we have to specify which one we want to use
        WifiClient.connect(self)

    async def comm_loop(self):
        """
        overrides the wifi_client comm_loop() method. This
        definition grabs a new value, then waits to be
        forcefully timed out.
        """

        # request update
        self.send("c")  # send request for rpm updata
        self._received = False  # switch flag back to false
        self.rotation_time = 0  # set rpm to zero
        # wait or timeout
        while not self._received:
            await asyncio.sleep(0.01)
        # if updated, transform the data into power numbers.
        a = 199_844_880_469.07413 - 48_000_000_000
        b = -7_111_362.674411774 + 2_100_500
        c = 68.65055109403046
        if self.rotation_time:
            omega = 1/self.rotation_time
            self.power = (a*(omega**2)) + (b*(omega)) + c
        else:
            self.power = 0.0
        # forced wait for timeout
        await asyncio.sleep(1)

    def poll(self):
        """
        overrides the wifi_client poll() method
        to manage the comm_loop
        """
        self.start_time = time()
        while self.is_connected:
            start = time()
            try:
                self.loop.run_until_complete(
                    asyncio.wait_for(self.comm_loop(), self.timeout)
                )
            except asyncio.TimeoutError:
                self.signals.power_updated.emit(self.power)
        self.signals.connect_status_changed(self.is_connected)


class PowerDashboard(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__(parent=None)
        self.setWindowTitle("uPower")
        self.msgbox = QtWidgets.QMessageBox()
        self.msgbox.setText("attempting to connect...")
        self.msgbox.setStandardButtons(
            QtWidgets.QMessageBox.NoButton
        )
        self.set_central_widget()
        self.set_layout()
        self.set_plots()
        self.set_top_banner()
        self.set_menu_buttons()
        self.set_status_label()
        self.set_power_poller()

    def set_central_widget(self):
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

    def set_layout(self):
        self.main_layout = QtWidgets.QGridLayout(self.centralWidget())
        self.central_widget.setLayout(self.main_layout)

    def set_plots(self):
        # create charts
        self.chart = QtCharts.QChart()
        # create chart views
        self.chart_view = QtCharts.QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        # add to the widget
        self.main_layout.addWidget(self.chart_view, 1, 0, 1, 1)
        # create chart's line series
        self.line_series = QtCharts.QLineSeries()
        self.chart.addSeries(self.line_series)
        # create the axis
        self.x_axis = QtCharts.QValueAxis(self.chart)
        self.y_axis = QtCharts.QValueAxis(self.chart)
        self.x_axis.setTickCount(10)
        self.y_axis.setTickCount(10)
        # add the axis to the chart
        self.chart.addAxis(self.x_axis, Qt.AlignBottom)
        self.chart.addAxis(self.y_axis, Qt.AlignLeft)
        # add axis to the series
        self.line_series.attachAxis(self.x_axis)
        self.line_series.attachAxis(self.y_axis)
        self.chart.legend().setVisible(False)
        self.y_axis.setRange(0, 250)

    def set_top_banner(self):
        # create spacers
        self.left_banner_spacer = QtWidgets.QSpacerItem(
                0,  # width
                0,  # height
                QtWidgets.QSizePolicy.Expanding,  # h_policy
                QtWidgets.QSizePolicy.Minimum  # v_policy

            )
        self.middle_banner_spacer = QtWidgets.QSpacerItem(
                0,  # width
                0,  # height
                QtWidgets.QSizePolicy.Expanding,  # h_policy
                QtWidgets.QSizePolicy.Minimum  # v_policy

            )
        self.right_banner_spacer = QtWidgets.QSpacerItem(
                0,  # width
                0,  # height
                QtWidgets.QSizePolicy.Expanding,  # h_policy
                QtWidgets.QSizePolicy.Minimum  # v_policy

            )
        # create clock label
        hr_min_sec = str(timedelta(seconds=0))
        self.clock_label = QtWidgets.QLabel(hr_min_sec, parent=self)
        self.banner_font = QFont("Times", 40, QFont.Bold)
        self.clock_label.setFont(self.banner_font)
        # create the power label
        self.power_label = QtWidgets.QLabel("000", parent=self)
        self.power_label.setFont(self.banner_font)
        # add items to h_box_layout
        self.h_layout = QtWidgets.QHBoxLayout(self.centralWidget())
        self.h_layout.addSpacerItem(self.right_banner_spacer)
        self.h_layout.addWidget(self.clock_label)
        self.h_layout.addSpacerItem(self.middle_banner_spacer)
        self.h_layout.addWidget(self.power_label)
        self.h_layout.addSpacerItem(self.left_banner_spacer)
        # add h_box_layout to main layout
        self.main_layout.addLayout(self.h_layout, 0, 0, 1, 1)

    def set_menu_buttons(self):
        self.menu = self.menuBar().addAction(
            "Connect",
            self.connect_to_sensor_call
        )
        self.menu = self.menuBar().addAction(
            "Start",
            self.start_workout
        )

    def set_status_label(self):
        self.status_label = QtWidgets.QLabel(parent=self)
        self.statusBar().addPermanentWidget(self.status_label)
        self.update_status(False)

    def add_data(self, y_val: float):
        # update the clock
        cur_time = int(time() - self.pp.start_time)
        hr_min_sec = str(timedelta(seconds=cur_time))
        self.clock_label.setText(hr_min_sec)
        # plot iff reading is valid
        if y_val < 1000:
            # update the power
            self.power_label.setText(str(int(y_val)))
            # updat the graph
            self.line_series.append(cur_time, y_val)
            self.x_axis.setRange(0, cur_time)

    def update_status(self, connection_status: bool):
        if connection_status:
            self.status_label.setText("status: connected")
        else:
            self.status_label.setText("status: not connected")

    def set_power_poller(self):
        self.pp = PlotterPoller()  # create object
        self.pp.signals.power_updated.connect(self.add_data)
        self.sensor_thread = Thread(target=self.pp.poll)
        self.sensor_thread.daemon = True

    def connect_to_sensor_call(self):
        self.msgbox.resize(200, 100)
        self.msgbox.show()
        # always thread the non gui item if you want a msg box
        # to pop up
        thread = Thread(
            target=self.connect_to_sensor_process,
            daemon=True
        )
        thread.start()

    def connect_to_sensor_process(self):
        try:
            self.pp.connect()
        except Exception:
            self.msgbox.accept()
            self.update_status(False)
            self.msgbox.close()
            QtWidgets.QMessageBox.critical(
                self,
                'WARNING',
                'Failed to connect'
            )
        else:
            self.msgbox.accept()
            self.update_status(True)

    def start_workout(self):
        if self.pp.is_connected:
            self.sensor_thread.start()
        else:
            QtWidgets.QMessageBox.critical(
                None,
                'WARNING',
                'Cannot start workout without being connected'
            )


if __name__ == "__main__":
    app = QtWidgets.QApplication()
    pd = PowerDashboard()
    pd.resize(600, 500)
    pd.showMaximized()
    return_status = app.exec_()
    exit(return_status)
