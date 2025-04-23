import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class VisualizationStorage:
    """
    Class to handle storage of recent decomposition visualizations metadata and state.
    This allows the dashboard to list and reload previous decomposition sessions.
    """
    
    DEFAULT_STORAGE_FILE = "recent_visualizations.json"
    MAX_STORED_VISUALIZATIONS = 10  # Maximum number of visualizations to keep in history
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the visualization storage.
        
        Args:
            storage_path: Optional custom path to store the visualization metadata.
                          If None, defaults to the user's home directory.
        """
        if storage_path is None:
            # Create a .hdemg folder in the user's home directory
            home_dir = Path.home()
            self.storage_dir = home_dir / ".hdemg"
            self.storage_dir.mkdir(exist_ok=True)
            self.storage_file = self.storage_dir / self.DEFAULT_STORAGE_FILE
        else:
            self.storage_file = Path(storage_path)
            
        # Create the file if it doesn't exist
        if not self.storage_file.exists():
            self._save_visualizations([])
    
    def add_visualization(self, 
                         title: str, 
                         filepath: str, 
                         parameters: Dict[str, Any],
                         viz_state: Optional[Dict[str, Any]] = None,
                         timestamp: Optional[datetime.datetime] = None) -> None:
        """
        Add a visualization to recent history.
        
        Args:
            title: Title of the visualization
            filepath: Path to the saved decomposition file
            parameters: Algorithm parameters used for decomposition
            viz_state: Dictionary containing visualization state in native Python format
            timestamp: Optional timestamp, defaults to current time
        """
        visualizations = self.get_visualizations()
        
        # Create new visualization entry
        if timestamp is None:
            timestamp = datetime.datetime.now()
            
        # Convert to ISO format string for JSON serialization
        timestamp_str = timestamp.isoformat()
        
        new_viz = {
            "title": title,
            "filepath": filepath,
            "parameters": parameters,
            "viz_state": viz_state,  # Store visualization state as native Python structure
            "timestamp": timestamp_str,
            "id": f"viz_{int(timestamp.timestamp())}",  # Generate a unique ID from timestamp
            "type": "hdemg"  # Default type
        }
        
        # Check if a visualization with the same filepath already exists
        existing_index = next(
            (i for i, viz in enumerate(visualizations) 
             if viz.get("filepath") == filepath), 
            None
        )
        
        if existing_index is not None:
            # Update existing entry
            visualizations[existing_index] = new_viz
        else:
            # Add new entry
            visualizations.insert(0, new_viz)
            
        # Trim list if needed
        if len(visualizations) > self.MAX_STORED_VISUALIZATIONS:
            visualizations = visualizations[:self.MAX_STORED_VISUALIZATIONS]
            
        # Save updated list
        self._save_visualizations(visualizations)
    
    def get_visualizations(self) -> List[Dict[str, Any]]:
        """
        Get the list of recent visualizations.
        
        Returns:
            List of visualization metadata dictionaries
        """
        try:
            with open(self.storage_file, 'r') as f:
                visualizations = json.load(f)
                
            # Add formatted date for display
            for viz in visualizations:
                if "timestamp" in viz:
                    try:
                        timestamp = datetime.datetime.fromisoformat(viz["timestamp"])
                        now = datetime.datetime.now()
                        delta = now - timestamp
                        
                        if delta.days == 0:
                            viz["date"] = f"Last modified: Today"
                        elif delta.days == 1:
                            viz["date"] = f"Last modified: Yesterday"
                        else:
                            viz["date"] = f"Last modified: {timestamp.strftime('%b %d, %Y')}"
                    except (ValueError, TypeError):
                        viz["date"] = "Unknown date"
                else:
                    viz["date"] = "Unknown date"
                    
            return visualizations
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_visualizations(self, visualizations: List[Dict[str, Any]]) -> None:
        """
        Save the visualizations list to storage.
        
        Args:
            visualizations: List of visualization metadata to save
        """
        with open(self.storage_file, 'w') as f:
            json.dump(visualizations, f, indent=2)
    
    def get_visualization_by_id(self, viz_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific visualization by its ID.
        
        Args:
            viz_id: The unique identifier of the visualization
            
        Returns:
            The visualization data or None if not found
        """
        visualizations = self.get_visualizations()
        for viz in visualizations:
            if viz.get("id") == viz_id:
                return viz
        return None
    
    def remove_visualization(self, viz_id: str) -> bool:
        """
        Remove a visualization from history.
        
        Args:
            viz_id: The unique identifier of the visualization to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        visualizations = self.get_visualizations()
        initial_count = len(visualizations)
        
        visualizations = [viz for viz in visualizations if viz.get("id") != viz_id]
        
        if len(visualizations) < initial_count:
            self._save_visualizations(visualizations)
            return True
        return False