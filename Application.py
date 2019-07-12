import os
import json
import tempfile
import shutil
import pydicom
import webbrowser
from tkinter import *
from tkinter import ttk, filedialog, messagebox

from proknow import ProKnow, ProKnowError, HttpError

from Steps import CredentialsPage, UploadsPage, ResultsPage

class Application(object):
    ENTITY_TYPES = ["image_set", "structure_set", "plan", "dose"]

    ENTITY_TYPE_REQUIRED_MAP = {
        "image_set": "is_image_set_required",
        "structure_set": "is_structure_set_required",
        "plan": "is_plan_required",
        "dose": "is_dose_required"
    }

    ENTITY_TYPE_NAME_MAP = {
        "image_set": "Image Set",
        "structure_set": "Structure Set",
        "plan": "Plan",
        "dose": "Dose"
    }

    MODALITY_ENTITY_TYPE_MAP = {
        "CT": "image_set",
        "MR": "image_set",
        "RTSTRUCT": "structure_set",
        "RTPLAN": "plan",
        "RTDOSE": "dose",
    }

    def __init__(self):
        self.home_path = os.path.expanduser('~')
        self.root_path = os.path.abspath(os.sep)

        # Load app configurations
        self.app_configuration_path = os.path.abspath("./config/config.json")
        if os.path.exists(self.app_configuration_path):
            with open(self.app_configuration_path, 'r') as file:
                self.app_configuration = json.load(file)
        else:
            raise FileNotFoundError(f"App configuration file {self.app_configuration_path} does not exist")
        self.project_name = self.app_configuration["project_name"]
        self.base_url = self.app_configuration["base_url"]

        # Load user configuration
        self.user_configuration_path = os.path.join(self.home_path, ".proknow", "uploader", self.project_name, "user_configuration.json")
        if os.path.exists(self.user_configuration_path):
            with open(self.user_configuration_path, 'r') as file:
                self.user_configuration = json.load(file)
        else:
            self.user_configuration = {}

        # Initialize the application
        self.root = Tk()
        self.root.title(f"{self.project_name} Uploader")
        self.root.protocol("WM_DELETE_WINDOW", self._destroy)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        row = 0
        # Info link
        if "info_link" in self.app_configuration:
            self.info_link_frame = ttk.Frame(self.root, padding="5 5 5 0")
            self.info_link_frame.grid(column=0, row=row, sticky=(W,E))
            self.info_link_frame.columnconfigure(0, weight=1)
            self.info_link_label = ttk.Label(self.info_link_frame, text=self.app_configuration["info_link"]["text"], foreground="blue", cursor="hand2", wraplength=600)
            self.info_link_label.bind("<Button-1>", lambda e: webbrowser.open_new(self.app_configuration["info_link"]["url"]))
            self.info_link_label.grid(column=0, row=0)
            row += 1

        # Mainframe
        self.mainframe = ttk.Frame(self.root, padding="20")
        self.mainframe.grid(column=0, row=row, sticky=(N, W, E, S))
        self.mainframe.columnconfigure(0, weight=1)

        self.credentials_page = CredentialsPage(self)
        self.uploads_page = UploadsPage(self)
        self.results_page = ResultsPage(self)

        self._initialize()

    @staticmethod
    def anonymize(dataset, identifier):
        # Set identifier
        dataset.PatientID = identifier
        dataset.PatientName = identifier

        # Set birthdate
        if "PatientBirthDate" not in dataset or len(dataset.PatientBirthDate) != 8:
            dataset.PatientBirthDate = None
        else:
            dataset.PatientBirthDate = f"{dataset.PatientBirthDate[:4]}0101"

        # Set deidentification fields
        dataset.PatientIdentityRemoved = "YES"
        dataset.DeidentificationMethod = "Uploader Deidentification"

        # Clear sensitive data elements of type 2 (required)
        tags = [
            # "PatientBirthDate", - Handled by special logic above
            "ReferringPhysicianName"
        ]
        for tag in tags:
            if tag in dataset:
                dataset.data_element(tag).value = ""

        # Remove sensitive data elements of type 3 (optional)
        tags = [
            "OtherPatientIDs",
            "OtherPatientIDsSequence"
            "OtherPatientNames",
            "PatientAlternativeCalendar",
            "PatientBirthDateInAlternativeCalendar",
            "PatientBirthTime",
            "PatientDeathDateInAlternativeCalendar",
            "PatientComments",
            "ResponsiblePerson",
            "ResponsiblePersonRole",
            "ResponsibleOrganization",
            "ReferringPhysicianIdentificationSequence",
            "ConsultingPhysicianName",
            "ConsultingPhysicianIdentificationSequence",
            "PhysiciansOfRecord",
            "PhysiciansOfRecordIdentificationSequence",
            "NameOfPhysiciansReadingStudy",
            "PhysiciansReadingStudyIdentificationSequence",
            "InstitutionName",
            "InstitutionAddress",
            "StationName",
            "InstitutionalDepartmentName",
            "PerformingPhysicianName",
            "PerformingPhysicianIdentificationSequence",
            "OperatorsName",
            "OperatorIdentificationSequence",
        ]
        for tag in tags:
            if tag in dataset:
                delattr(dataset, tag)

    def add_files(self, paths):
        data = self.uploads_page_data
        if "uploads" not in data:
            data["uploads"] = {
                "tempdir": tempfile.mkdtemp(prefix="com.proknow."),
                "inpaths": set(),
                "outpaths": {
                    "image_set": [],
                    "structure_set": [],
                    "plan": [],
                    "dose": [],
                },
                "series_info": {
                    "image_set": set(),
                    "structure_set": set(),
                    "plan": set(),
                    "dose": set(),
                },
            }

        for path in paths:
            if path not in data["uploads"]["inpaths"]:
                data["uploads"]["inpaths"].add(path)
                dataset = pydicom.dcmread(path, force=True)
                if "Modality" in dataset:
                    modality = dataset.Modality
                    if modality in self.MODALITY_ENTITY_TYPE_MAP:
                        entity_type = self.MODALITY_ENTITY_TYPE_MAP[modality]
                        self.anonymize(dataset, data["identifier"])
                        _, outpath = tempfile.mkstemp(dir=data["uploads"]["tempdir"],suffix=".dcm")
                        dataset.save_as(outpath, False)
                        data["uploads"]["series_info"][entity_type].add(dataset.SeriesInstanceUID)
                        data["uploads"]["outpaths"][entity_type].append(outpath)

        self.render()

    def clear_files(self):
        data = self.uploads_page_data
        if "uploads" in data:
            shutil.rmtree(data["uploads"]["tempdir"])
            del data["uploads"]

    def refresh_patient(self):
        cdata = self.credentials_page_data
        if self.pk is None or cdata["session"] is None or cdata["workspace"] is None or cdata["scorecard"] is None:
            return

        udata = self.uploads_page_data

        try:
            name = cdata["session"]["name"]
            udata["identifier"] = name[:64] if len(name) > 64 else name
            udata["patient"] = self.pk.patients.find(cdata["workspace"].id, mrn=name)
            udata["entities"] = {}
            for entity_type in self.ENTITY_TYPES:
                udata["entities"][entity_type] = []
            if udata["patient"] is not None:
                for entity_type in self.ENTITY_TYPES:
                    udata["entities"][entity_type] = udata["patient"].get().find_entities(type=entity_type)

            self.render()
            self.refresh_results()
        except Exception as err:
            messagebox.showinfo(message='An error occurred while attempting to find your ' +
                'submission. Please try again or close and reopen this app. If the problem ' +
                f'persists, report this error to support@proknow.com. \n{str(err)}')

    def refresh_proknow(self):
        self._reset()

        if "credentials_path" not in self.user_configuration:
            self.render()
            return

        # Load session
        try:
            self.pk = ProKnow(self.app_configuration["base_url"], self.user_configuration["credentials_path"])
            self.credentials_page_data["session"] = self.pk.session.get()
            self.credentials_page_data["session_error"] = None
        except HttpError as err:
            self.credentials_page_data["session"] = None
            self.credentials_page_data["session_error"] = err.body
        except ProKnowError as err:
            self.credentials_page_data["session"] = None
            self.credentials_page_data["session_error"] = err.message
        except Exception as err:
            self.credentials_page_data["session"] = None
            self.credentials_page_data["session_error"] = str(err)

        if self.credentials_page_data["session"] is None:
            self.credentials_page_data["workspace"] = None
            self.credentials_page_data["workspace_error"] = None
            self.credentials_page_data["scorecard"] = None
            self.credentials_page_data["scorecard_error"] = None
        else:
            # Load workspace
            try:
                self.credentials_page_data["workspace"] = self.pk.workspaces.resolve(self.app_configuration["workspace_id"])
                self.credentials_page_data["workspace_error"] = None
            except HttpError as err:
                self.credentials_page_data["workspace"] = None
                self.credentials_page_data["workspace_error"] = err.body
            except ProKnowError as err:
                self.credentials_page_data["workspace"] = None
                self.credentials_page_data["workspace_error"] = err.message
            except Exception as err:
                self.credentials_page_data["workspace"] = None
                self.credentials_page_data["workspace_error"] = str(err)

            # Load scorecard
            try:
                self.credentials_page_data["scorecard"] = self.pk.scorecard_templates.resolve(self.app_configuration["scorecard_template_id"])
            except HttpError as err:
                self.credentials_page_data["scorecard"] = None
                self.credentials_page_data["scorecard_error"] = str(err)
            except ProKnowError as err:
                self.credentials_page_data["scorecard"] = None
                self.credentials_page_data["scorecard_error"] = str(err)
            except Exception as err:
                self.credentials_page_data["scorecard"] = None
                self.credentials_page_data["scorecard_error"] = str(err)

        self.render()
        self.refresh_patient()

    def refresh_results(self):
        self.results_page_data = {}

        # Set ready
        ready = True
        for entity_type in self.ENTITY_TYPES:
            required = self.app_configuration[self.ENTITY_TYPE_REQUIRED_MAP[entity_type]]
            if required and len(self.uploads_page_data["entities"][entity_type]) == 0:
                ready = False
                break
        self.results_page_data["ready"] = ready

        # Load scorecard
        if ready and self.app_configuration["is_dose_required"]:
            template = self.credentials_page_data["scorecard"].get()
            scorecards = self.uploads_page_data["entities"]["dose"][0].get().scorecards
            scorecard = scorecards.find(name=template.name)
            if scorecard is None:
                scorecard = scorecards.create(template.name, template.computed, template.custom)
            else:
                scorecard = scorecard.get()
            self.results_page_data["scorecard"] = scorecard

        self.render()

    def render(self):
        self.credentials_page.render()
        self.uploads_page.render()
        self.results_page.render()

    def run(self):
        self.root.mainloop()

    def upload_files(self):
        try:
            cdata = self.credentials_page_data
            data = self.uploads_page_data
            # Create patient
            if data["patient"] is None:
                identifier = data["identifier"]
                patient = self.pk.patients.create(cdata["workspace"].id, identifier, identifier)
            else:
                patient = data["patient"]

            # Delete entities and discover paths
            paths = []
            for entity_type in self.ENTITY_TYPES:
                if len(data["uploads"]["outpaths"][entity_type]) > 0:
                    entities = data["entities"][entity_type]
                    for entity in entities:
                        entity.delete()

                paths = paths + data["uploads"]["outpaths"][entity_type]

            # Upload entities
            patient.upload(paths)

            self.clear_files()
            self._reset_uploads_data()
            self.refresh_patient()
        except Exception as err:
            messagebox.showinfo(message='An error occurred while attempting to upload your ' +
                'submission. Please try again or close and reopen this app. If the problem ' +
                f'persists, report this error to support@proknow.com. \n{str(err)}')

    def save_user_configuration(self):
        parts = [self.home_path, ".proknow", "uploader", self.project_name]
        length = len(parts)
        for i in range(length):
            subparts = parts[:(i+1)]
            directory = os.path.join(*subparts)
            if not os.path.isdir(directory):
                os.mkdir(directory)
        with open(self.user_configuration_path, 'w') as file:
            json.dump(self.user_configuration, file)

    def _destroy(self):
        self.clear_files()
        self.root.destroy()

    def _initialize(self):
        self.pk = None
        self.credentials_page_data = {}
        self.uploads_page_data = {}
        self.results_page_data = {}
        if "credentials_path" in self.user_configuration:
            if not os.path.exists(self.user_configuration["credentials_path"]):
                del self.user_configuration["credentials_path"]
        self.refresh_proknow()

    def _reset(self):
        self._reset_proknow()
        self._reset_credentials_data()
        self._reset_uploads_data()
        self._reset_results_data()

    def _reset_proknow(self):
        self.pk = None

    def _reset_credentials_data(self):
        self.credentials_page_data = {}

    def _reset_results_data(self):
        self.results_page_data = {}

    def _reset_uploads_data(self):
        self.clear_files()
        self.uploads_page_data = {}
