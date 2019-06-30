# proknow-uploader
Application for creating unique applications for uploading to ProKnow DS


Requirements:
* Python 3.7 or newer
* PyInstaller


Create the uploader JSON configuration file with the format:
```$xslt
{
	"project_name": "ABC123 Plan Challenge",
	"base_url": "https://demo.proknow-staging.com",
	"workspace_id": "5c4f61bad040de2715ebc87b3853a4d6",
	"scorecard_template_id": "5b9803186ac0486c82ad6c1cc562e59d",
	"is_imageset_required": true,
	"is_structure_set_required": true,
	"is_plan_required": true,
	"is_dose_required": true
}


```
To build an uploader on Windows:
```$xslt
pyinstaller --add-data CONFIG.JSON;config.json uploader.py
```
or MacOS/Linux:
```$xslt
pyinstaller --add-data CONFIG.JSON:config.json uploader.py
```
where CONFIG.JSON is the path to the uploader configuration file.


The application will be bundled into the dist/PROJECT_NAME folder where PROJECT_NAME is the value specified for the project_name property in the uploader configuration file.
