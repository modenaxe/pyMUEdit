import sys
import traceback
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QPushButton, QStyle, QMessageBox
from PyQt5.QtCore import Qt
from datetime import datetime

# Import UI setup function - using your existing function
from ui.HDEMGDashboardUI import setup_ui, update_sidebar_selection

# Import for external windows/widgets
from ImportDataWindow import ImportDataWindow
from ui.MUAnalysisUI import MUAnalysis
from ExportResults import ExportResultsWindow
from DecompositionApp import DecompositionApp
from VisualizationManager import VisualizationManager


class HDEMGDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Instance variables for external windows/widgets
        self.import_data_page = None
        self.export_results_window = None
        self.mu_analysis_page = None
        self.manual_editing_page = None
        self.decomposition_page = None
        self.current_decomposition_app = None

        # Initialize visualization manager
        self.visualization_manager = VisualizationManager()

        # Colors and recent items for demonstration
        self.colors = {
            "bg_main": "#f5f5f5",
            "bg_sidebar": "#f0f0f0",
            "bg_card": "#e8e8e8",
            "bg_card_hdemg": "#1a73e8",
            "bg_card_neuro": "#7cb342",
            "bg_card_emg": "#e91e63",
            "bg_card_eeg": "#9c27b0",
            "bg_card_default": "#607d8b",
            "border": "#d0d0d0",
            "text_primary": "#333333",
            "text_secondary": "#777777",
            "accent": "#000000",
            "sidebar_selected_bg": "#e6e6e6",
        }

        # Load recent visualizations from manager
        self.recent_visualizations = self._load_recent_visualizations()
        
        # Sample data for recent datasets (you may want to implement dataset tracking too)
        self.recent_datasets = [
            {"filename": "HDEMG_Analysis2025.csv", "metadata": "2.5MB • 1,000 rows"},
            {"filename": "NeuroSignal_Analysis.xlsx", "metadata": "1.8MB • 750 rows"},
            {"filename": "EMG_Recording23.dat", "metadata": "3.2MB • 1,500 rows"},
            {"filename": "EEG_Study_Jan2025.csv", "metadata": "5.1MB • 2,200 rows"},
        ]

        # Initialize external widgets if available
        self.initialize_external_widgets()

        # Set up the UI components by calling the function from HDEMGDashboardUI.py
        setup_ui(self)

        # Connect signals to slots
        self.connect_signals()

        # Start on dashboard view
        self.show_dashboard_view()

    def _load_recent_visualizations(self):
        """Load recent visualizations from the visualization manager and format for the UI."""
        try:
            recent_vis_data = self.visualization_manager.get_recent_visualizations()
            ui_vis_data = []
            
            for vis in recent_vis_data:
                # Format the visualization data for the UI
                title = vis.get("title", "Unnamed Visualization")
                date_str = f"Last modified: {vis.get('modified', 'Unknown date')}"
                vis_type = vis.get("icon_type", "hdemg")
                
                # Get appropriate icon for visualization type
                icon_mapping = {
                    "hdemg": getattr(QStyle, "SP_FileDialogDetailedView"),
                    "neuro": getattr(QStyle, "SP_DialogApplyButton"),
                    "emg": getattr(QStyle, "SP_FileDialogInfoView"),
                    "eeg": getattr(QStyle, "SP_DialogHelpButton"),
                    "default": getattr(QStyle, "SP_FileDialogDetailedView")
                }
                icon = icon_mapping.get(vis_type, icon_mapping["default"])
                
                ui_vis_data.append({
                    "title": title,
                    "date": date_str,
                    "type": vis_type,
                    "icon": icon,
                    "id": vis.get("id", "unknown_id")  # Store the ID for loading later
                })
            
            return ui_vis_data
            
        except Exception as e:
            print(f"Error loading recent visualizations: {e}")
            traceback.print_exc()
            return []

    def initialize_external_widgets(self):
        """Initialize external widgets if their modules are available."""
        # Initialize MU Analysis page
        if MUAnalysis:
            self.mu_analysis_page = MUAnalysis()
            self.mu_analysis_page.return_to_dashboard_requested.connect(self.show_dashboard_view)
            if hasattr(self.mu_analysis_page, "set_export_window_opener"):
                self.mu_analysis_page.set_export_window_opener(self.open_export_results_window)
            else:
                print("WARNING: MotorUnitAnalysisWidget does not have 'set_export_window_opener' method.")

        # Initialize Import Data page
        if ImportDataWindow:
            self.import_data_page = ImportDataWindow(parent=self)
            # Use the correct windowflags
            self.import_data_page.setWindowFlags(getattr(Qt.WindowType, "Widget"))
            if hasattr(self.import_data_page, "return_to_dashboard_requested"):
                self.import_data_page.return_to_dashboard_requested.connect(self.show_dashboard_view)

    def connect_signals(self):
        """Connect UI signals to slot methods."""
        # Connect sidebar buttons
        self.sidebar_buttons["dashboard"].clicked.connect(self.show_dashboard_view)
        self.sidebar_buttons["mu_analysis"].clicked.connect(self.show_mu_analysis_view)
        self.sidebar_buttons["decomposition"].clicked.connect(self.show_decomposition_view)
        self.sidebar_buttons["manual_edit"].clicked.connect(self.show_manual_editing_view)

        if ImportDataWindow:
            self.sidebar_buttons["import"].clicked.connect(self.show_import_data_view)
        else:
            self.sidebar_buttons["import"].setEnabled(False)

        if not MUAnalysis:
            self.sidebar_buttons["mu_analysis"].setEnabled(False)

        # Connect "New Analysis" button on the dashboard
        new_viz_btn = None
        content_widget = self.dashboard_page.widget()
        if content_widget and content_widget.layout():
            for layout_idx in range(content_widget.layout().count()):
                item = content_widget.layout().itemAt(layout_idx)
                if item and isinstance(item.layout(), QHBoxLayout):
                    for i in range(item.layout().count()):
                        layout_item = item.layout().itemAt(i)
                        if layout_item and layout_item.widget():
                            widget = layout_item.widget()
                            if isinstance(widget, QPushButton) and widget.text() == "+ New Analysis":
                                new_viz_btn = widget
                                break
                if new_viz_btn:
                    break

        if new_viz_btn and ImportDataWindow:
            new_viz_btn.clicked.connect(self.show_import_data_view)
            
        # Connect visualization cards if they exist
        self.connect_visualization_cards()

    def connect_visualization_cards(self):
        """Connect click handlers for visualization cards."""
        # Find the viz container in the dashboard
        try:
            content_widget = self.dashboard_page.widget()
            if not content_widget:
                return
                
            # Look for frames in the visualization section
            viz_cards = content_widget.findChildren(QFrame, lambda name: name.startswith("vizCard_"))
            
            for card in viz_cards:
                # Connect directly to the open_visualization method
                title = card.property("title")
                vis_id = card.property("vis_id")
                if title and vis_id:
                    card.mousePressEvent = lambda event, t=title, v=vis_id: self.open_visualization(t, v)
        except Exception as e:
            print(f"Error connecting visualization cards: {e}")
            traceback.print_exc()

    # Navigation methods
    def show_dashboard_view(self):
        """Switches the central widget to the dashboard page."""
        print("Switching to Dashboard View")
        
        # Refresh recent visualizations when returning to dashboard
        self.recent_visualizations = self._load_recent_visualizations()
        
        # We don't recreate the dashboard page - use the existing one from setup_ui
        self.central_stacked_widget.setCurrentWidget(self.dashboard_page)
        update_sidebar_selection(self, "dashboard")
        
        # Update visualization cards - this function should be implemented in HDEMGDashboardUI.py
        # If not available, you'll need to adapt your UI to support this
        self.connect_visualization_cards()

    def show_mu_analysis_view(self):
        """Switches the central widget to the MU Analysis page."""
        if hasattr(self, "mu_analysis_page") and self.mu_analysis_page:
            print("Switching to MU Analysis View")
            self.central_stacked_widget.setCurrentWidget(self.mu_analysis_page)
            update_sidebar_selection(self, "mu_analysis")
        else:
            print("MU Analysis view is not available.")

    def show_import_data_view(self):
        """Switches the central widget to the Import Data page."""
        if ImportDataWindow is None or self.import_data_page is None:
            print("ImportDataWindow not available.")
            return
        print("Switching to Import Data view")
        self.central_stacked_widget.setCurrentWidget(self.import_data_page)
        update_sidebar_selection(self, "import")

    def show_manual_editing_view(self):
        """Switches to Manual Editing view."""
        print("Switching to Manual Editing View")
        if hasattr(self, "manual_editing_page") and self.manual_editing_page:
            self.central_stacked_widget.setCurrentWidget(self.manual_editing_page)
            update_sidebar_selection(self, "manual_edit")
        else:
            print("Manual Editing view widget not found.")

    def show_decomposition_view(self):
        """Switches to Decomposition view."""
        print("Switching to Decomposition View")
        if hasattr(self, "decomposition_page") and self.decomposition_page:
            self.central_stacked_widget.setCurrentWidget(self.decomposition_page)
            update_sidebar_selection(self, "decomposition")
        else:
            print("Decomposition view widget not found.")

    def open_visualization(self, title, vis_id=None):
        """Handles clicks on visualization cards."""
        print(f"Clicked visualization/analysis card: {title}")
        
        if vis_id:
            # Get the visualization data from the manager
            vis_data = self.visualization_manager.get_visualization(vis_id)
            
            if vis_data:
                # Open the visualization in DecompositionApp
                self.load_saved_visualization(vis_data)
            else:
                QMessageBox.warning(self, "Visualization Not Found", 
                                   f"The visualization '{title}' could not be found.")
        else:
            print(f"No ID provided for visualization '{title}'. Cannot load.")

    def load_saved_visualization(self, vis_data):
        """
        Loads a saved visualization into a new DecompositionApp instance.
        
        Args:
            vis_data (dict): The visualization data from the visualization manager
        """
        try:
            print(f"Loading visualization: {vis_data.get('title')}")
            
            # Check if the result file exists
            result_path = vis_data.get('result_path')
            if not result_path or not os.path.exists(result_path):
                QMessageBox.warning(self, "File Not Found", 
                                    f"The result file for this visualization could not be found at: {result_path}")
                return
            
            # Create a new DecompositionApp instance
            self.current_decomposition_app = DecompositionApp(
                filename=vis_data.get('filename'),
                pathname=os.path.dirname(result_path),
                parameters=vis_data.get('parameters'),
                result_file=result_path
            )
            
            # Set parent dashboard for communication
            self.current_decomposition_app.set_parent_dashboard(self)
            
            # Connect back button
            if hasattr(self.current_decomposition_app, "back_to_import"):
                self.current_decomposition_app.back_to_import_btn.clicked.connect(self.on_decomp_app_closed)
            
            # Show the DecompositionApp
            self.current_decomposition_app.show()
            
            # Update the visualization's last modified date
            self.visualization_manager.update_visualization(
                vis_data['id'], 
                {'modified': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading the visualization: {str(e)}")
            print(f"Error loading visualization: {e}")
            traceback.print_exc()

    def on_decomp_app_closed(self):
        """Handle when decomposition app is closed."""
        # Show the dashboard again
        self.show()
        
        # Close the decomposition app
        if self.current_decomposition_app:
            self.current_decomposition_app.hide()
            self.current_decomposition_app = None
        
        # Refresh the dashboard view
        self.show_dashboard_view()

    def on_decomposition_complete(self, emg_obj, filename, pathname, result_path, parameters):
        """
        Called when a decomposition is complete to save its visualization data.
        
        Args:
            emg_obj: The EMG object with decomposition results
            filename: Original filename
            pathname: Original path
            result_path: Path to saved result file
            parameters: Parameters used for decomposition
        """
        try:
            # Create a title based on the filename
            title = f"HDEMG Analysis - {filename}"
            
            # Add the visualization to the manager
            vis_id = self.visualization_manager.add_visualization(
                title=title,
                filename=filename,
                parameters=parameters,
                result_path=result_path,
                icon_type="hdemg"
            )
            
            print(f"Added new visualization with ID: {vis_id}")
            
            # Refresh the dashboard view
            self.recent_visualizations = self._load_recent_visualizations()
            
        except Exception as e:
            print(f"Error saving visualization data: {e}")
            traceback.print_exc()

    def open_export_results_window(self):
        """Opens the Export Results window, creating it if necessary."""
        print(">>> Main Window: Request received to open Export Results window.")
        if ExportResultsWindow is None:
            print("ERROR: ExportResultsWindow class is not available (check import).")
            return

        window_exists = False
        if self.export_results_window:
            try:
                # Check if the window still exists and hasn't been closed/deleted
                if self.export_results_window.isVisible() or not self.export_results_window.isHidden():
                    window_exists = True
                    print(">>> Main Window: Existing ExportResultsWindow instance seems valid.")
                else:
                    print(
                        ">>> Main Window: Existing window reference present but window is hidden/closed; will create new."
                    )
                    self.export_results_window = None  # Force recreation
                    window_exists = False
            except RuntimeError:  # Window was likely deleted
                print(">>> Main Window: Existing window reference invalid (RuntimeError); will create new.")
                self.export_results_window = None
                window_exists = False
            except Exception as e:  # Catch other potential issues
                print(f">>> Main Window: Error checking existing window ({type(e).__name__}); will create new.")
                self.export_results_window = None
                window_exists = False

        if not window_exists:
            try:
                print(">>> Main Window: Creating NEW ExportResultsWindow instance.")
                # Ensure it's created as a top-level window (parent=None)
                self.export_results_window = ExportResultsWindow(parent=None)
                # Position it relative to the main window for convenience
                main_geo = self.geometry()
                new_x = main_geo.x() + 100
                new_y = main_geo.y() + 100
                width = 600  # Define desired size
                height = 550
                self.export_results_window.setGeometry(new_x, new_y, width, height)
                print(f">>> Set geometry for new window to ({new_x}, {new_y}, {width}, {height})")
            except Exception as e:
                print(f"FATAL ERROR during ExportResultsWindow creation: {e}")
                traceback.print_exc()
                self.export_results_window = None  # Ensure it's None if creation failed
                return  # Stop execution here

        # After potentially creating or confirming existence, try to show/activate
        if self.export_results_window:
            try:
                print(">>> Main Window: Attempting to show and activate ExportResultsWindow.")
                self.export_results_window.show()
                self.export_results_window.raise_()  # Bring to front
                self.export_results_window.activateWindow()  # Give focus
                QApplication.processEvents()  # Ensure UI updates
                print(">>> ExportResultsWindow shown and activated.")
            except RuntimeError:  # Catch if window was deleted between check and show
                print(">>> Error: ExportResultsWindow was deleted before it could be shown.")
                self.export_results_window = None
            except Exception as e:
                print(f"Error displaying/activating ExportResultsWindow: {e}")
                traceback.print_exc()
        else:
            print("ERROR - self.export_results_window is None even after creation attempt.")


# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HDEMGDashboard()
    window.show()
    sys.exit(app.exec_())