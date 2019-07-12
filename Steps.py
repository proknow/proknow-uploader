import os
import json
import webbrowser
from tkinter import *
from tkinter import ttk, filedialog, messagebox

class CredentialsPage(object):
    def __init__(self, app):
        self.app = app

        # Variables
        self.credentials_path_variable = StringVar()
        self.session_label_variable = StringVar()
        self.workspace_label_variable = StringVar()
        self.scorecard_label_variable = StringVar()

        # Initialize Widgets
        self.step1_label_frame = ttk.Labelframe(self.app.mainframe, text='Step 1: Load Credentials File', padding="10")
        self.step1_label_frame.columnconfigure(0, weight=1)
        self.credentials_label = ttk.Label(self.step1_label_frame, text='Credentials:')
        self.credentials_entry = ttk.Entry(self.step1_label_frame, textvariable=self.credentials_path_variable, state=['readonly'])
        self.credentials_path_browse_button = ttk.Button(self.step1_label_frame, text="Browse", command=self._browse_credential_file)
        self.session_label = ttk.Label(self.step1_label_frame, textvariable=self.session_label_variable, wraplength=600, foreground="green")
        self.workspace_label = ttk.Label(self.step1_label_frame, textvariable=self.workspace_label_variable, wraplength=600, foreground="green")
        self.scorecard_label = ttk.Label(self.step1_label_frame, textvariable=self.scorecard_label_variable, wraplength=600, foreground="green")

    def render(self):
        # Grid widgets
        self.step1_label_frame.grid(column=0, row=0, sticky=(N, W, E))
        self.credentials_label.grid(column=0, row=0, sticky=(W,))
        self.credentials_entry.grid(column=0, row=1, sticky=(W, E))
        self.credentials_path_browse_button.grid(column=1, row=1, sticky=(W, E))

        # Set credentials path
        if "credentials_path" in self.app.user_configuration:
            self.credentials_path_variable.set(self.app.user_configuration["credentials_path"])
        else:
            self.credentials_path_variable.set("")

        data = self.app.credentials_page_data

        # Configure session
        if "session" not in data:
            self.session_label_variable.set("Please select a credentials file.")
            self.session_label.configure(foreground="black")
            self.session_label.grid(column=0, row=2, columnspan=2, sticky=(W,))
            self.workspace_label.grid_remove()
            self.scorecard_label.grid_remove()
            return
        elif data["session"] is None:
            self.session_label_variable.set("\u2717 Credentials error: " + data["session_error"])
            self.session_label.configure(foreground="red")
            self.session_label.grid(column=0, row=2, columnspan=2, sticky=(W,))

            self.workspace_label.grid_remove()
            self.scorecard_label.grid_remove()
        else:
            self.session_label_variable.set("\u2713 Credentials validated")
            self.session_label.configure(foreground="green")
            self.session_label.grid(column=0, row=2, columnspan=2, sticky=(W,))

            # Configure workspace
            if data["workspace"] is None:
                self.workspace_label_variable.set("\u2717 Resolved Workspace Name: " + data["workspace_error"])
                self.workspace_label.configure(foreground="red")
            else:
                self.workspace_label_variable.set("\u2713 Resolved Workspace Name: " + data["workspace"].name)
                self.workspace_label.configure(foreground="green")
            self.workspace_label.grid(column=0, row=3, columnspan=2, sticky=(W,))

            # Configure scorecard
            if data["scorecard"] is None:
                self.scorecard_label_variable.set("\u2717 Resolved Scorecard Template Name: " + data["scorecard_error"])
                self.scorecard_label.configure(foreground="red")
            else:
                self.scorecard_label_variable.set("\u2713 Resolved Scorecard Template Name: " + data["scorecard"].name)
                self.scorecard_label.configure(foreground="green")
            self.scorecard_label.grid(column=0, row=4, columnspan=2, sticky=(W,))

        # Show error message if credentials are invalid
        if data["session"] is None or data["workspace"] is None or data["scorecard"] is None:
            messagebox.showinfo(message='Please resolve the error to continue.')

    def _browse_credential_file(self):
        self.app.root.update()
        filename = filedialog.askopenfilename(initialdir=self.app.root_path, title="Select credentials file", filetypes=(("JSON files", "*.json"), ("All files", "*.*")))
        self.app.root.update()
        if filename:
            self.app.user_configuration["credentials_path"] = filename
            self.app.save_user_configuration()
            self.app.refresh_proknow()

