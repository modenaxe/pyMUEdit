"""
Navigator module to handle transitions between different screens in the application.
This centralizes the navigation logic and prevents import path problems.
"""

import os
import sys
import importlib.util
import traceback

# Add necessary paths
def ensure_paths_in_sys_path():
    """Ensure all necessary paths are in sys.path"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # project root
    
    paths_to_add = [
        project_root,
        current_dir,
        os.path.join(current_dir, 'views'),
        os.path.join(current_dir, 'views', 'Algorithm_Selection_Decomposition')
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.append(path)

def get_decomposition_app_class():
    """Locate and return the DecompositionApp class"""
    ensure_paths_in_sys_path()
    
    # First try the proper import
    try:
        from views.Algorithm_Selection_Decomposition.algo_select_screen import DecompositionApp
        return DecompositionApp
    except ImportError:
        pass
    
    # Try alternative import paths
    try:
        from algo_select_screen import DecompositionApp
        return DecompositionApp
    except ImportError:
        pass
    
    # Try loading from file directly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    views_path = os.path.join(current_dir, 'views')
    algos_path = os.path.join(views_path, 'Algorithm_Selection_Decomposition')
    
    # Try with underscore
    module_path = os.path.join(algos_path, 'algo_select_screen.py')
    if os.path.exists(module_path):
        try:
            spec = importlib.util.spec_from_file_location("decomp_app", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.DecompositionApp
        except Exception:
            traceback.print_exc()
    
    # Try with hyphen
    module_path = os.path.join(algos_path, 'algo-select-screen.py')
    if os.path.exists(module_path):
        try:
            spec = importlib.util.spec_from_file_location("decomp_app", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.DecompositionApp
        except Exception:
            traceback.print_exc()
    
    raise ImportError("Could not find DecompositionApp class")

def open_algorithm_screen(parent_window, filename, pathname, signal_data):
    """
    Open the algorithm selection screen with the given data
    
    Args:
        parent_window: The window that's opening the algorithm screen
        filename: The name of the file that was imported
        pathname: The path to the directory containing the file
        signal_data: The imported signal data
    
    Returns:
        The algorithm screen window instance if successful, None otherwise
    """
    try:
        # Get the DecompositionApp class
        DecompositionApp = get_decomposition_app_class()
        
        # Create the window
        algo_window = DecompositionApp()
        
        # Set the filename and pathname
        algo_window.filename = filename
        algo_window.pathname = pathname
        
        # Update UI
        algo_window.edit_field_saving_3.setText(filename)
        
        # Update reference dropdown
        algo_window.reference_dropdown.blockSignals(True)
        algo_window.reference_dropdown.clear()
        
        # Update the list of signals for reference
        if "auxiliaryname" in signal_data:
            algo_window.reference_dropdown.addItem("EMG amplitude")
            for name in signal_data["auxiliaryname"]:
                algo_window.reference_dropdown.addItem(str(name))
        elif "target" in signal_data:
            algo_window.reference_dropdown.addItem("EMG amplitude")
            algo_window.reference_dropdown.addItem("Path")
            algo_window.reference_dropdown.addItem("Target")
        else:
            algo_window.reference_dropdown.addItem("EMG amplitude")
        
        algo_window.reference_dropdown.blockSignals(False)
        
        # Enable configuration button if needed
        if hasattr(algo_window, 'set_configuration_button'):
            algo_window.set_configuration_button.setEnabled(True)
        
        # Return the window
        return algo_window
    
    except Exception as e:
        print(f"Error opening algorithm screen: {e}")
        traceback.print_exc()
        return None