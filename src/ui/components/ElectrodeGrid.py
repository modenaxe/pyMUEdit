import math
from PyQt5.QtWidgets import QWidget, QGridLayout, QLayout, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import Qt, QSize
import matplotlib.cm as cm
import numpy as np


class SquareWidget(QWidget):
    def __init__(self, color, index, change_index, interactive=True):
        super().__init__()

        self.interactive = interactive
        self.color = color
        self.hover_color = color.lighter(50)
        self.current_color = self.color

        self._width = 18
        self._height = 18
        self.change_index = change_index
        self.index = index
        self.setMinimumSize(self.sizeHint())
        self.setMaximumSize(self.sizeHint())

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    def setColor(self, color):
        self.color = color
        self.hover_color = color.lighter(50)
        self.current_color = self.color
        self.update()

    def setIndex(self, index):
        self.index = index

    def sizeHint(self):
        return QSize(self._width, self._height)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setBrush(self.current_color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

    def mousePressEvent(self, a0):
        if self.interactive:
            self.change_index(self.index)

    def enterEvent(self, a0):
        if self.interactive:
            self.current_color = self.hover_color
            self.update()

    def leaveEvent(self, a0):
        if self.interactive:
            self.current_color = self.color
            self.update()

class ElectrodeGrid(QWidget):
    def __init__(self, emg_obj, channel_indices, change_index, parent=None):
        super().__init__(parent)

        self.channel_indices = channel_indices
        self.change_index = change_index
        if "gridname" in emg_obj.signal_dict:
            self.electrode_names = emg_obj.signal_dict["gridname"]
            self.muscle_names = emg_obj.signal_dict["muscle"]
        else:
            return
        
        self.electrode_index = 0
        self.square_map = {}

        # left panel
        left_container = QWidget()
        layout = QVBoxLayout(left_container)
        layout.addStretch()

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.init_grids()
        self.draw_grid()
        layout.addLayout(self.grid_layout)

        self.label = QLabel(f"{self.muscle_names[self.electrode_index]}")
        layout.addWidget(self.label)

        # left and right buttons
        lrbuttons = QWidget()
        button_layout = QHBoxLayout()
        self.left_button = QPushButton("←")
        self.left_button.setEnabled(False)
        self.right_button = QPushButton("→")
        self.left_button.clicked.connect(self.left_clicked)
        self.right_button.clicked.connect(self.right_clicked)
        button_layout.addWidget(self.left_button)
        button_layout.addWidget(self.right_button)
        lrbuttons.setLayout(button_layout)
        layout.addWidget(lrbuttons)

        layout.addStretch()

        self.setLayout(layout)

    def clear_grid_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self.clear_grid_layout(sub_layout)

    def draw_grid(self):
        self.clear_grid_layout(self.grid_layout)
        colors = get_n_colours(len(self.channel_indices))
        for row, i in enumerate(self.channel_maps[self.electrode_index]):
            for col, j in enumerate(i):
                qcolor = QColor("gray")
                interactive = True
                if row == 0 and col == 0:
                    qcolor = QColor("white")
                    interactive = False
                elif j in self.channel_indices:
                    r, g, b, a = colors[min(len(colors) - 1, j - min(self.channel_indices))]
                    qcolor = QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255))
                square = SquareWidget(qcolor, j, self.change_index, interactive)
                if row != 0 or col != 0:
                    self.square_map[j] = square
                self.grid_layout.addWidget(square, row, col)

    def left_clicked(self):
        self.electrode_index -= 1
        self.update_grid()

    def right_clicked(self):
        self.electrode_index += 1
        self.update_grid()

    def update_indices(self, indices):
        self.channel_indices = indices

        lo = sum(self.chans_per_electrode[:self.electrode_index])
        hi = sum(self.chans_per_electrode[:(self.electrode_index + 1)])
        # no channels are in the current electrode
        if lo > max(indices) or min(indices) >= hi:
            self.electrode_index = 0
            total = self.chans_per_electrode[self.electrode_index]
            while min(indices) >= total:
                self.electrode_index += 1
                total += self.chans_per_electrode[self.electrode_index]

        self.update_grid()

    def update_grid(self):
        if self.electrode_index == 0:
            self.left_button.setEnabled(False)
        else:
            self.left_button.setEnabled(True)

        if self.electrode_index >= len(self.electrode_names) - 1:
            self.right_button.setEnabled(False)
        else:
            self.right_button.setEnabled(True)

        modifier = sum(self.chans_per_electrode[:self.electrode_index])

        colors = get_n_colours(len(self.channel_indices))
        for index, square in self.square_map.items():
            if modifier + index in self.channel_indices:
                r, g, b, a = colors[min(len(colors) - 1, modifier + index - min(self.channel_indices))]
                qcolor = QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255))
                square.setColor(qcolor)
                square.setIndex(index + modifier)
            else:
                square.setColor(QColor("gray"))
                square.setIndex(index + modifier)

        self.label.setText(f"{self.muscle_names[self.electrode_index]}")

        self.draw_grid()

    def init_grids(self):
        self.channel_maps = []
        self.chans_per_electrode = []
        for i, electrode_name in enumerate(self.electrode_names):
            if electrode_name == "GR04MM1305":
                self.channel_maps.append(
                    [
                        [0, 24, 25, 50, 51],
                        [0, 23, 26, 49, 52],
                        [1, 22, 27, 48, 53],
                        [2, 21, 28, 47, 54],
                        [3, 20, 29, 46, 55],
                        [4, 19, 30, 45, 56],
                        [5, 18, 31, 44, 57],
                        [6, 17, 32, 43, 58],
                        [7, 16, 33, 42, 59],
                        [8, 15, 34, 41, 60],
                        [9, 14, 35, 40, 61],
                        [10, 13, 36, 39, 62],
                        [11, 12, 37, 38, 63],
                    ]
                )
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]) - 1)

            elif electrode_name == "ELSCH064NM2":
                self.channel_maps.append(
                    [
                        [0, 0, 1, 2, 3],
                        [15, 7, 6, 5, 4],
                        [14, 13, 12, 11, 10],
                        [18, 17, 16, 8, 9],
                        [19, 20, 21, 22, 23],
                        [27, 28, 29, 30, 31],
                        [24, 25, 26, 32, 33],
                        [34, 35, 36, 37, 38],
                        [44, 45, 46, 47, 39],
                        [43, 42, 41, 40, 38],
                        [53, 52, 51, 50, 49],
                        [54, 55, 63, 62, 61],
                        [56, 57, 58, 59, 60],
                    ]
                )
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]) - 1)

            elif electrode_name == "GR08MM1305":
                self.channel_maps.append(
                    [
                        [0, 24, 25, 50, 51],
                        [0, 23, 26, 49, 52],
                        [1, 22, 27, 48, 53],
                        [2, 21, 28, 47, 54],
                        [3, 20, 29, 46, 55],
                        [4, 19, 30, 45, 56],
                        [5, 18, 31, 44, 57],
                        [6, 17, 32, 43, 58],
                        [7, 16, 33, 42, 59],
                        [8, 15, 34, 41, 60],
                        [9, 14, 35, 40, 61],
                        [10, 13, 36, 39, 62],
                        [11, 12, 37, 38, 63],
                    ]
                )
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]) - 1)

            elif electrode_name == "GR10MM0808":
                self.channel_maps.append(
                    [
                        [7, 15, 23, 31, 39, 47, 55, 63],
                        [6, 14, 22, 30, 38, 46, 54, 62],
                        [5, 13, 21, 29, 37, 45, 53, 61],
                        [4, 12, 20, 28, 36, 44, 52, 60],
                        [3, 11, 19, 27, 35, 43, 51, 59],
                        [2, 10, 18, 26, 34, 42, 50, 58],
                        [1, 9, 17, 25, 33, 41, 49, 57],
                        [0, 8, 16, 24, 32, 40, 48, 56],
                    ]
                )
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]) - 1)

            elif electrode_name == "other":
                self.channel_maps.append(
                    [
                        [0, 24, 25, 50, 51],
                        [0, 23, 26, 49, 52],
                        [1, 22, 27, 48, 53],
                        [2, 21, 28, 47, 54],
                        [3, 20, 29, 46, 55],
                        [4, 19, 30, 45, 56],
                        [5, 18, 31, 44, 57],
                        [6, 17, 32, 43, 58],
                        [7, 16, 33, 42, 59],
                        [8, 15, 34, 41, 60],
                        [9, 14, 35, 40, 61],
                        [10, 13, 36, 39, 62],
                        [11, 12, 37, 38, 63],
                    ]
                )
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]) - 1)

            elif electrode_name == "Thin film":
                self.channel_maps.append(
                    [
                        [0, 10, 20, 30],
                        [1, 11, 21, 31],
                        [2, 12, 22, 32],
                        [3, 13, 23, 33],
                        [4, 14, 24, 34],
                        [5, 15, 25, 35],
                        [6, 16, 26, 36],
                        [7, 17, 27, 37],
                        [8, 18, 28, 38],
                        [9, 19, 29, 39],
                    ]
                )
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]))

            elif electrode_name == "4-wire needle":
                self.channel_maps.append([[0, 8], [1, 9], [2, 10], [3, 11], [4, 12], [5, 13], [6, 14], [7, 15]])
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]))

            elif electrode_name == "Myomatrix Monopolar":
                self.channel_maps.append(
                    [
                        [0, 8, 16, 24],
                        [1, 9, 17, 25],
                        [2, 10, 18, 26],
                        [3, 11, 19, 27],
                        [4, 12, 20, 28],
                        [5, 13, 21, 29],
                        [6, 14, 22, 30],
                        [7, 15, 23, 31],
                    ]
                )
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]))

            else:
                # assume that it is some variation of an intramusuclar array
                self.channel_maps.append([[0, 8], [1, 9], [2, 10], [3, 11], [4, 12], [5, 13], [6, 14], [7, 15]])
                self.channel_maps[i] = np.squeeze(np.array(self.channel_maps[i]))
                self.chans_per_electrode.append((np.shape(self.channel_maps[i])[0] * np.shape(self.channel_maps[i])[1]))

def get_n_colours(n):
    cmap = cm.get_cmap('hsv')
    return [cmap(i / n) for i in range(n)]