class UploadsPage(object):
    def __init__(self, app):
        self.app = app

        # Variables
        self.upload_files_message_variable = StringVar()

        # Initialize Widgets
        self.step2_label_frame = ttk.Labelframe(self.app.mainframe, text='Step 2: Upload Files', padding="10")
        self.step2_label_frame.columnconfigure(0, weight=1)
        self.upload_instructions = ttk.Label(self.step2_label_frame, text='Below is a list of ' +
            'the patient entities that are required as part of your submission. Use the upload ' +
            'button below to initiate new patient entity uploads. Please note that you may only ' +
            'upload one series per entity type at a time, and uploading an entity will replace ' +
            'any current entities of that type.', wraplength=600)
        self.current_entities_frame = ttk.Frame(self.step2_label_frame, padding="0 5")
        self.required_labels = {}
        for key in ["is_image_set_required", "is_structure_set_required", "is_plan_required", "is_dose_required"]:
            if self.app.app_configuration[key]:
                variable = StringVar()
                label = ttk.Label(self.current_entities_frame, textvariable=variable)
                self.required_labels[key] = {
                    "label": label,
                    "variable": variable,
                }
        self.required_uploaded_separator = ttk.Separator(self.step2_label_frame, orient=HORIZONTAL)
        self.choose_buttons_frame = ttk.Frame(self.step2_label_frame, padding="0 5")
        self.choose_directory_button = ttk.Button(self.choose_buttons_frame, text='Choose Directory...', command=self._choose_directory)
        self.choose_files_button = ttk.Button(self.choose_buttons_frame, text='Choose Files...', command=self._choose_files)
        self.upload_files_message = ttk.Label(self.step2_label_frame, textvariable=self.upload_files_message_variable, wraplength=600)
        self.upload_summary_frame = ttk.Frame(self.step2_label_frame, padding="0 5")
        self.upload_labels = {}
        for key in self.app.ENTITY_TYPES:
            variable = StringVar()
            label = ttk.Label(self.upload_summary_frame, textvariable=variable)
            self.upload_labels[key] = {
                "label": label,
                "variable": variable,
            }
        self.upload_buttons_frame = ttk.Frame(self.step2_label_frame, padding="0 5")
        self.upload_button = ttk.Button(self.upload_buttons_frame, text='Upload', command=self._upload_files)
        self.clear_button = ttk.Button(self.upload_buttons_frame, text='Clear', command=self._clear_files)
        self.progress_frame = ttk.Frame(self.step2_label_frame, padding="0 5")
        self.upload_progress_label = ttk.Label(self.progress_frame, text="Upload Progress")
        self.upload_progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=200, mode='determinate')
        self.process_progress_label = ttk.Label(self.progress_frame, text="Processing Progress")
        self.process_progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=200, mode='determinate')

    def render(self):
        data = self.app.uploads_page_data
        if "patient" not in data:
            self.step2_label_frame.grid_remove()
            return

        # Grid widgets
        # |- step2_label_frame
        #    |- upload_instructions
        #    \- current_entities_frame
        #       |- ...required_labels
        #    \- required_uploaded_separator
        #    \- choose_buttons_frame
        #       |- choose_directory_button
        #       |- choose_files_button
        #    |- upload_summary_frame
        #       |- upload_files_message
        #       |- ...upload_labels
        #    \- upload_buttons_frame
        #       |- upload_button
        #       |- clear_button
        self.step2_label_frame.grid(column=0, row=1, sticky=(N, W, E))
        self.upload_instructions.grid(column=0, row=0, sticky=(W,))
        self.current_entities_frame.grid(column=0, row=1, sticky=(W,E))
        self.required_uploaded_separator.grid(column=0, row=2, sticky=(W, E))
        if "upload_progress" in data and False:
            self.choose_buttons_frame.grid_remove()
            self.choose_directory_button.grid_remove()
            self.choose_files_button.grid_remove()
            self.upload_files_message.grid_remove()
            self.upload_summary_frame.grid_remove()
            self.upload_buttons_frame.grid_remove()
            self.upload_button.grid_remove()
            self.clear_button.grid_remove()

            self.progress_frame.grid(column=0, row=3, sticky=(W,E))
            self.upload_progress_label.grid(column=0, row=0, sticky=(W,))
            self.upload_progress.grid(column=1, row=0, sticky=(W,))
            self.process_progress_label.grid(column=0, row=1, sticky=(W,))
            self.process_progress.grid(column=1, row=1, sticky=(W,))
        else:
            self.progress_frame.grid_remove()
            self.upload_progress_label.grid_remove()
            self.upload_progress.grid_remove()
            self.process_progress_label.grid_remove()
            self.process_progress_label.grid_remove()

            self.choose_buttons_frame.grid(column=0, row=3, sticky=(W, E))
            self.choose_directory_button.grid(column=0, row=0)
            self.choose_files_button.grid(column=1, row=0)

            if "uploads" in data:
                self.upload_files_message.grid(column=0, row=4, sticky=(W,))
                self.upload_summary_frame.grid(column=0, row=5, sticky=(W,E))
                self.upload_buttons_frame.grid(column=0, row=6, sticky=(W,E))
                self.upload_button.grid(column=0, row=0)
                self.clear_button.grid(column=1, row=0)
            else:
                self.upload_files_message.grid_remove()
                self.upload_summary_frame.grid_remove()
                self.upload_buttons_frame.grid_remove()
                self.upload_button.grid_remove()
                self.clear_button.grid_remove()

        # Configure upload progress
        if "upload_progress" in data and False:
            total = data["upload_progress"]["total"]
            uploaded = data["upload_progress"]["uploaded"]
            processed = data["upload_progress"]["processed"]
            self.upload_progress.configure(maximum=total, value=uploaded)
            self.process_progress.configure(maximum=total, value=processed)
        else:

            # Configure entities
            row = 0
            items = [
                (
                    self.app.ENTITY_TYPE_REQUIRED_MAP[entity_type],
                    self.app.ENTITY_TYPE_NAME_MAP[entity_type],
                    self.app.uploads_page_data["entities"][entity_type]
                ) for entity_type in self.app.ENTITY_TYPES
            ]
            for item in items:
                key = item[0]
                name = item[1]
                collection = item[2]
                if self.app.app_configuration[key]:
                    self.required_labels[key]["label"].grid(column=0, row=row, sticky=(W,))
                    if len(collection) > 0:
                        self.required_labels[key]["variable"].set('\u2713 ' + name)
                        self.required_labels[key]["label"].configure(foreground="green")
                    else:
                        self.required_labels[key]["variable"].set('\u2717 ' + name + ' (Not Found)')
                        self.required_labels[key]["label"].configure(foreground="red")
                row += 1

            # Configure uploads
            if "uploads" in data:
                row = 0
                valid = 0
                invalid = 0
                for key in self.app.ENTITY_TYPES:
                    item = self.upload_labels[key]
                    info = data["uploads"]["series_info"][key]
                    length = len(info)
                    if length == 0:
                        item["label"].grid_remove()
                    elif length == 1:
                        item["variable"].set('\u2713 ' + self.app.ENTITY_TYPE_NAME_MAP[key] + "(1)")
                        item["label"].configure(foreground="green")
                        item["label"].grid(column=0, row=row, sticky=(W,))
                        valid += 1
                        row += 1
                    else:
                        item.variable.set('\u2717 ' + self.app.ENTITY_TYPE_NAME_MAP[key] + "(" + length + ")")
                        item["label"].configure(foreground="green")
                        item["label"].grid(column=0, row=row, sticky=(W,))
                        invalid += 1
                        row += 1

                if invalid > 0:
                    count = (str(invalid) + ' entity types') if invalid > 1 else ('1 entity type')
                    self.upload_files_message_variable.set('More than one entity was selected ' +
                        'for ' + count + ' below. Please clear the uploads and try again with a ' +
                        'single entity per entity type.')
                elif valid > 0:
                    count = (str(valid) + ' entities') if valid > 1 else ('1 entity')
                    self.upload_files_message_variable.set("You are ready to upload " + count +
                        ", which will (1) anonymize each file, (2) create a patient for you " +
                        "if it doesn't already exist, (3) remove any entities of the same type " +
                        "as the entities being upload, and (4) upload the patient entities to " +
                        "the selected patient. Press the Upload button below when you are " +
                        "ready to initiate the upload or use the button above to add additional " +
                        "DICOM files to the upload batch.")
                else:
                    self.upload_files_message_variable.set("No valid DICOM files were found in " +
                        "the selected directory or in the set of selected files. Use the button " +
                        "above to add additional DICOM files to the upload batch.")

    def _choose_directory(self):
        self.app.root.update()
        upload_directory = filedialog.askdirectory(initialdir=self.app.root_path, title="Choose directory to upload")
        self.app.root.update()
        if upload_directory:
            upload_file_paths = []
            for root, dirs, files in os.walk(upload_directory):
                for name in files:
                    upload_file_paths.append(os.path.join(root, name))
            self.app.add_files(upload_file_paths)

    def _choose_files(self):
        self.app.root.update()
        upload_file_paths = filedialog.askopenfilenames(initialdir=self.app.root_path, title="Choose files to upload")
        self.app.root.update()
        if upload_file_paths:
            self.app.add_files(upload_file_paths)

    def _clear_files(self):
        self.app.clear_files()
        self.app.render()

    def _upload_files(self):
        self.app.upload_files()

