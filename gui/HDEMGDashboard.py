import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QPushButton, QStyle, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

# Import UI setup function
from ui.HDEMGDashboardUI import setup_ui, update_sidebar_selection

# Import for external windows/widgets
from ImportDataWindow import ImportDataWindow
from ui.MUAnalysisUI import MUAnalysis
from ExportResults import ExportResultsWindow
from DecompositionApp import DecompositionApp


class HDEMGDashboard(QMainWindow):
    def __init__(self):
        super().__init__()

        # Instance variables for external windows/widgets
        self.import_data_page = None
        self.export_results_window = None
        self.mu_analysis_page = None
        self.manual_editing_page = None
        self.decomposition_page = None

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

        # Sample data for the UI
        self.recent_visualizations = [
            {
                "title": "HDEMG Analysis",
                "date": "Last modified: Jan 15, 2025",
                "type": "hdemg",
                "icon": getattr(QStyle, "SP_FileDialogDetailedView"),
            },
            {
                "title": "Neuro Analysis",
                "date": "Last modified: Jan 14, 2025",
                "type": "neuro",
                "icon": getattr(QStyle, "SP_DialogApplyButton"),
            },
            {
                "title": "EMG Recording 23",
                "date": "Last modified: Jan 13, 2025",
                "type": "emg",
                "icon": getattr(QStyle, "SP_FileDialogInfoView"),
            },
            {
                "title": "EEG Study Results",
                "date": "Last modified: Jan 10, 2025",
                "type": "eeg",
                "icon": getattr(QStyle, "SP_DialogHelpButton"),
            },
        ]

        self.recent_datasets = [
            {"filename": "HDEMG_Analysis2025.csv", "metadata": "2.5MB • 1,000 rows"},
            {"filename": "NeuroSignal_Analysis.xlsx", "metadata": "1.8MB • 750 rows"},
            {"filename": "EMG_Recording23.dat", "metadata": "3.2MB • 1,500 rows"},
            {"filename": "EEG_Study_Jan2025.csv", "metadata": "5.1MB • 2,200 rows"},
        ]

        # Initialize external widgets if available
        self.initialize_external_widgets()

        # Set up the UI (imported from main_window_ui.py)
        setup_ui(self)

        # Connect signals to slots
        self.connect_signals()

        # Start on dashboard view
        self.show_dashboard_view()

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
            # Connect the new signal for decomposition
            if hasattr(self.import_data_page, "decomposition_requested"):
                self.import_data_page.decomposition_requested.connect(self.create_decomposition_view)

    def create_decomposition_view(self, emg_obj, filename, pathname, imported_signal):
        """Creates a decomposition view with the provided data and adds it to the stacked widget."""
        try:
            print("Creating decomposition view with provided data")

            # Create a wrapper widget to hold the DecompositionApp
            wrapper = QWidget()
            wrapper.setObjectName("decomposition_wrapper")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)

            # Create DecompositionApp instance
            decomp_app = DecompositionApp(
                emg_obj=emg_obj,
                filename=filename,
                pathname=pathname,
                imported_signal=imported_signal,
                parent=self,  # Set parent for proper widget hierarchy
            )

            # Set window flags to make it a widget instead of a window
            decomp_app.setWindowFlags(Qt.WindowType.Widget)

            # Add to layout
            wrapper_layout.addWidget(decomp_app)

            # Connect back button to show import view
            if hasattr(decomp_app, "back_to_import_btn"):
                decomp_app.back_to_import_btn.clicked.connect(self.show_import_data_view)

            # Replace the placeholder with our real decomposition view
            self.decomposition_page = wrapper

            # Remove the old placeholder if it exists
            for i in range(self.central_stacked_widget.count()):
                widget = self.central_stacked_widget.widget(i)
                if widget and (
                    widget.objectName() == "decomposition_placeholder"
                    or (hasattr(widget, "objectName") and widget.objectName() == "decomposition_placeholder")
                ):
                    self.central_stacked_widget.removeWidget(widget)
                    break

            # Add the wrapper to the stacked widget
            self.central_stacked_widget.addWidget(wrapper)

            # Show the decomposition view
            self.show_decomposition_view()

        except Exception as e:
            print(f"Error creating decomposition view: {e}")
            traceback.print_exc()

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

    # Navigation methods
    def show_dashboard_view(self):
        """Switches the central widget to the dashboard page."""
        print("Switching to Dashboard View")

        self.central_stacked_widget.setCurrentWidget(self.dashboard_page)
        update_sidebar_selection(self, "dashboard")

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

    def open_visualization(self, title):
        """Handles clicks on visualization cards."""
        print(f"Clicked visualization/analysis card: {title}")
        # Map visualization titles to corresponding views
        if "HDEMG Analysis" in title and hasattr(self, "mu_analysis_page") and self.mu_analysis_page:
            self.show_mu_analysis_view()
        else:
            print(f"No specific action defined for card '{title}'. Staying on Dashboard.")

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
