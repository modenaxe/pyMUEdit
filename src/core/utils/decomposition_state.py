import os
import pickle
import numpy as np
import time
import copy

# Path for saving decomposition states - Fixed to create in user home directory
HOME_DIR = os.path.expanduser("~")
STATES_DIR = os.path.join(HOME_DIR, "hdemg_states")


class DecompositionState:
    """Helper class to store and load decomposition states."""
    
    @staticmethod
    def ensure_state_directory():
        """Ensures that the states directory exists."""
        global STATES_DIR 
        
        if not os.path.exists(STATES_DIR):
            try:
                os.makedirs(STATES_DIR)
                print(f"Created states directory at {STATES_DIR}")
            except Exception as e:
                print(f"Error creating states directory: {e}")
                # Fallback to temp directory if home directory is not writable
                STATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "saved_states")
                if not os.path.exists(STATES_DIR):
                    os.makedirs(STATES_DIR)
                print(f"Using fallback states directory: {STATES_DIR}")
    
    @staticmethod
    def save_state(decomp_app, state_name=None):
        """
        Saves the current state of the decomposition screen to be loaded later.
        
        Args:
            decomp_app: The DecompositionApp instance
            state_name: Optional name for the state, defaults to timestamp + filename
        """
        DecompositionState.ensure_state_directory()
        
        # Generate default state name if none provided
        if not state_name:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            state_name = f"{timestamp}_{decomp_app.filename}"
        
        # Count total motor units
        total_mus = 0
        if hasattr(decomp_app, 'decomposition_result') and decomp_app.decomposition_result:
            result = decomp_app.decomposition_result
            if "Pulsetrain" in result:
                if isinstance(result["Pulsetrain"], dict):
                    for electrode, pulses in result["Pulsetrain"].items():
                        if hasattr(pulses, "shape"):
                            total_mus += pulses.shape[0]
                elif isinstance(result["Pulsetrain"], np.ndarray) and result["Pulsetrain"].size > 0:
                    # Handle MATLAB-style cell array format
                    for i in range(result["Pulsetrain"].shape[1]):
                        pulses = result["Pulsetrain"][0, i]
                        if hasattr(pulses, "shape"):
                            total_mus += pulses.shape[0]
        
        # Get SIL and CoV values
        sil_value = None
        cov_value = None
        if hasattr(decomp_app, 'sil_value_label'):
            sil_text = decomp_app.sil_value_label.text()
            if sil_text and ':' in sil_text:
                sil_value = sil_text.split(':', 1)[1].strip()
        
        if hasattr(decomp_app, 'cov_value_label'):
            cov_text = decomp_app.cov_value_label.text()
            if cov_text and ':' in cov_text:
                cov_value = cov_text.split(':', 1)[1].strip()
        
        # Save plot data from the PyQtGraph plot widgets
        plot_data = {}
        
        # Save reference plot data
        if hasattr(decomp_app, 'ui_plot_reference'):
            plot_data['reference'] = DecompositionState._extract_plot_data(decomp_app.ui_plot_reference)
            
        # Save pulse train plot data
        if hasattr(decomp_app, 'ui_plot_pulsetrain'):
            plot_data['pulsetrain'] = DecompositionState._extract_plot_data(decomp_app.ui_plot_pulsetrain)
        
        # Create a dictionary with all the important state information
        state = {
            # Basic metadata
            'filename': decomp_app.filename,
            'pathname': decomp_app.pathname,
            'timestamp': time.time(),
            'title': f"Analysis of {decomp_app.filename}",
            'description': f"Decomposition completed on {time.strftime('%Y-%m-%d %H:%M:%S')}",
            
            # UI configurations
            'ui_params': decomp_app.ui_params if hasattr(decomp_app, 'ui_params') else None,
            
            # Results summary
            'motor_units_count': str(total_mus),
            'sil_value': sil_value,
            'cov_value': cov_value,
            
            # Visualization data
            'current_plot_data': decomp_app.current_plot_data if hasattr(decomp_app, 'current_plot_data') else None,
            'plot_data': plot_data,  # New field for extracted plot data
            
            # EMG data for channel viewer (use a more safe approach)
            'emg_data': None,  # Will be set below if available
            
            # Decomposition result data (for reconstruction)
            'decomposition_result': decomp_app.decomposition_result if hasattr(decomp_app, 'decomposition_result') else None,
            
            # Path to the saved output file for reference
            'output_file': os.path.join(decomp_app.pathname, decomp_app.filename + "_output_decomp.mat") if decomp_app.pathname and decomp_app.filename else None,
        }
        
        # Try to safely extract EMG data for channel viewer
        try:
            if hasattr(decomp_app, 'emg_obj') and decomp_app.emg_obj:
                if hasattr(decomp_app.emg_obj, 'signal_dict'):
                    # Only save the EMG data array and essential metadata, not the full emg_obj
                    # to reduce serialization issues and file size
                    state['emg_data'] = {
                        'data': decomp_app.emg_obj.signal_dict.get('data', None),
                        'fsamp': decomp_app.emg_obj.signal_dict.get('fsamp', None),
                        'nchans': decomp_app.emg_obj.signal_dict.get('nchans', None)
                    }
                    print(f"EMG data extracted for channel viewer: {state['emg_data']['data'].shape if state['emg_data']['data'] is not None else 'None'}")
        except Exception as e:
            print(f"Warning: Failed to extract EMG data for channel viewer: {e}")
            # This is not critical, so continue with saving anyway
        
        # Create a special object for storing NumPy arrays
        serializable_state = DecompositionState._make_serializable(state)
        
        # Save the state
        state_path = os.path.join(STATES_DIR, f"{state_name}.decomp")
        print(f"Saving state to {state_path}")
        try:
            with open(state_path, 'wb') as f:
                pickle.dump(serializable_state, f)
            print(f"Successfully saved state with {total_mus} motor units")
        except Exception as e:
            print(f"Error saving state: {e}")
            import traceback
            traceback.print_exc()
        
        # Return metadata for the saved state
        return {
            'state_name': state_name,
            'state_path': state_path,
            'timestamp': state['timestamp'],
            'title': state['title'],
            'description': state['description'],
            'motor_units_count': state['motor_units_count'],
        }
    
    @staticmethod
    def _extract_plot_data(plot_widget):
        """
        Extracts data from a PyQtGraph plot widget to enable reconstruction.
        
        Args:
            plot_widget: A PyQtGraph PlotWidget
            
        Returns:
            Dictionary with plot data and configuration
        """
        if not plot_widget:
            return None
            
        plot_data = {
            'items': [],
            'title': plot_widget.plotItem.titleLabel.text if hasattr(plot_widget.plotItem, 'titleLabel') else None,
            'x_range': plot_widget.viewRange()[0] if hasattr(plot_widget, 'viewRange') else None,
            'y_range': plot_widget.viewRange()[1] if hasattr(plot_widget, 'viewRange') else None,
        }
        
        # Extract data from each plot item
        for item in plot_widget.plotItem.items:
            if hasattr(item, 'xData') and hasattr(item, 'yData'):
                # PlotDataItem
                # Get color information carefully
                pen_color = "#000000"  # Default black
                pen_width = 1
                pen_style = None
                
                if hasattr(item, 'opts') and isinstance(item.opts, dict):
                    pen_opt = item.opts.get('pen', None)
                    
                    # Handle different pen formats
                    if isinstance(pen_opt, dict):
                        pen_color = pen_opt.get('color', "#000000")
                        pen_width = pen_opt.get('width', 1)
                        pen_style = pen_opt.get('style', None)
                    elif hasattr(pen_opt, 'color') and callable(pen_opt.color):
                        pen_color = pen_opt.color().name()
                        pen_width = pen_opt.width() if hasattr(pen_opt, 'width') else 1
                    elif isinstance(pen_opt, str):
                        pen_color = pen_opt
                
                item_data = {
                    'type': 'plot',
                    'x_data': item.xData if hasattr(item, 'xData') else None,
                    'y_data': item.yData if hasattr(item, 'yData') else None,
                    'pen': {
                        'color': pen_color,
                        'width': pen_width,
                        'style': pen_style,
                    }
                }
                plot_data['items'].append(item_data)
            elif hasattr(item, 'pos') and item.__class__.__name__ == 'InfiniteLine':
                # InfiniteLine (for plateau markers)
                item_data = {
                    'type': 'infinite_line',
                    'pos': item.pos() if callable(item.pos) else None,
                    'angle': item.angle if hasattr(item, 'angle') else 90,
                    'pen': {
                        'color': item.pen.color().name() if hasattr(item.pen, 'color') else '#FF0000',
                        'width': item.pen.width() if hasattr(item.pen, 'width') else 1,
                    } if hasattr(item, 'pen') else None,
                }
                plot_data['items'].append(item_data)
            elif hasattr(item, 'data') and item.__class__.__name__ == 'ScatterPlotItem':
                # ScatterPlotItem (for spikes)
                try:
                    # There are different ways ScatterPlotItem might store its data
                    # Method 1: Direct access to x and y data arrays
                    if hasattr(item, 'xData') and hasattr(item, 'yData'):
                        x_values = item.xData
                        y_values = item.yData
                    # Method 2: Extracting from data structure
                    elif hasattr(item, 'data'):
                        # Sometimes data is a numpy array with fields 'x' and 'y'
                        if hasattr(item.data, 'dtype') and 'x' in item.data.dtype.names and 'y' in item.data.dtype.names:
                            x_values = item.data['x']
                            y_values = item.data['y']
                        # Sometimes it's a list of dictionaries
                        elif isinstance(item.data, list) and item.data and isinstance(item.data[0], dict):
                            x_values = [spot['x'] for spot in item.data]
                            y_values = [spot['y'] for spot in item.data]
                        else:
                            # Fallback if we can't determine the format
                            x_values = []
                            y_values = []
                    else:
                        x_values = []
                        y_values = []
                    
                    # Convert to list for serialization
                    if not isinstance(x_values, list):
                        x_values = list(x_values)
                    if not isinstance(y_values, list):
                        y_values = list(y_values)
                    
                    # Get styling properties
                    size = item.opts.get('size', 10) if hasattr(item, 'opts') else 10
                    
                    # Extract brush color safely
                    brush = '#FF0000'  # Default fallback
                    if hasattr(item, 'opts') and 'brush' in item.opts:
                        brush_obj = item.opts['brush']
                        # Check different brush formats
                        if hasattr(brush_obj, 'color') and callable(brush_obj.color):
                            brush = brush_obj.color().name()
                        elif isinstance(brush_obj, str):
                            brush = brush_obj
                    
                    item_data = {
                        'type': 'scatter',
                        'x_data': x_values,
                        'y_data': y_values,
                        'size': size,
                        'brush': brush,
                    }
                except Exception as e:
                    print(f"Error extracting scatter plot data: {e}")
                    # Create a minimal scatter item entry that won't cause problems
                    item_data = {
                        'type': 'scatter',
                        'x_data': [],
                        'y_data': [],
                        'size': 10,
                        'brush': '#FF0000',
                    }
                plot_data['items'].append(item_data)
        
        return plot_data
        
    @staticmethod
    def load_state(state_path):
        """
        Loads a saved decomposition state.
        
        Args:
            state_path: Path to the saved state file
        
        Returns:
            Dictionary with the complete state information
        """
        with open(state_path, 'rb') as f:
            state = pickle.load(f)
        
        # Convert serializable form back to original format
        return DecompositionState._restore_from_serializable(state)
    
    @staticmethod
    def list_saved_states():
        """
        Lists all saved decomposition states.
        
        Returns:
            List of dictionaries with state metadata
        """
        DecompositionState.ensure_state_directory()
        
        states = []
        if os.path.exists(STATES_DIR):
            for filename in os.listdir(STATES_DIR):
                if filename.endswith('.decomp'):
                    try:
                        state_path = os.path.join(STATES_DIR, filename)
                        with open(state_path, 'rb') as f:
                            state = pickle.load(f)
                        
                        # Extract basic metadata without full deserialization
                        metadata = {
                            'state_name': os.path.splitext(filename)[0],
                            'state_path': state_path,
                            'timestamp': state.get('timestamp', 0),
                            'title': state.get('title', 'Unknown Analysis'),
                            'description': state.get('description', ''),
                            'motor_units_count': state.get('motor_units_count', '?'),
                            'filename': state.get('filename', 'unknown.mat'),
                        }
                        states.append(metadata)
                    except Exception as e:
                        # Skip corrupted state files
                        print(f"Error reading state file {filename}: {e}")
                        continue
        
        # Sort by timestamp, newest first
        states.sort(key=lambda x: x['timestamp'], reverse=True)
        return states
    
    @staticmethod
    def delete_state(state_path):
        """Deletes a saved state file."""
        if os.path.exists(state_path):
            try:
                os.remove(state_path)
                print(f"Deleted state file: {state_path}")
                return True
            except Exception as e:
                print(f"Error deleting state file {state_path}: {e}")
        return False
    
    @staticmethod
    def _make_serializable(obj):
        """
        Convert objects containing NumPy arrays to serializable format.
        """
        if isinstance(obj, np.ndarray):
            return {
                '__type__': 'ndarray',
                'data': obj.tolist(),
                'dtype': str(obj.dtype),
                'shape': obj.shape
            }
        elif isinstance(obj, dict):
            return {k: DecompositionState._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DecompositionState._make_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return {
                '__type__': 'tuple',
                'data': [DecompositionState._make_serializable(item) for item in obj]
            }
        else:
            return obj
    
    @staticmethod
    def _restore_from_serializable(obj):
        """
        Restore objects from serializable format.
        """
        if isinstance(obj, dict):
            if '__type__' in obj:
                if obj['__type__'] == 'ndarray':
                    return np.array(obj['data'], dtype=np.dtype(obj['dtype']))
                elif obj['__type__'] == 'tuple':
                    return tuple(DecompositionState._restore_from_serializable(item) for item in obj['data'])
            return {k: DecompositionState._restore_from_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DecompositionState._restore_from_serializable(item) for item in obj]
        else:
            return obj