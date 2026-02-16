import yaml
from string import Template
from pathlib import Path

class AnkiProject(object):
    """Work with Anki project"""

    def __init__(self, filename: str):
        project = None

        project_file = Path(filename)
        if not project_file.is_file():
            raise Exception(f'Project does not exist: {project_file.absolute()}')

        with project_file.open(encoding="utf-8") as f:
            try:
                project = yaml.load(f, Loader=yaml.SafeLoader)
            except Exception as e:
                raise Exception(f'Could not parse project file: {e}')
            
        basedir = project_file.parent

        style = project['model']['style'] if 'style' in project['model'] else None
        if style:
            if 'css' in style: style['css'] = basedir / style['css']
            latex = style['latex'] if 'latex' in style else None
            if latex:
                if 'prefix' in latex: latex['prefix'] = basedir / latex['prefix']
                if 'postfix' in latex: latex['postfix'] = basedir / latex['postfix']

        for i in project['model']['templates']:
            if 'qfmt' in i: i['qfmt'] = basedir / i['qfmt']
            if 'afmt' in i: i['afmt'] = basedir / i['afmt']

        for i in project['model']['fields']:
            i['template'] = basedir / i['template']

        for i in project['data']:
            i['filename'] = basedir / i['filename']

        self.basedir = basedir
        self.project_file = project_file
        self.project_data = project

    def deck_name(self):
        return self.project_data['deck']['name']

    def model(self):
        return self.project_data['model']
    
    def field_type(self):
        return {i['name']: i['format'] if 'format' in i else 'text' for i in self.project_data['model']['fields']}
    
    def note_index(self):
        return [i['name'] for i in self.project_data['model']['fields'] if 'index' in i and i['index']]
    
    def merge_fields(self):
        return [i['name'] for i in self.project_data['model']['fields'] if 'merge' in i and i['merge']]
    
    def field_template(self):
        return {i['name']: Template(i['template'].read_text()) for i in self.project_data['model']['fields']}
    
    def data(self):
        return self.project_data['data']
