# proknow-uploader

Application for creating unique applications for uploading to ProKnow DS.

## Building an Uploader

To build the uploader you will need a configuration file. It's a good idea to name this file `config.json` and put it in an accessible location. An example of the configuration is given below.

```
{
    "project_name": "ABC123 Plan Challenge",
    "info_link": {
    	"url": "https://proknow.com",
    	"text": "Learn more"
    },
    "base_url": "https://demo.proknow.com",
    "workspace_id": "5c48eb3474404ef753e3e295c4952760",
    "scorecard_template_id": "5b9803186ac0486c82ad6c1cc562e59d",
    "is_image_set_required": true,
    "is_structure_set_required": true,
    "is_plan_required": true,
    "is_dose_required": true
}
```

- `project_name` (required): The name of the uploader. This name will be concatenated with the string "Uploader" and displayed in the uploader's title bar (e.g., "ABC123 Plan Challenge Uploader").
- `info_link` (optional): A link that can be used to point users to documentation on how to use your uploader. The link will be presented with the specified text near the top of the uploader.
	- `url`: The link URL.
	- `text`: The link text.
- `base_url` (required): The ProKnow DS base URL. This SHOULD include `https://` and SHOULD NOT end with a slash.
- `workspace_id` (required): The ID of the workspace in ProKnow DS to which the DICOM data should be uploaded.
- `scorecard_template_id` (required): The ID of the scorecard template that should be applied to an uploaded dose.
- `is_image_set_required` (required): Indicates whether an image set is required as part of the user's submission.
- `is_structure_set_required` (required): Indicates whether a structure set is required as part of the user's submission.
- `is_plan_required` (required): Indicates whether a plan is required as part of the user's submission.
- `is_dose_required` (required): Indicates whether a dose is required as part of the user's submission.

Support for building uploaders is only 

### Windows

Here is the command to build the uploader. Please be sure to replace "Project Name" with the name of the uploader and `config.json` with the path to your config file.

```
pyinstaller --onefile --windowed --add-data "config.json;./" --icon="icon.ico" --name="Project Name" uploader.py Application.py Steps.py
```

### Mac OS

Unfortunately, the uploader cannot be built as a console-less application for Mac OS right now.

In addition, the second workaround listed in [this comment](https://github.com/pyinstaller/pyinstaller/issues/3753#issuecomment-432464838) must be used to get around this error:

```
#### ERROR: Tcl/Tk improperly installed on this system.
```

In any case, here is a command to build a console-based uploader application. Please be sure to replace "Project Name" with the name of the uploader and `config.json` with the path to your config file.

```
pyinstaller --onefile --add-data "config.json:./" --icon="icon.ico" --name="Project Name" uploader.py Application.py Steps.py
```

## Development

### Mac

#### Requirements

- Python 3.7 (Python 2.7 may work, but no guarantees) with `pip`
- [Pipenv](https://pipenv.readthedocs.io/en/latest/)

#### Setup

One you have Python installed, install `pipenv`, install the pipenv virtual environment environment, and start the shell.

```
pip install pipenv
```

```
pipenv install --dev
```

```
pipenv shell
```

Run the uploader in the shell.

```
python uploader.py
```

Note that you'll need a valid `config.json` located in the root of this repository for testing.

### Windows

#### Requirements

- Python 3.7 (Python 2.7 may work, but no guarantees) with `pip`

#### Setup

Once you have Python installed, install the following modules.

```
pip install pyinstaller proknow pydicom
```

```
python uploader.py
```

Note that you'll need a valid `config.json` located in the root of this repository for testing.
