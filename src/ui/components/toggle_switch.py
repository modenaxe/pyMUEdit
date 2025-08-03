# toggle_switch.py
from PyQt5.QtCore   import QEasingCurve, QPropertyAnimation, pyqtProperty
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui    import QColor, QPainter, QBrush, QPen, QLinearGradient
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt 

class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)  
    """iOS style Toggle Switch"""
    def __init__(self, parent=None, checked=False, bg_off="#d0d0d0", bg_on="#3a7afe"):
        """
        A minimalist iOS-style toggle switch with animated transitions

        Emits:
            toggled (bool): Emitted whenever the switch state changes

        Args:
            parent (QWidget, optional): Parent widget
            checked (bool, optional): Initial state of the switch (on/off)
            bg_off (str, optional): Hex color for the off-state background
            bg_on (str, optional): Hex color for the on-state background
        """
        
        super().__init__(parent)
        self._checked = checked
        self._bg_off  = QColor(bg_off)
        self._bg_on   = QColor(bg_on)
        self.start_pos = 1
        self.end_pos = 19
        self._x_pos   = self.start_pos if not checked else self.end_pos
        self.setFixedSize(40,22)
        self._anim = QPropertyAnimation(self, b"xPos", self,
                                        duration=300, easingCurve=QEasingCurve.InOutQuad)
        
        self._progress = 1.0 if checked else 0.0
        self._color_anim = QPropertyAnimation(self, b"progress", self)
        self._color_anim.setDuration(300)
        self._color_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._disabled = False

    # --- 属性：xPos 用来做动画滑动 ---
    def getX(self):  return self._x_pos
    def setX(self,v):
        self._x_pos = v
        self.update()
    xPos = pyqtProperty(int, fget=getX, fset=setX)
    
    def mix_colors(self, c1: QColor, c2: QColor, t: float) -> QColor:
        r = c1.red() + (c2.red() - c1.red()) * t
        g = c1.green() + (c2.green() - c1.green()) * t
        b = c1.blue() + (c2.blue() - c1.blue()) * t
        return QColor(int(r), int(g), int(b))

    def getProgress(self): 
        return self._progress
    
    def setProgress(self, v): 
        self._progress = v
        self.update()
        
    progress = pyqtProperty(float, fget=getProgress, fset=setProgress)

    # --- 鼠标点击切换状态 ---
    def mousePressEvent(self, ev):
        if self._disabled:
            return
        self._checked = not self._checked
        self._anim.stop()
        self._anim.setStartValue(self._x_pos)
        self._anim.setEndValue(self.end_pos if self._checked else self.start_pos)
        self._anim.start()
        
        self._color_anim.stop()
        self._color_anim.setStartValue(0 if self._checked else 1)
        self._color_anim.setEndValue(1 if self._checked else 0)
        self._color_anim.start()
        
        # 发一个信号给外层
        self.toggled.emit(self._checked)

    # --- 绘制 ---
    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # 轨道
        mixed_color = self.mix_colors(self._bg_off, self._bg_on, self._progress)
        
        if self._disabled:
            mixed_color = mixed_color.lighter(150)
            
        p.setBrush(QBrush(mixed_color))
        
        p.setPen(QPen(Qt.transparent))
        p.drawRoundedRect(0,0,40,22,11,11)
        
        if self._disabled:
            overlay = QColor(160, 160, 160, 60) 
            p.setBrush(QBrush(overlay))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(0, 0, 40, 22, 11, 11)
        
        # 滑块
        knob_color = QColor("#ffffff") if not self._disabled else QColor("#eeeeee")
        p.setBrush(QBrush(knob_color))
        p.drawEllipse(self._x_pos, 1, 20, 20)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, state: bool):
        if state == self._checked:
            return
        self.mousePressEvent(None)
    
    def setEnabled(self, state: bool):
        self._disabled = not state
        self.update()