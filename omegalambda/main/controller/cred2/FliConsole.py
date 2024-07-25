from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets

class FliConsole(QtWidgets.QPlainTextEdit):
    getData = pyqtSignal(str)
#-------------------------------------------------------------------#
    def __init__(self):
        super(FliConsole, self).__init__()
        p = self.palette()
        p.setColor(QPalette.Base, Qt.black)
        p.setColor(QPalette.Text, QColor(218,171,255))
        self.setPalette(p)
        self.setFont(QFont("Courier",12))
        self.insertPlainText("fli-cli>")
        c = self.textCursor()
        self.cursorPos = c.position()
        self.commands = []
        self.command = []
        self.commandToSend = ""
        self.index = 0

#-------------------------------------------------------------------#
    def PutData(self,data):
        self.insertPlainText(data)
        c = self.textCursor()
        c.movePosition(QTextCursor.End)
        self.setTextCursor(c)
        self.cursorPos = c.position()

#-------------------------------------------------------------------#
    def keyPressEvent(self, e):
        c = self.textCursor()
        if e.key() == Qt.Key_Delete:
            if c.position() < self.cursorPos:
                return
            if len(self.command) != 0:
                removeIndex = c.position() - self.cursorPos
                del self.command[removeIndex]
            QPlainTextEdit.keyPressEvent(self,e)
        elif e.key() == Qt.Key_Backspace:
            if self.toPlainText()[len(self.toPlainText())-1] == ">":
                return
            else:
                if len(self.command) != 0:
                    removeIndex = c.position() - 1 - self.cursorPos
                    del self.command[removeIndex]
                QPlainTextEdit.keyPressEvent(self,e)
        elif e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.command.append(e.text())
            c.movePosition(QTextCursor.End)
            self.setTextCursor(c)
            QPlainTextEdit.keyPressEvent(self,e)
            self.getData.emit(''.join(self.command))
            self.commands.append(''.join(self.command))
            self.index = len(self.commands)
            self.command.clear()
        elif e.key() == Qt.Key_Up:
            c.movePosition(QTextCursor.End)
            self.setTextCursor(c)
            for i in range(0, len(self.command)):
                c.deletePreviousChar()
            if self.index != 0:
                self.index = self.index - 1
            if len(self.commands) > self.index:
                self.command = list(self.commands[self.index].replace('\r',''))
                self.insertPlainText(''.join(self.command))
        elif e.key() == Qt.Key_Down:
            c.movePosition(QTextCursor.End)
            self.setTextCursor(c)
            for i in range(0, len(self.command)):
                c.deletePreviousChar()
            if self.index != (len(self.commands)-1):
                self.index = self.index + 1
            if len(self.commands) > self.index:
                self.command = list(self.commands[self.index].replace('\r',''))
                self.insertPlainText(''.join(self.command))
        elif e.key() == Qt.Key_Left or e.key() == Qt.Key_Right:
            QPlainTextEdit.keyPressEvent(self,e)
        else:
            insertIndex = c.position() - self.cursorPos
            if Qt.Key_Backspace != e.key() and insertIndex >= 0:
                if insertIndex >= len(self.command):
                    self.command.append(e.text())
                else:
                    self.command.insert(insertIndex,e.text())
            QPlainTextEdit.keyPressEvent(self,e)
