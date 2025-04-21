import os
import json
from datetime import datetime
import traceback


class VisualizationManager:
    """
    Manages saving, loading, and tracking visualization metadata for the HDEMG Dashboard.
    This class provides functionality to store and retrieve information about decomposition
    visualizations that have been created by the user.
    """

    def __init__(self, base_storage_dir=None):
        """
        Initialize the visualization manager.
        
        Args:
            base_storage_dir (str, optional): Directory to store visualization data.
                If None, defaults to a subdirectory in the user's home directory.
        """
        if base_storage_dir is None:
            self.base_dir = os.path.join(os.path.expanduser("~"), ".hdemg_dashboard")
        else:
            self.base_dir = base_storage_dir
            
        self.vis_dir = os.path.join(self.base_dir, "visualizations")
        self.metadata_file = os.path.join(self.base_dir, "visualization_index.json")
        
        # Create directories if they don't exist
        os.makedirs(self.vis_dir, exist_ok=True)
        
        # Load existing visualization index or create a new one
        self.visualizations = self._load_visualization_index()
    
    def _load_visualization_index(self):
        """Load the visualization index from disk or create a new one if it doesn't exist."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            else:
                return {"visualizations": []}
        except Exception as e:
            print(f"Error loading visualization index: {e}")
            traceback.print_exc()
            return {"visualizations": []}
    
    def _save_visualization_index(self):
        """Save the visualization index to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.visualizations, f, indent=2)
        except Exception as e:
            print(f"Error saving visualization index: {e}")
            traceback.print_exc()
    
    def add_visualization(self, title, filename, parameters, result_path=None, icon_type="hdemg"):
        """
        Add a new visualization to the index.
        
        Args:
            title (str): Title of the visualization
            filename (str): Original data filename
            parameters (dict): Parameters used for decomposition
            result_path (str, optional): Path to saved result file
            icon_type (str, optional): Type of icon to use
            
        Returns:
            str: ID of the visualization
        """
        vis_id = f"vis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        new_vis = {
            "id": vis_id,
            "title": title,
            "filename": filename,
            "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "parameters": parameters,
            "result_path": result_path,
            "icon_type": icon_type
        }
        
        # Add to beginning of list (most recent first)
        self.visualizations["visualizations"].insert(0, new_vis)
        
        # Save the updated index
        self._save_visualization_index()
        
        return vis_id
    
    def get_recent_visualizations(self, limit=10):
        """
        Get a list of recent visualizations.
        
        Args:
            limit (int, optional): Maximum number of visualizations to return
            
        Returns:
            list: List of visualization metadata dictionaries
        """
        return self.visualizations["visualizations"][:limit]
    
    def get_visualization(self, vis_id):
        """
        Get a specific visualization by ID.
        
        Args:
            vis_id (str): ID of the visualization to retrieve
            
        Returns:
            dict: Visualization metadata or None if not found
        """
        for vis in self.visualizations["visualizations"]:
            if vis["id"] == vis_id:
                return vis
        return None
    
    def update_visualization(self, vis_id, updates):
        """
        Update an existing visualization's metadata.
        
        Args:
            vis_id (str): ID of the visualization to update
            updates (dict): Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        for i, vis in enumerate(self.visualizations["visualizations"]):
            if vis["id"] == vis_id:
                # Update fields
                for key, value in updates.items():
                    self.visualizations["visualizations"][i][key] = value
                
                # Always update modified timestamp
                self.visualizations["visualizations"][i]["modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Save the updated index
                self._save_visualization_index()
                return True
        
        return False
    
    def delete_visualization(self, vis_id):
        """
        Delete a visualization from the index.
        
        Args:
            vis_id (str): ID of the visualization to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        for i, vis in enumerate(self.visualizations["visualizations"]):
            if vis["id"] == vis_id:
                # Remove from list
                del self.visualizations["visualizations"][i]
                
                # Save the updated index
                self._save_visualization_index()
                return True
        
        return False