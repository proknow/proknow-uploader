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

## Development

### Requirements

- Python 3.7 (Python 2.7 may work, but no guarantees) with `pip`
- [Pipenv](https://pipenv.readthedocs.io/en/latest/)

### Setup

One you have Python installed and Pipenv added as package with `pip`, use `pipenv` to install your development environment.

```
pipenv install --dev
```

Then start the shell in the virtual environment.

```
pipenv shell
```
