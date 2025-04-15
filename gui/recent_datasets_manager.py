import os
import json
import datetime
from pathlib import Path

class RecentDatasetsManager:
    """
    Manages the tracking of recent datasets used in the application.
    Stores dataset information in a JSON file for persistence across sessions.
    """
    
    def __init__(self, max_entries=10):
        """
        Initialize the recent datasets manager.
        
        Args:
            max_entries: Maximum number of recent datasets to keep track of
        """
        self.max_entries = max_entries
        self.config_dir = os.path.join(str(Path.home()), '.hdemg_app')
        self.config_file = os.path.join(self.config_dir, 'recent_datasets.json')
        self.recent_datasets = []
        
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Load existing recent datasets if available
        self.load_recent_datasets()
    
    def load_recent_datasets(self):
        """Load recent datasets from the config file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.recent_datasets = json.load(f)
            except (json.JSONDecodeError, IOError):
                # Reset if file is corrupted
                self.recent_datasets = []
        else:
            self.recent_datasets = []
    
    def save_recent_datasets(self):
        """Save recent datasets to the config file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.recent_datasets, f)
        except IOError as e:
            print(f"Error saving recent datasets: {e}")
    
    def add_dataset(self, filepath, dataset_type="Decomposition Result", filesize=None, row_count=None):
        """
        Add a dataset to the recent datasets list.
        
        Args:
            filepath: Full path to the dataset file
            dataset_type: Type of the dataset (e.g., "Decomposition Result")
            filesize: Size of the file in bytes (will be calculated if None)
            row_count: Number of rows/items in the dataset (optional)
        """
        # Get file information
        filename = os.path.basename(filepath)
        
        # Calculate file size if not provided
        if filesize is None and os.path.exists(filepath):
            filesize = os.path.getsize(filepath)
        
        # Format file size for display
        if filesize:
            if filesize < 1024:
                filesize_str = f"{filesize} B"
            elif filesize < 1024 * 1024:
                filesize_str = f"{filesize/1024:.1f} KB"
            else:
                filesize_str = f"{filesize/(1024*1024):.1f} MB"
        else:
            filesize_str = "Unknown size"
        
        # Format row count if provided
        if row_count:
            metadata = f"{filesize_str} • {row_count:,} rows"
        else:
            metadata = filesize_str
        
        # Create dataset entry
        dataset_entry = {
            "filename": filename,
            "filepath": filepath,
            "type": dataset_type,
            "metadata": metadata,
            "date_added": datetime.datetime.now().isoformat(),
            "filesize": filesize,
            "filesize_str": filesize_str
        }
        
        # Remove existing entry with the same filename if it exists
        self.recent_datasets = [d for d in self.recent_datasets if d["filepath"] != filepath]
        
        # Add new entry at the beginning
        self.recent_datasets.insert(0, dataset_entry)
        
        # Truncate list if necessary
        if len(self.recent_datasets) > self.max_entries:
            self.recent_datasets = self.recent_datasets[:self.max_entries]
        
        # Save updated list
        self.save_recent_datasets()
    
    def get_recent_datasets(self, count=None):
        """
        Get the list of recent datasets.
        
        Args:
            count: Number of datasets to return (None for all)
            
        Returns:
            List of recent dataset entries
        """
        if count is None or count >= len(self.recent_datasets):
            return self.recent_datasets
        return self.recent_datasets[:count]
    
    def clear_recent_datasets(self):
        """Clear all recent datasets."""
        self.recent_datasets = []
        self.save_recent_datasets()
    
    def remove_dataset(self, filepath):
        """
        Remove a specific dataset from the recent list.
        
        Args:
            filepath: Path of the dataset to remove
        """
        self.recent_datasets = [d for d in self.recent_datasets if d["filepath"] != filepath]
        self.save_recent_datasets()
    
    def dataset_exists(self, filepath):
        """
        Check if a dataset already exists in the recent list.
        
        Args:
            filepath: Path of the dataset to check
            
        Returns:
            True if the dataset exists, False otherwise
        """
        return any(d["filepath"] == filepath for d in self.recent_datasets)