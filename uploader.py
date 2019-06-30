from tkinter import *
import json
import os


def read_configuration(configuration_path):
    if not os.path.exists(configuration_path):
        raise FileNotFoundError(rf"The configuration file {configuration_path} does not exist.")
    with open(configuration_path) as configuration_file:
        return json.load(configuration_file)


configuration = read_configuration("./config/config.json")
print("Configuration:")
print(json.dumps(configuration, indent=4))
project_name = configuration["project_name"]

root = Tk()
root.title(f"{project_name} Uploader")
root.geometry('{}x{}'.format(400, 300))

app_config_frame = Frame(root, width=390, height=100, pady=3)

root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

app_config_frame.grid(row=0, sticky="ew")

base_url_label = Label(app_config_frame, text="Base URL: ", relief=RIDGE, width=20, anchor=W)
base_url_value = Label(app_config_frame, text=configuration["base_url"], relief=SUNKEN, width=32, anchor=E)
workspace_id_label = Label(app_config_frame, text="Workspace ID: ", relief=RIDGE, width=20, anchor=W)
workspace_id_value = Label(app_config_frame, text=configuration["workspace_id"], relief=SUNKEN, width=32, anchor=E)
scorecard_template_id_label = Label(app_config_frame, text="Scorecard Template ID: ", relief=RIDGE, width=20, anchor=W)
scorecard_template_id_value = Label(app_config_frame, text=configuration["scorecard_template_id"], relief=SUNKEN, width=32, anchor=E)
imageset_required_label = Label(app_config_frame, text="Imageset Required: ", relief=RIDGE, width=20, anchor=W)
imageset_required_value = Label(app_config_frame, text="Yes" if configuration["is_imageset_required"] else "No", relief=SUNKEN, width=32, anchor=E)
structure_set_required_label = Label(app_config_frame, text="Structure Set Required: ", relief=RIDGE, width=20, anchor=W)
structure_set_required_value = Label(app_config_frame, text="Yes" if configuration["is_structure_set_required"] else "No", relief=SUNKEN, width=32, anchor=E)
plan_required_label = Label(app_config_frame, text="Plan Required: ", relief=RIDGE, width=20, anchor=W)
plan_required_value = Label(app_config_frame, text="Yes" if configuration["is_plan_required"] else "No", relief=SUNKEN, width=32, anchor=E)
dose_required_label = Label(app_config_frame, text="Dose Required: ", relief=RIDGE, width=20, anchor=W)
dose_required_value = Label(app_config_frame, text="Yes" if configuration["is_dose_required"] else "No", relief=SUNKEN, width=32, anchor=E)

base_url_label.grid(row=0, column=0)
base_url_value.grid(row=0, column=1)
workspace_id_label.grid(row=1, column=0)
workspace_id_value.grid(row=1, column=1)
scorecard_template_id_label.grid(row=2, column=0)
scorecard_template_id_value.grid(row=2, column=1)
imageset_required_label.grid(row=3, column=0)
imageset_required_value.grid(row=3, column=1)
structure_set_required_label.grid(row=4, column=0)
structure_set_required_value.grid(row=4, column=1)
plan_required_label.grid(row=5, column=0)
plan_required_value.grid(row=5, column=1)
dose_required_label.grid(row=6, column=0)
dose_required_value.grid(row=6, column=1)

root.mainloop()
