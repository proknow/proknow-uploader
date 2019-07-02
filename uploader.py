import json
import os
import shutil
import tempfile
import webbrowser
from pathlib import Path
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

import pydicom
from proknow import ProKnow
from pydicom.errors import *

from Requestor import Requestor


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


def maybe_update_credential_dependencies():
    global credentials_path
    global pk
    global requestor
    global user_name
    if credentials_path.get():
        pk = ProKnow(base_url, credentials_file=credentials_path.get())
        requestor = get_requestor()
        user_name = get_user_name()


def get_requestor():
    global credentials_path
    with open(credentials_path.get()) as credentials_file:
        credentials = json.load(credentials_file)
        credentials_id = credentials["id"]
        credentials_secret = credentials["secret"]
        return Requestor(base_url, credentials_id, credentials_secret)


def get_user_name():
    global requestor
    _, user = requestor.get('/user')
    return user["name"]


def maybe_update_entity_statuses():
    global pk
    global workspace_id
    global user_name
    global does_patient_exist
    global was_imageset_submitted
    global was_structure_set_submitted
    global was_plan_submitted
    global was_dose_submitted
    global does_patient_exist_value
    global was_imageset_submitted_value
    global was_structure_set_submitted_value
    global was_plan_submitted_value
    global was_dose_submitted_value
    does_patient_exist.set("")
    was_imageset_submitted.set("")
    was_structure_set_submitted.set("")
    was_plan_submitted.set("")
    was_dose_submitted.set("")
    if user_name is not None:
        patient = pk.patients.find(workspace_id, name=user_name)
        does_patient_exist.set("Yes" if patient is not None else "No")
        if does_patient_exist.get() == "Yes":
            patient_item = patient.get()
            if is_imageset_required:
                was_imageset_submitted.set("Yes" if len(patient_item.find_entities(lambda entity: entity.data["type"] == "image_set")) > 0 else "No")
            if is_structure_set_required:
                was_structure_set_submitted.set("Yes" if len(patient_item.find_entities(lambda entity: entity.data["type"] == "structure_set")) > 0 else "No")
            if is_plan_required:
                was_plan_submitted.set("Yes" if len(patient_item.find_entities(lambda entity: entity.data["type"] == "plan")) > 0 else "No")
            if is_dose_required:
                was_dose_submitted.set("Yes" if len(patient_item.find_entities(lambda entity: entity.data["type"] == "dose")) > 0 else "No")
    does_patient_exist_value.update_idletasks()
    was_imageset_submitted_value.update_idletasks()
    was_structure_set_submitted_value.update_idletasks()
    was_plan_submitted_value.update_idletasks()
    was_dose_submitted_value.update_idletasks()


def show_credentials_help(*_):
    webbrowser.open_new_tab("https://support.proknow.com/hc/en-us/articles/360019798893-Configuring-Your-Profile#managing-api-keys")


def browse_credentials():
    global root_path
    global credentials_path
    filename = filedialog.askopenfilename(initialdir=root_path, title="Select credentials file", filetypes=(("json files", "*.json"), ("all files", "*.*")))
    if filename:
        credentials_path.set(filename)
        save_credentials_path()
        maybe_update_credential_dependencies()
        maybe_update_entity_statuses()
        maybe_enable_upload_button()


def save_credentials_path():
    global user_configuration_path
    global credentials_path
    os.makedirs(os.path.dirname(user_configuration_path), exist_ok=True)
    with open(user_configuration_path, mode="w+") as user_configuration_file:
        user_configuration = dict()
        user_configuration["credentials_file"] = credentials_path.get()
        json.dump(user_configuration, user_configuration_file)


def browse_directory_to_upload():
    global root_path
    global directory_to_upload_path
    directory = filedialog.askdirectory(initialdir=root_path, title="Select directory to upload")
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
    global workspace_id
    global directory_to_upload_path
    global pk
    global upload_status
    global patient_url
    upload_status.set("in progress...")
    upload_status_value.update_idletasks()
    tempfolder = tempfile.mkdtemp(prefix="proknow-uploader")
    anonymize(directory_to_upload_path.get(), tempfolder)
    if not do_conflicting_entities_exist(tempfolder):
        batch = pk.uploads.upload(workspace_id, tempfolder)
        shutil.rmtree(tempfolder)
        patients = [patient.get() for patient in batch.patients]
        if len(patients) > 0:
            maybe_update_entity_statuses()
            maybe_attach_scorecard(patients[0])
            workspace = pk.workspaces.resolve_by_id(workspace_id)
            patient_url.set(f"{base_url}/{workspace.slug}/patients/{patients[0].id}/browse")
            enable_view_patient()
        upload_status.set("completed")
    else:
        shutil.rmtree(tempfolder)
        upload_status.set("aborted")
    upload_status_value.update_idletasks()


