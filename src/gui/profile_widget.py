"""
Profile Management Widget for Local AI Model Manager
"""

from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFormLayout,
    QSpinBox,
    QSlider,
)
from PySide6.QtCore import Qt, Signal

# Add src to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import DatabaseManager
from src.profile_manager import ProfileManager


class ProfileWidget(QWidget):
    """Widget for managing model profiles"""

    profile_changed = Signal(str)  # profile_name

    def __init__(self, profile_manager: ProfileManager, database: DatabaseManager):
        super().__init__()
        self.profile_manager = profile_manager
        self.database = database

        self.profiles = []
        self.current_profile = None

        self.setup_ui()
        self.refresh_profiles()

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)

        # Profile Management title with help
        profile_title = QLabel("Profile Management")
        profile_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ffcc00;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4080c0, stop:1 #60a0e0);
                padding: 10px;
                border-radius: 8px;
                border: 2px solid #ffcc00;
            }
        """)
        layout.addWidget(profile_title)

        # Comprehensive help text
        help_label = QLabel(
            "Profiles let you organize models with specific settings.\n"
            "• Select models to include in each profile\n"
            "• Set max context, auto-unload timer, and RAM threshold\n"
            "• Load/Save profiles to switch between different model configurations\n"
            "• Profiles are optional - you can manage models without them"
        )
        help_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: #306090;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #5090d0;
                font-size: 11px;
            }
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        # Profile selection
        selection_group = QGroupBox("Active Profile")
        selection_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #ff00ff;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: #5090d0;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 3px 0 3px;
                color: #ffffff;
            }
        """)
        selection_layout = QVBoxLayout(selection_group)

        self.profile_combo = QComboBox()
        self.profile_combo.setToolTip(
            "Select a profile to activate. Profiles contain your model configurations and settings."
        )
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        selection_layout.addWidget(self.profile_combo)

        # Profile actions
        profile_actions = QHBoxLayout()

        self.load_profile_btn = QPushButton("Load Profile")
        self.load_profile_btn.setToolTip(
            "Load the selected profile and apply its settings to the current session"
        )
        self.load_profile_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ccff, stop:1 #0099cc);
                color: white;
                border: 2px solid #006699;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ddff, stop:1 #00aadd);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0088bb, stop:1 #006699);
            }
        """)
        self.load_profile_btn.clicked.connect(self.load_current_profile)
        profile_actions.addWidget(self.load_profile_btn)

        self.save_profile_btn = QPushButton("Save Changes")
        self.save_profile_btn.setToolTip(
            "Save the current configuration changes to the selected profile"
        )
        self.save_profile_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff66, stop:1 #00cc44);
                color: white;
                border: 2px solid #009933;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff88, stop:1 #00dd55);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00aa44, stop:1 #008833);
            }
        """)
        self.save_profile_btn.clicked.connect(self.save_profile_changes)
        profile_actions.addWidget(self.save_profile_btn)

        selection_layout.addLayout(profile_actions)
        layout.addWidget(selection_group)

        # Profile details
        details_group = QGroupBox("Profile Details")
        details_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #ff00ff;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: #5090d0;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 3px 0 3px;
                color: #ffffff;
            }
        """)
        self.details_layout = QVBoxLayout(details_group)

        # Profile name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        name_layout.addWidget(name_label)
        self.profile_name_label = QLabel("No profile selected")
        self.profile_name_label.setStyleSheet("color: #ffccff;")
        self.profile_name_label.setToolTip("The name of the currently selected profile")
        name_layout.addWidget(self.profile_name_label)
        name_layout.addStretch()
        self.details_layout.addLayout(name_layout)

        # Models in profile
        self.models_label = QLabel("Models: None")
        self.models_label.setStyleSheet("color: #ffccff;")
        self.models_label.setToolTip("List of AI models included in this profile")
        self.details_layout.addWidget(self.models_label)

        # Profile settings
        settings_form = QFormLayout()

        self.max_context_spin = QSpinBox()
        self.max_context_spin.setRange(512, 32768)
        self.max_context_spin.setSingleStep(512)
        self.max_context_spin.setToolTip(
            "Maximum context window size for models (higher values allow longer conversations but use more memory)"
        )
        settings_form.addRow("Max Context:", self.max_context_spin)

        self.auto_unload_spin = QSpinBox()
        self.auto_unload_spin.setRange(1, 120)
        self.auto_unload_spin.setSuffix(" min")
        self.auto_unload_spin.setToolTip(
            "Auto-unload models after they've been idle for this many minutes"
        )
        settings_form.addRow("Auto Unload:", self.auto_unload_spin)

        self.ram_threshold_spin = QSpinBox()
        self.ram_threshold_spin.setRange(50, 95)
        self.ram_threshold_spin.setSuffix("%")
        self.ram_threshold_spin.setToolTip(
            "RAM usage threshold - models will be auto-unloaded when memory usage exceeds this percentage"
        )
        settings_form.addRow("RAM Threshold:", self.ram_threshold_spin)

        self.details_layout.addLayout(settings_form)
        layout.addWidget(details_group)

        # Available models
        available_group = QGroupBox("Available Models")
        available_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #ff00ff;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: #5090d0;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 3px 0 3px;
                color: #ffffff;
            }
        """)
        available_layout = QVBoxLayout(available_group)

        self.available_list = QListWidget()
        self.available_list.setMaximumHeight(150)
        self.available_list.setToolTip("Select models to add to the current profile")
        available_layout.addWidget(self.available_list)

        # Add/Remove buttons
        add_remove_layout = QHBoxLayout()

        self.add_model_btn = QPushButton("Add Model")
        self.add_model_btn.setToolTip("Add selected model to the current profile")
        self.add_model_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff66, stop:1 #00cc44);
                color: white;
                border: 2px solid #009933;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff88, stop:1 #00dd55);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00aa44, stop:1 #008833);
            }
        """)
        self.add_model_btn.clicked.connect(self.add_model_to_profile)
        add_remove_layout.addWidget(self.add_model_btn)

        self.remove_model_btn = QPushButton("Remove Model")
        self.remove_model_btn.setToolTip(
            "Remove selected model from the current profile"
        )
        self.remove_model_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6666, stop:1 #cc4444);
                color: white;
                border: 2px solid #993333;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8888, stop:1 #dd5555);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #aa4444, stop:1 #883333);
            }
        """)
        self.remove_model_btn.clicked.connect(self.remove_model_from_profile)
        add_remove_layout.addWidget(self.remove_model_btn)
        available_layout.addLayout(add_remove_layout)
        layout.addWidget(available_group)

        # Profile management
        management_group = QGroupBox("Profile Management")
        management_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #ff00ff;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 5px;
                background-color: #5090d0;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                padding: 0 3px 0 3px;
                color: #ffffff;
            }
        """)
        management_layout = QHBoxLayout(management_group)

        self.new_profile_btn = QPushButton("New Profile")
        self.new_profile_btn.setToolTip("Create a new profile with default settings")
        self.new_profile_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ccff, stop:1 #0099cc);
                color: white;
                border: 2px solid #006699;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ddff, stop:1 #00aadd);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0088bb, stop:1 #006699);
            }
        """)
        self.new_profile_btn.clicked.connect(self.create_new_profile)
        management_layout.addWidget(self.new_profile_btn)

        self.delete_profile_btn = QPushButton("Delete Profile")
        self.delete_profile_btn.setToolTip(
            "Delete the currently selected profile (cannot be undone)"
        )
        self.delete_profile_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff6666, stop:1 #cc4444);
                color: white;
                border: 2px solid #993333;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8888, stop:1 #dd5555);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #aa4444, stop:1 #883333);
            }
        """)
        self.delete_profile_btn.clicked.connect(self.delete_current_profile)
        management_layout.addWidget(self.delete_profile_btn)

        layout.addWidget(management_group)

        # Initially disable buttons
        self.update_button_states()

    def refresh_profiles(self):
        """Refresh profile list"""
        try:
            self.profiles = self.database.get_profiles()

            # Update combo box
            self.profile_combo.clear()
            for profile in self.profiles:
                self.profile_combo.addItem(profile["name"])

            # Select first profile if available
            if self.profiles:
                self.profile_combo.setCurrentIndex(0)
                self.load_profile_details(self.profiles[0])

            # Update available models
            self.update_available_models()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh profiles: {str(e)}")

    def update_available_models(self):
        """Update available models list"""
        try:
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from src.ollama_client import OllamaClient
            import asyncio

            # Get available models
            client = OllamaClient()
            loop = asyncio.new_event_loop()
            models = loop.run_until_complete(client.list_models())

            self.available_list.clear()
            for model in models:
                item = QListWidgetItem(model.name)
                item.setData(Qt.UserRole, model.name)
                self.available_list.addItem(item)

        except Exception as e:
            print(f"Error updating available models: {e}")

    def on_profile_changed(self, profile_name: str):
        """Handle profile selection change"""
        if not profile_name:
            return

        # Find profile data
        profile = None
        for p in self.profiles:
            if p["name"] == profile_name:
                profile = p
                break

        if profile:
            self.load_profile_details(profile)

    def load_profile_details(self, profile: Dict[str, Any]):
        """Load profile details into UI"""
        self.current_profile = profile

        # Update labels
        self.profile_name_label.setText(profile["name"])

        # Update models
        models_text = ", ".join(profile["models"]) if profile["models"] else "None"
        self.models_label.setText(f"Models: {models_text}")

        # Update settings
        self.max_context_spin.setValue(profile["max_context"])
        self.auto_unload_spin.setValue(profile["auto_unload_minutes"])
        self.ram_threshold_spin.setValue(profile["ram_threshold"])

        # Update button states
        self.update_button_states()

    def load_current_profile(self):
        """Load the current profile"""
        if not self.current_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return

        try:
            # Load profile using profile manager
            success = self.profile_manager.switch_to_profile(
                self.current_profile["name"]
            )

            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Profile '{self.current_profile['name']}' loaded successfully",
                )
                self.profile_changed.emit(self.current_profile["name"])
            else:
                QMessageBox.warning(self, "Warning", "Failed to load profile")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load profile: {str(e)}")

    def save_profile_changes(self):
        """Save changes to current profile"""
        if not self.current_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return

        try:
            # Update profile data
            updated_profile = {
                "name": self.current_profile["name"],
                "models": self.current_profile["models"],  # Keep existing models
                "max_context": self.max_context_spin.value(),
                "auto_unload_minutes": self.auto_unload_spin.value(),
                "ram_threshold": self.ram_threshold_spin.value(),
            }

            # Update in database
            self.database.update_profile(updated_profile["name"], updated_profile)

            # Refresh profiles
            self.refresh_profiles()

            QMessageBox.information(self, "Success", "Profile saved successfully")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save profile: {str(e)}")

    def add_model_to_profile(self):
        """Add selected model to profile"""
        print(f"DEBUG: add_model_to_profile called")
        if not self.current_profile:
            print(f"DEBUG: No current profile selected")
            QMessageBox.warning(self, "Warning", "No profile selected")
            return

        current_item = self.available_list.currentItem()
        if not current_item:
            print(f"DEBUG: No model selected from available list")
            QMessageBox.warning(self, "Warning", "No model selected")
            return

        model_name = current_item.data(Qt.UserRole)
        print(
            f"DEBUG: Adding model {model_name} to profile {self.current_profile['name']}"
        )

        if model_name in self.current_profile["models"]:
            QMessageBox.information(self, "Info", "Model already in profile")
            return

        try:
            # Add model to profile
            self.current_profile["models"].append(model_name)
            print(f"DEBUG: Updated profile models: {self.current_profile['models']}")

            # Update database
            self.database.update_profile(
                self.current_profile["name"], self.current_profile
            )

            # Refresh display
            models_text = ", ".join(self.current_profile["models"])
            self.models_label.setText(f"Models: {models_text}")

            QMessageBox.information(self, "Success", f"Added {model_name} to profile")

        except Exception as e:
            print(f"ERROR: Failed to add model: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add model: {str(e)}")

    def remove_model_from_profile(self):
        """Remove selected model from profile"""
        print(f"DEBUG: remove_model_from_profile called")
        if not self.current_profile:
            print(f"DEBUG: No current profile selected")
            QMessageBox.warning(self, "Warning", "No profile selected")
            return

        if not self.current_profile["models"]:
            print(f"DEBUG: No models in profile to remove")
            QMessageBox.warning(self, "Warning", "No models in profile")
            return

        # For simplicity, remove the last model
        # In a real implementation, you'd have a separate list for profile models
        try:
            if self.current_profile["models"]:
                removed_model = self.current_profile["models"].pop()
                print(f"DEBUG: Removed model {removed_model} from profile")

                # Update database
                self.database.update_profile(
                    self.current_profile["name"], self.current_profile
                )

                # Refresh display
                models_text = (
                    ", ".join(self.current_profile["models"])
                    if self.current_profile["models"]
                    else "None"
                )
                self.models_label.setText(f"Models: {models_text}")

                QMessageBox.information(
                    self, "Success", f"Removed {removed_model} from profile"
                )

        except Exception as e:
            print(f"ERROR: Failed to remove model: {e}")
            QMessageBox.warning(self, "Error", f"Failed to remove model: {str(e)}")

    def create_new_profile(self):
        """Create a new profile"""
        # Simple implementation - in reality you'd want a dialog
        try:
            new_profile = {
                "name": f"Profile {len(self.profiles) + 1}",
                "models": [],
                "max_context": 4096,
                "auto_unload_minutes": 15,
                "ram_threshold": 80,
            }

            print(f"DEBUG: Creating new profile: {new_profile}")

            # Add to database
            self.database.update_profile(new_profile["name"], new_profile)

            # Refresh profiles
            self.refresh_profiles()

            # Select new profile
            self.profile_combo.setCurrentText(new_profile["name"])

            QMessageBox.information(
                self, "Success", f"Created profile: {new_profile['name']}"
            )

        except Exception as e:
            print(f"ERROR: Failed to create profile: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create profile: {str(e)}")

    def delete_current_profile(self):
        """Delete current profile"""
        if not self.current_profile:
            QMessageBox.warning(self, "Warning", "No profile selected")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete profile '{self.current_profile['name']}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                print(f"DEBUG: Deleting profile: {self.current_profile['name']}")

                # Delete from database
                self.database.delete_profile(self.current_profile["name"])

                # Refresh profiles
                self.refresh_profiles()

                QMessageBox.information(
                    self, "Success", f"Deleted profile: {self.current_profile['name']}"
                )

            except Exception as e:
                print(f"ERROR: Failed to delete profile: {e}")
                QMessageBox.warning(
                    self, "Error", f"Failed to delete profile: {str(e)}"
                )

    def update_button_states(self):
        """Enable or disable profile buttons"""
        has_profile = self.current_profile is not None
        has_models = bool(self.current_profile and self.current_profile.get("models"))

        self.load_profile_btn.setEnabled(has_profile)
        self.save_profile_btn.setEnabled(has_profile)
        self.add_model_btn.setEnabled(has_profile)
        self.remove_model_btn.setEnabled(has_models)
        self.new_profile_btn.setEnabled(True)
        self.delete_profile_btn.setEnabled(has_profile)

    def get_current_profile(self) -> Optional[Dict[str, Any]]:
        """Get current profile data"""
        return self.current_profile
