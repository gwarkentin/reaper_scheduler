import os
import subprocess
import requests
import json
from jsonschema import validate
import datetime

def upload_file(file_path):
    return file_path

def upload_files(files):
    uploaded_files = []
    failed_files = []
    for file in files:
        uf = upload_file(file['render_filepath'])
        if uf is not None:
            uploaded_files.append(file)
        else:
            failed_files.append(file)
    return [uploaded_files,failed_files]

def validate_config(config, config_schema_fp="config_schema.json"):
    if os.path.exists(config_schema_fp):
        with open(config_schema_fp,'r') as config_schema_file:
            config_schema = json.load(config_schema_file)
            validate(config, config_schema)
            return config
    raise FileExistsError(f"Config schema doesn't exist at path: {config_schema_fp}")

def get_config_local(path):
    if os.path.exists(path):
        with open(path,'r') as config_file:
            config = json.load(config_file)
            return validate_config(config)
    raise FileExistsError(f"Config doesn't exist at path: {path}")
            
def get_config_remote(url):
    response = requests.get(url) 
    if response.status_code == 200:
        config = response.json()
        return validate_config(config) 
    raise RuntimeError(f'Unexpected response from server requesting config: {response.status_code}, {response.text}')

def render_file(file_path):
    args = ['/Applications/REAPER.app/Contents/MacOS/REAPER', '-nosplash','-renderproject', file_path]
    sp = subprocess.run(args)
    if sp.returncode == 0:
        return 0
    else:
        raise RuntimeError(f'Render process failed with return code {sp.returncode}')

def render_and_check(file):
    if os.path.exists(file["project_filepath"]):
        render_file(file["project_filepath"])
        if os.path.exists(file["render_filepath"]):
          return file
        raise FileExistsError(f'File {file["render_filepath"]} not found after rendering.\nDouble check the render file location in Reaper before saving and closing.')
    raise FileExistsError(f'Project {file["project_filepath"]} not found.')

def process_files(file_list):
    rendered_files = []
    failed_files = []
    uploaded_files = []
    for file in file_list:
        rf = render_and_check(file)
        if rf is not None:
            rendered_files.append(rf)
        else:
            failed_files.append([file,'Failed render',])
                    
    if len(rendered_files) > 0:
        [uploaded_files, failed] = upload_files(rendered_files)
        failed_files.extend(failed)

    return [rendered_files, uploaded_files, failed_files]

def main():
    config = get_config_local('config.json')
    print(f'Config: {config}')
    if config is not None:
        file_list = config['file_list']
        [rendered_files, uploaded_files, failed_files] = process_files(file_list)
        print(f'Rendered: {len(rendered_files)}\nUploaded: {len(uploaded_files)}\nFailed: {len(failed_files)}')

        results = {
            "rendered_files": rendered_files,
            "uploaded_files": uploaded_files,
            "failed_files": failed_files
        }
        with open(f'./render_results{datetime.date.today().strftime("%Y%d%m")}','w') as render_results_file:
            json.dump(results, render_results_file)

if __name__ == "__main__":
    main()