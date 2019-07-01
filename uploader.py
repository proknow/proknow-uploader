from tkinter import *
from tkinter import filedialog
import json
import os
import webbrowser
from proknow import ProKnow
from pathlib import Path


def read_app_configuration(configuration_path):
    if not os.path.exists(configuration_path):
        raise FileNotFoundError(rf"The configuration file {configuration_path} does not exist.")
    with open(configuration_path) as configuration_file:
        return json.load(configuration_file)


def maybe_initialize_credentials_path():
    global user_configuration_path
    global credentials_path
    if os.path.exists(user_configuration_path):
        with open(user_configuration_path) as user_configuration_file:
            user_configuration = json.load(user_configuration_file)
            credentials_path.set(user_configuration["credentials_file"])


def save_credentials_path():
    global user_configuration_path
    global credentials_path
    os.makedirs(os.path.dirname(user_configuration_path), exist_ok=True)
    with open(user_configuration_path, mode="w+") as user_configuration_file:
        user_configuration = dict()
        user_configuration["credentials_file"] = credentials_path.get()
        json.dump(user_configuration, user_configuration_file)


def root_path():
    return os.path.abspath(os.sep)


def show_credentials_help(*_):
    webbrowser.open_new_tab("https://support.proknow.com/hc/en-us/articles/360019798893-Configuring-Your-Profile#managing-api-keys")


def browse_credentials():
    global credentials_path
    filename = filedialog.askopenfilename(initialdir=root_path(), title="Select credentials file", filetypes=(("json files", "*.json"), ("all files", "*.*")))
    if filename:
        credentials_path.set(filename)
        save_credentials_path()
        maybe_enable_upload_button()


def browse_directory_to_upload():
    global directory_to_upload_path
    directory = filedialog.askdirectory(initialdir=root_path(), title="Select directory to upload")
    if directory:
        directory_to_upload_path.set(directory)
        maybe_enable_upload_button()
        reset_upload_status()
        disable_view_patient()


def maybe_enable_upload_button():
    global credentials_path
    global directory_to_upload_path
    if credentials_path.get() and directory_to_upload_path.get():
        upload_button['state'] = 'normal'


def reset_upload_status():
    upload_status.set("")
    upload_status_value.update_idletasks()


def upload():
    global credentials_path
    global workspace_id
    global directory_to_upload_path
    global upload_status
    pk = ProKnow(base_url, credentials_file=credentials_path.get())
    upload_status.set("in progress...")
    upload_status_value.update_idletasks()
    pk.uploads.upload(workspace_id, directory_to_upload_path.get())
    upload_status.set("completed")
    upload_status_value.update_idletasks()
    enable_view_patient()


def enable_view_patient():
    view_patient['state'] = 'normal'


def disable_view_patient():
    view_patient['state'] = DISABLED


def show_uploaded_patient(*_):
    webbrowser.open_new_tab(configuration["base_url"])  #TODO--Open patient just uploaded


configuration = read_app_configuration("./config/config.json")
project_name = configuration["project_name"]
base_url = configuration["base_url"]
workspace_id = configuration["workspace_id"]
scorecard_template_id = configuration["scorecard_template_id"]
user_configuration_path = os.path.join(str(Path.home()), ".proknow", "uploader", "user_configuration.json")

root = Tk()
root.title(f"{project_name} Uploader")
root.geometry('{}x{}'.format(500, 300))

app_config_frame = Frame(root, width=490, height=90, padx=5, pady=5)
credentials_frame = Frame(root, width=490, height=40, padx=5, pady=5)
directory_to_upload_frame = Frame(root, width=490, height=40, padx=5, pady=5)
upload_frame = Frame(root, width=490, height=40, padx=5, pady=5)
is_imageset_required = configuration["is_imageset_required"]
is_structure_set_required = configuration["is_structure_set_required"]
is_plan_required = configuration["is_plan_required"]
is_dose_required = configuration["is_dose_required"]

root.grid_rowconfigure(3, weight=1)
root.grid_columnconfigure(0, weight=1)

app_config_frame.grid(row=0, sticky="ew")
credentials_frame.grid(row=1, sticky="ew")
directory_to_upload_frame.grid(row=2, sticky="ew")
upload_frame.grid(row=4, sticky="ew")