def anonymize(input_folder, output_folder):
    global user_name
    # r=root, d=directories, f = files
    for r, d, f in os.walk(input_folder):
        for file in f:
            input_file_path = os.path.normpath(os.path.join(r, file))
            try:
                dataset = pydicom.dcmread(input_file_path)
                dataset.InstitutionName = None
                dataset.InstitutionAddress = None
                dataset.ReferringPhysicianName = None
                dataset.PhysiciansOfRecord = None
                dataset.PatientName = user_name
                dataset.PatientID = user_name
                if "PatientBirthDate" not in dataset or len(dataset.PatientBirthDate) != 8:
                    dataset.PatientBirthDate = None
                else:
                    dataset.PatientBirthDate = f"{dataset.PatientBirthDate[:4]}0101"
                dataset.EthnicGroup = None
                dataset.StudyID = None
                output_filename = f"{dataset.Modality}.{dataset.SOPInstanceUID}.dcm"
                output_file_path = os.path.normpath(os.path.join(output_folder, output_filename))
                dataset.save_as(output_file_path, False)
            except InvalidDicomError:
                pass  # ignore non-DICOM files


def do_conflicting_entities_exist(folder):
    global workspace_id
    global user_name
    entity_types_to_be_overwritten = get_entity_types_to_be_overwritten(folder)
    if len(entity_types_to_be_overwritten) > 0:
        pretty_entity_types_to_be_overwritten = [x.replace("_", " ") for x in entity_types_to_be_overwritten]
        prompt = f'Replace existing {", ".join(pretty_entity_types_to_be_overwritten)} entities?'
        result = messagebox.askquestion("Entities Already Uploaded", message=prompt, icon='warning')
        if result == 'yes':
            patient_item = pk.patients.find(workspace_id, name=user_name).get()
            for entity_type in entity_types_to_be_overwritten:
                for entity in patient_item.find_entities(lambda e: e.data["type"] == entity_type):
                    requestor.delete(f"/workspaces/{workspace_id}/entities/{entity.id}")
                    return False
        else:
            return True
    else:
        return False


def get_entity_types_to_be_overwritten(folder):
    global was_imageset_submitted
    global was_structure_set_submitted
    global was_plan_submitted
    global was_dose_submitted
    file_entity_types = get_file_entity_types(folder)
    entity_types_to_be_overwritten = []
    if was_imageset_submitted.get() == "Yes" and "image_set" in file_entity_types:
        entity_types_to_be_overwritten.append("image_set")
    if was_structure_set_submitted.get() == "Yes" and "structure_set" in file_entity_types:
        entity_types_to_be_overwritten.append("structure_set")
    if was_plan_submitted.get() == "Yes" and "plan" in file_entity_types:
        entity_types_to_be_overwritten.append("plan")
    if was_dose_submitted.get() == "Yes" and "dose" in file_entity_types:
        entity_types_to_be_overwritten.append("dose")
    return entity_types_to_be_overwritten


def get_file_entity_types(folder):
    # r=root, d=directories, f = files
    entity_types = []
    modality_entity_type_map = {
        "CT": "image_set",
        "MR": "image_set",
        "RTSTRUCT": "structure_set",
        "RTPLAN": "plan",
        "RTDOSE": "dose"
    }
    for r, d, f in os.walk(folder):
        for file in f:
            file_path = os.path.normpath(os.path.join(r, file))
            dataset = pydicom.dcmread(file_path, specific_tags=["Modality"])
            modality = dataset.Modality
            entity_type = modality_entity_type_map[modality]
            if entity_type not in entity_types:
                entity_types.append(entity_type)
    return entity_types


def maybe_attach_scorecard(patient_item):
    global scorecard_template_id
    dose_id = get_dose_id(patient_item)
    if dose_id:
        _, scorecard_template = requestor.get(f"/metrics/templates/{scorecard_template_id}")
        del scorecard_template["id"]
        _, scorecards = requestor.get(f"/workspaces/{workspace_id}/entities/{dose_id}/metrics/sets")
        for scorecard in scorecards:
            if scorecard["name"] == scorecard_template["name"]:
                requestor.delete(f"/workspaces/{workspace_id}/entities/{dose_id}/metrics/sets/{scorecard['id']}")
        requestor.post(f"/workspaces/{workspace_id}/entities/{dose_id}/metrics/sets", body=scorecard_template)


def get_dose_id(patient_item):
    dose_entities = patient_item.find_entities(lambda entity: entity.data["type"] == "dose")
    if len(dose_entities) > 0:
        return dose_entities[0].id
    else:
        return None


def enable_view_patient():
    view_patient['state'] = 'normal'


def disable_view_patient():
    view_patient['state'] = DISABLED


def show_uploaded_patient(*_):
    webbrowser.open_new_tab(patient_url.get())


root_path = os.path.abspath(os.sep)
configuration = read_app_configuration("./config/config.json")
project_name = configuration["project_name"]
base_url = configuration["base_url"]
workspace_id = configuration["workspace_id"]
scorecard_template_id = configuration["scorecard_template_id"]
is_imageset_required = configuration["is_imageset_required"]
is_structure_set_required = configuration["is_structure_set_required"]
is_plan_required = configuration["is_plan_required"]
is_dose_required = configuration["is_dose_required"]
user_configuration_path = os.path.join(str(Path.home()), ".proknow", "uploader", "user_configuration.json")  #TODO--INCLUDE UPLOADER NAME IN PATH
pk = None
requestor = None
user_name = None

