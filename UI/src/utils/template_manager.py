import json
import os
from PySide6.QtWidgets import QComboBox

class TemplateManager:
    def __init__(self):
        self.template_dir = "."
        
    def get_template_names(self):
        return [f for f in os.listdir(self.template_dir) if f.endswith('.json')]
        
    def load_template(self, template_name):
        if template_name and template_name != "Select Template":
            try:
                with open(template_name, "r") as file:
                    template = json.load(file)
                    return template
            except Exception as e:
                print(f"Error loading template: {str(e)}")
        return None
        
    def save_template(self, name, template_data):
        try:
            with open(f"{name}.json", "w") as file:
                json.dump(template_data, file)
            return True
        except Exception as e:
            print(f"Error saving template: {str(e)}")
            return False
            
    def delete_template(self, template_name):
        try:
            os.remove(template_name)
            return True
        except Exception as e:
            print(f"Error deleting template: {str(e)}")
            return False
            
    def update_template_combo(self, combo_box):
        combo_box.clear()
        combo_box.addItem("Select Template")
        
        for template_name in self.get_template_names():
            combo_box.addItem(template_name) 