base_url_label = Label(app_config_frame, text="Base URL: ")
base_url_value = Label(app_config_frame, text=base_url)
workspace_id_label = Label(app_config_frame, text="Workspace ID: ")
workspace_id_value = Label(app_config_frame, text=workspace_id)
scorecard_template_id_label = Label(app_config_frame, text="Scorecard Template ID: ")
scorecard_template_id_value = Label(app_config_frame, text=scorecard_template_id)
imageset_required_label = Label(app_config_frame, text="Imageset Required: ")
imageset_required_value = Label(app_config_frame, text="Yes" if is_imageset_required else "No")
structure_set_required_label = Label(app_config_frame, text="Structure Set Required: ")
structure_set_required_value = Label(app_config_frame, text="Yes" if is_structure_set_required else "No")
plan_required_label = Label(app_config_frame, text="Plan Required: ")
plan_required_value = Label(app_config_frame, text="Yes" if is_plan_required else "No")
dose_required_label = Label(app_config_frame, text="Dose Required: ")
dose_required_value = Label(app_config_frame, text="Yes" if is_dose_required else "No")

app_config_frame.grid_columnconfigure(1, weight=1)
base_url_label.grid(row=0, column=0, sticky=W)
base_url_value.grid(row=0, column=1, sticky=E)
workspace_id_label.grid(row=1, column=0, sticky=W)
workspace_id_value.grid(row=1, column=1, sticky=E)
scorecard_template_id_label.grid(row=2, column=0, sticky=W)
scorecard_template_id_value.grid(row=2, column=1, sticky=E)
imageset_required_label.grid(row=3, column=0, sticky=W)
imageset_required_value.grid(row=3, column=1, sticky=E)
structure_set_required_label.grid(row=4, column=0, sticky=W)
structure_set_required_value.grid(row=4, column=1, sticky=E)
plan_required_label.grid(row=5, column=0, sticky=W)
plan_required_value.grid(row=5, column=1, sticky=E)
dose_required_label.grid(row=6, column=0, sticky=W)
dose_required_value.grid(row=6, column=1, sticky=E)

credentials_path = StringVar()
maybe_initialize_credentials_path()

credentials_path_label = Label(credentials_frame, text="Credentials: ")
credentials_help = Label(credentials_frame, text="Help", fg="blue", cursor="hand2")
credentials_help.bind("<Button-1>", show_credentials_help)
credentials_path_value = Label(credentials_frame, textvariable=credentials_path)
credentials_path_browse_button = Button(credentials_frame, text="Browse", command=browse_credentials)

credentials_frame.grid_columnconfigure(2, weight=1)
credentials_path_label.grid(row=0, column=0, sticky=W)
credentials_help.grid(row=0, column=1, sticky=W)
credentials_path_value.grid(row=0, column=2, sticky=E)
credentials_path_browse_button.grid(row=0, column=3, sticky=E)

directory_to_upload_path = StringVar()

directory_to_upload_path_label = Label(directory_to_upload_frame, text="Directory to upload: ")
directory_to_upload_path_value = Label(directory_to_upload_frame, textvariable=directory_to_upload_path)
directory_to_upload_path_browse_button = Button(directory_to_upload_frame, text="Browse", command=browse_directory_to_upload)

directory_to_upload_frame.grid_columnconfigure(1, weight=1)
directory_to_upload_path_label.grid(row=0, column=0, sticky=W)
directory_to_upload_path_value.grid(row=0, column=1, sticky=E)
directory_to_upload_path_browse_button.grid(row=0, column=2, sticky=E)

upload_status = StringVar()

upload_button = Button(upload_frame, text="Upload", command=upload, state=DISABLED)
upload_status_value = Label(upload_frame, textvariable=upload_status)
view_patient = Label(upload_frame, text="View Patient", fg="blue", cursor="hand2", state=DISABLED)
view_patient.bind("<Button-1>", show_uploaded_patient)

upload_frame.grid_columnconfigure(2, weight=1)
upload_button.grid(row=0, column=0, sticky=W)
upload_status_value.grid(row=0, column=1, sticky=W)
view_patient.grid(row=0, column=2, sticky=E)

root.mainloop()