class ResultsPage(object):
    def __init__(self, app):
        self.app = app

        # Variables
        self.results_instructions_variable = StringVar()

        # Initialize Widgets
        self.step3_label_frame = ttk.Labelframe(self.app.mainframe, text='Step 3: View Results', padding="10")
        self.step3_label_frame.columnconfigure(0, weight=1)
        self.step3_label_frame.columnconfigure(1, weight=1)
        self.results_instructions = ttk.Label(self.step3_label_frame, textvariable=self.results_instructions_variable, wraplength=600)
        self.view_patient_button = ttk.Button(self.step3_label_frame, text='View Patient in ProKnow DS', command=self._open_patient)

    def render(self):
        data = self.app.results_page_data
        if "ready" not in data or not data["ready"]:
            self.step3_label_frame.grid_remove()
            return

        # Grid widgets
        self.step3_label_frame.grid(column=0, row=2, sticky=(N, W, E))
        self.results_instructions.grid(column=0, row=0, columnspan=2, sticky=(W,))
        self.view_patient_button.grid(column=0, row=1, sticky=(E,))

        if "scorecard" in data:
            self.results_instructions_variable.set('Your submission is complete. You may make ' +
                'changes to your submission by uploading new files. To view your patient or ' +
                'scorecard for your submission, use the button below.')
        else:
            self.results_instructions_variable.set('Your submission is complete. You may make ' +
                'changes to your submission by uploading new files. To view your patient for ' +
                'your submission, use the buttons below.')

    def _open_patient(self):
        base_url = self.app.base_url
        workspace = self.app.credentials_page_data["workspace"]
        patient = self.app.uploads_page_data["patient"]
        webbrowser.open(f"{base_url}/{workspace.slug}/patients/{patient.id}/browse")
