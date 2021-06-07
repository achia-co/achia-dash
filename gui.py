import sys,os
from PyQt5.QtWidgets import QLineEdit, QGridLayout,QLabel ,QPushButton,QCheckBox 
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QTimer
from logging.handlers import RotatingFileHandler



import logging
from run import achia_logger
import yaml




logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
# # create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# # add formatter to ch
ch.setFormatter(formatter)

file_handler = RotatingFileHandler('achia-debug.log', maxBytes=2000, backupCount=10)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# # if logger.handlers:
# #     print(logger.handlers)
# #     for hnd in logger.handlers:
# #         logger.removeHandler(hnd)

# # add ch to logger




logger_gui = logging.getLogger()
logger_gui.setLevel(logging.DEBUG)
# if logger_gui.handlers:
#     print(logger_gui.handlers)
#     for hnd in logger_gui.handlers:
#         logger_gui.removeHandler(hnd)
# # You can control the logging level
# logger_gui.setLevel(logging.DEBUG)


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class MyDialog(QtWidgets.QDialog, QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_directory  = os.path.dirname(__file__)
        self.note_icon      = os.path.join( self.current_directory,'img','logo.ico' )
        self.file_name = 'achia.yaml'

        try:
            f = open(self.file_name, 'r')
            self.config = yaml.load(stream=f, Loader=yaml.Loader)
            f.close() 
            if not isinstance(self.config, dict):
                self.config = dict()
        except:
            self.config = dict()
        print(self.config)
        self.chia_logger = achia_logger()  
        

        

        logTextBox = QTextEditLogger(self)
        logTextBox.setLevel(logging.INFO)

        # You can format what is printed to text box
        logTextBox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger_gui.addHandler(logTextBox)

        grid = QGridLayout()
        grid.setSpacing(2)
        
        e1_lable = QLabel('Token')
        e2_lable = QLabel('Machine ID')
        e3_lable = QLabel('Plotting Logs Path')

        self.e1 = QLineEdit(self.config.get("TOKEN","Token xxxxxxxxxxxxxxxxxx"))
        self.e2 = QLineEdit(self.config.get("MACHINE_ID","xxxxxx"))
        self.e3 = QLineEdit(self.config.get("PLOTTING_LOGS_PATH",""))
        self.e3.setPlaceholderText("Put in the folder of the plotting logs")
        label = QLabel()
        label.setText('<a href="https://achia.co">https://achia.co</a>')
        label.setOpenExternalLinks(True)
        
        grid.addWidget(e1_lable, 1, 0, 1,1)
        grid.addWidget(self.e1, 1, 1, 1,4)

        grid.addWidget(e2_lable, 2, 0,1,1)
        grid.addWidget(self.e2, 2, 1,1,4)

        grid.addWidget(e3_lable, 3, 0,1,1)
        grid.addWidget(self.e3, 3, 1,1,4)
        
        
        logo = QLabel()
        logo.setPixmap(QtGui.QPixmap(os.path.join( self.current_directory,'img','logo-text.png' )).scaledToWidth(160))
        version = QLabel("Version: 0.2")
        
        self.startBtn=QPushButton('Start')
        self.endBtn=QPushButton('Stop')
        
        sublayout1 = QtWidgets.QVBoxLayout()
        sublayout1.addWidget(logo, alignment=QtCore.Qt.AlignCenter)
        sublayout1.addWidget(label, alignment=QtCore.Qt.AlignCenter)
        sublayout1.addWidget(version, alignment=QtCore.Qt.AlignCenter)
        self.is_debug = QCheckBox("Save debug log")
        self.is_debug.setChecked(True)
        sublayout1.addWidget(self.is_debug)
        sublayout1.addWidget(self.startBtn)
        sublayout1.addWidget(self.endBtn)
        
        grid.addLayout(sublayout1, 4, 0, 6, 1)
        grid.addWidget(logTextBox.widget,4, 1, 6, 4)
        
        self.startBtn.clicked.connect(self.start)
        self.endBtn.clicked.connect(self.end)
    

        
        self.setLayout(grid)
        self.setGeometry(800, 500, 800, 300)
        self.setWindowTitle('aChia Dash Monitor')
        self.setWindowIcon(QtGui.QIcon(self.note_icon))    
        self.timer=QTimer()
        self.timer.timeout.connect(self.run)
        
        self.chia_logger.config = self.config
 
    def get_value(self):
        self.config["TOKEN"] = self.e1.text() 
        self.config["MACHINE_ID"] = self.e2.text()
        self.config["PLOTTING_LOGS_PATH"] = self.e3.text()
        with open(self.file_name, 'w') as yaml_file:
            yaml.dump(self.config, yaml_file, default_flow_style=False)

    def run(self):
        self.chia_logger.run() 
        
    def start(self):
        try:
            self.get_value()
            logging.info("***********Starting aChia Dash Monitor***********")
            logging.info(f"TOKEN = {self.config['TOKEN']}" )
            logging.info(f"MACHINE_ID = {self.config['MACHINE_ID']}" )
            logging.info(f"PLOTTING_LOGS_PATH = {self.config['PLOTTING_LOGS_PATH']}" )
            logging.info("********************************************" )
            self.is_debug.setEnabled(False)
            if self.is_debug.isChecked():
                logger_gui.setLevel(logging.DEBUG)
                logging.info("DEBUG is ON" )
            else:
                logger_gui.setLevel(logging.INFO)
                logging.info("DEBUG is OFF" )
            
            self.chia_logger.set_value()
            self.run() 
            self.timer.start(60000)
            self.startBtn.setEnabled(False)
            self.endBtn.setEnabled(True)
        except Exception as e:
            logging.error(e)
        
    def end(self):
        logging.info("***********Stopped*********" )
        self.timer.stop()
        self.startBtn.setEnabled(True)
        self.endBtn.setEnabled(False)  
        self.is_debug.setEnabled(True)

        


        
if __name__ == '__main__':
      app = QtWidgets.QApplication(sys.argv)
      widget = MyDialog()
      widget.show()
      #widget.line_edit.setText('Text updated!')
      ret = sys.exit(app.exec_())
      sys.exit(ret)
