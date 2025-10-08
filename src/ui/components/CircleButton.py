from PyQt5.QtWidgets import QPushButton


class CircleButton(QPushButton):
    def __init__(self, diameter=30):
        super().__init__()
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)
        self.setCheckable(True)
        self.setStyleSheet(self.style(False))
        self.toggled.connect(self.update_style)

    def update_style(self, checked):
        self.setStyleSheet(self.style(checked))

    def style(self, checked):
        if checked:
            # black background
            return f"""
                QPushButton {{
                    border-radius: {self.diameter // 2}px;
                    background-color: #626363;
                    border: 2px solid #626363;
                }}
            """
        else:
            # white background
            return f"""
                QPushButton {{
                    border-radius: {self.diameter // 2}px;
                    background-color: white;
                    border: 2px solid #626363;
                }}
            """
