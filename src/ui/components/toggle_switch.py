# toggle_switch.py
from PyQt5.QtCore   import QEasingCurve, QPropertyAnimation, pyqtProperty
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui    import QColor, QPainter, QBrush, QPen
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt 
class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)   
    def __init__(self, parent=None, checked=False, bg_off="#d0d0d0", bg_on="#3a7afe"):
        super().__init__(parent)
        self._checked = checked
        self._bg_off  = QColor(bg_off)
        self._bg_on   = QColor(bg_on)
        self._x_pos   = 1 if not checked else 21
        self.setFixedSize(40,22)
        self._anim = QPropertyAnimation(self, b"xPos", self,
                                        duration=160, easingCurve=QEasingCurve.OutQuad)

    # --- 属性：xPos 用来做动画滑动 ---
    def getX(self):  return self._x_pos
    def setX(self,v):
        self._x_pos = v
        self.update()
    xPos = pyqtProperty(int, fget=getX, fset=setX)

    # --- 鼠标点击切换状态 ---
    def mousePressEvent(self, ev):
        self._checked = not self._checked
        self._anim.stop()
        self._anim.setStartValue(self._x_pos)
        self._anim.setEndValue(21 if self._checked else 1)
        self._anim.start()
        # 发一个信号给外层
        self.toggled.emit(self._checked)

    # --- 绘制 ---
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # 轨道
        p.setBrush(QBrush(self._bg_on if self._checked else self._bg_off))
        p.setPen(QPen(Qt.transparent))
        p.drawRoundedRect(0,0,40,22,11,11)
        # 滑块
        p.setBrush(QBrush(Qt.white))
        p.drawEllipse(self._x_pos, 1, 18,18)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, state: bool):
        if state == self._checked:
            return
        self.mousePressEvent(None)