root = Tk()
root.title(f"{project_name} Uploader")
root.geometry('{}x{}'.format(500, 400))

app_config_frame = Frame(root, width=490, height=90, padx=5, pady=5)
credentials_frame = Frame(root, width=490, height=40, padx=5, pady=5)
entity_status_frame = Frame(root, width=490, height=90, padx=5, pady=5)
directory_to_upload_frame = Frame(root, width=490, height=40, padx=5, pady=5)
upload_frame = Frame(root, width=490, height=40, padx=5, pady=5)

root.grid_rowconfigure(4, weight=1)
root.grid_columnconfigure(0, weight=1)

app_config_frame.grid(row=0, sticky="ew")
credentials_frame.grid(row=1, sticky="ew")
entity_status_frame.grid(row=2, sticky="ew")
directory_to_upload_frame.grid(row=3, sticky="ew")
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
maybe_update_credential_dependencies()

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

does_patient_exist = StringVar()
was_imageset_submitted = StringVar()
was_structure_set_submitted = StringVar()
was_plan_submitted = StringVar()
was_dose_submitted = StringVar()

does_patient_exist_label = Label(entity_status_frame, text="Patient exists? ")
does_patient_exist_value = Label(entity_status_frame, textvariable=does_patient_exist, state=DISABLED)
was_imageset_submitted_label = Label(entity_status_frame, text="Imageset submitted? ")
was_imageset_submitted_value = Label(entity_status_frame, textvariable=was_imageset_submitted, state=DISABLED)
was_structure_set_submitted_label = Label(entity_status_frame, text="Structure set submitted? ")
was_structure_set_submitted_value = Label(entity_status_frame, textvariable=was_structure_set_submitted, state=DISABLED)
was_plan_submitted_label = Label(entity_status_frame, text="Plan submitted? ")
was_plan_submitted_value = Label(entity_status_frame, textvariable=was_plan_submitted, state=DISABLED)
was_dose_submitted_label = Label(entity_status_frame, text="Dose submitted? ")
was_dose_submitted_value = Label(entity_status_frame, textvariable=was_dose_submitted, state=DISABLED)
maybe_update_entity_statuses()

entity_status_frame.grid_columnconfigure(1, weight=1)
does_patient_exist_label.grid(row=0, column=0, sticky=W)
does_patient_exist_value.grid(row=0, column=1, sticky=E)
if is_imageset_required:
    was_imageset_submitted_label.grid(row=1, column=0, sticky=W)
    was_imageset_submitted_value.grid(row=1, column=1, sticky=E)
else:
    was_imageset_submitted_label.grid_remove()
    was_imageset_submitted_value.grid_remove()
if is_structure_set_required:
    was_structure_set_submitted_label.grid(row=2, column=0, sticky=W)
    was_structure_set_submitted_value.grid(row=2, column=1, sticky=E)
else:
    was_structure_set_submitted_label.grid_remove()
    was_structure_set_submitted_value.grid_remove()
if is_plan_required:
    was_plan_submitted_label.grid(row=3, column=0, sticky=W)
    was_plan_submitted_value.grid(row=3, column=1, sticky=E)
else:
    was_plan_submitted_label.grid_remove()
    was_plan_submitted_value.grid_remove()
if is_dose_required:
    was_dose_submitted_label.grid(row=4, column=0, sticky=W)
    was_dose_submitted_value.grid(row=4, column=1, sticky=E)
else:
    was_dose_submitted_label.grid_remove()
    was_dose_submitted_value.grid_remove()

directory_to_upload_path = StringVar()

directory_to_upload_path_label = Label(directory_to_upload_frame, text="Directory to upload: ")
directory_to_upload_path_value = Label(directory_to_upload_frame, textvariable=directory_to_upload_path)
directory_to_upload_path_browse_button = Button(directory_to_upload_frame, text="Browse", command=browse_directory_to_upload)

directory_to_upload_frame.grid_columnconfigure(1, weight=1)
directory_to_upload_path_label.grid(row=0, column=0, sticky=W)
directory_to_upload_path_value.grid(row=0, column=1, sticky=E)
directory_to_upload_path_browse_button.grid(row=0, column=2, sticky=E)

upload_status = StringVar()
patient_url = StringVar()

upload_button = Button(upload_frame, text="Upload", command=upload, state=DISABLED)
upload_status_value = Label(upload_frame, textvariable=upload_status)
view_patient = Label(upload_frame, text="View Patient", fg="blue", cursor="hand2", state=DISABLED)
view_patient.bind("<Button-1>", show_uploaded_patient)

upload_frame.grid_columnconfigure(2, weight=1)
upload_button.grid(row=0, column=0, sticky=W)
upload_status_value.grid(row=0, column=1, sticky=W)
view_patient.grid(row=0, column=2, sticky=E)

root.mainloop()
