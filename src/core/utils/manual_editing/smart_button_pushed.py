from functools import wraps
from core.logger import logger

def smart_button_pushed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.MUedition:
            logger.warning("NO MUedition")
            return
        func_name = func.__name__
        btn = self.action_buttons.get(func_name)
        
        if not btn:
            logger.warning(f"Warning NO '{func_name}' Matched Button")
            logger.debug(self.action_buttons)
            return

        if btn.get_active():
            for b in self.action_buttons.values():
                b.setEnabled(True)
                b.setProperty("active", False)
                b.style().unpolish(b)
                b.style().polish(b)
            lock = self.Backup["lock"]
            if lock == 1: 
                self.action_buttons["lock_spikes_button_pushed"].set_active(True) 
            self.selection_tool.disable()
            return
        else:
            for name, b in self.action_buttons.items():
                b.setEnabled(name == func_name)
                b.setProperty("active", name == func_name)
                b.style().unpolish(b)
                b.style().polish(b)
            
        return func(self)
    return wrapper