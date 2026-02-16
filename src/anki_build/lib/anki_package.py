from pathlib import Path
from tempfile import mkdtemp

from anki.lang import set_lang

from anki.collection import (
    Collection,
    # Card,
    Note,
    # ImportAnkiPackageOptions,
    # ImportAnkiPackageRequest,
    # ExportAnkiPackageOptions,
    # ExportAnkiPackageRequest,
    # DeckIdLimit,
)

from .reader import read_data

from anki.errors import (
    DBError,
    # NotFoundError,
)

# from anki.models import ModelManager
from anki.exporting import AnkiPackageExporter

from anki.consts import MODEL_STD, MODEL_CLOZE 

class AnkiPackage(object):
    """Work with Anki package"""

    def __init__(self, workspace: str = None):
        self._mine = False
        self._open = False

        if not workspace:
            workspace = mkdtemp(suffix='.apkg', prefix='anki-build-')
            self._mine = True

        self.workspace = Path(workspace)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        if self._mine:
            self.delete()

    def open(self) -> None:
        if not self._open:
            if not self.workspace.exists():
                self.workspace.mkdir(parents=True, exist_ok=True)
                self._mine = True

            if not self.workspace.is_dir():
                raise Exception(f'APKG workspace is not a directory: {self.workspace.absolute()}')
            
            collection = self.workspace / 'collection.anki2'

            if not collection.exists():
                with open(collection, "w") as f:
                    pass

            if not collection.is_file():
                raise Exception(f'APKG collection database is not a file: {collection.absolute()}')

            try:
                self.collection = Collection(collection.absolute())
            except DBError as e:
                raise Exception(f'APKG collection database cannot be opened: {collection.absolute()}')
            
            
            set_lang("en_US")
            self.collection.upgrade_to_v2_scheduler()
            # self.model_manager = ModelManager(self.collection)
        
        self._open = True

    def close(self) -> None:
        self.collection.close()
        self._open = False

    def delete(self) -> None:
        def rmtree(f: Path):
            if f.is_file():
                f.unlink()
            else:
                for child in f.iterdir():
                    rmtree(child)
                f.rmdir()

        rmtree(self.workspace)

    def save(self, filename: str) -> Path:
        pkg = Path(filename)
        if pkg.exists():
            raise Exception(f'File already exists, package cannot be saved: {pkg.absolute()}')
        

        # model_mgr = ModelManager(self.collection)
        # for m in model_mgr.all_names_and_ids():
        #     m_id = m.id
        #     m_name = m.name
        #     print(f'{m_id} - {m_name}')

        exporter = AnkiPackageExporter(self.collection)
        exporter.exportInto(str(pkg))
        return pkg
    
    

    def load(self, project) -> None:

        deck_id = self.use_deck(project.deck_name())
        model = self.use_model(project.model())

        self.import_notes(
            deck = deck_id,
            model = model,
            data = project.data(),
            field_type = project.field_type(),
            note_index = project.note_index(),
            merge_fields = project.merge_fields(),
            field_template = project.field_template())

    def use_deck(self, deck_name: str):
        id = self.collection.decks.id(deck_name)
        # self.collection.decks.save()
        self.collection.decks.currentId = id
        return id

    def use_model(self, model):
        expected_fields = [field['name'] for field in model['fields']]

        models = self.collection.models
        m = models.by_name(model['name'])

        if not m:
            m = models.new(model['name'])
            
            if model['kind'] == 'normal':
                m["type"] = MODEL_STD
            elif model['kind'] == 'cloze':
                m["type"] = MODEL_CLOZE
            else:
                raise f"Unsupported model kind: {model['kind']}"

            m["sortf"] = 0
            for i in expected_fields:
                f = models.new_field(i)
                models.add_field(notetype=m, field=f)
            for i in model['templates']:
                t = models.new_template(i['name'])
                if 'qfmt' in i: t['qfmt'] = i['qfmt'].read_text()
                if 'afmt' in i: t['afmt'] = i['afmt'].read_text()
                models.add_template(m, t)
            models.add(m)

        style = model['style'] if 'style' in model else None
        if style:
            if style['css']: m["css"] = style['css'].read_text()
            latex = style['latex'] if 'latex' in style else None
            if latex:
                if 'prefix' in latex: m["latexPre"] = latex['prefix'].read_text()
                if 'postfix' in latex: m["latexPost"] = latex['postfix'].read_text()
                if 'svg' in latex: m["latexsvg"] = latex['svg']

        existing_fields = models.field_names(m)

        for i in expected_fields:
            if not i in existing_fields:
                f = models.new_field(i)
                models.add_field(notetype=m, field=f)

        for f in m['flds']:
            fld = next((x for x in model['fields'] if x['name'] == f['name']), None)
            if 'rtl' in fld: f['rtl'] = fld['rtl']
            if 'description' in fld: f['description'] = fld['description']
            
            font = fld['font'] if 'font' in fld else None
            if font:
                if font['name']: f['font'] = font['name']
                if font['size']: f['size'] = font['size']

        models.save(m)
        return m
    
    def import_notes(self, deck, model, data, field_type, note_index, merge_fields, field_template):
        col = self.collection
        note_name = model['name']
        for rec, tags in read_data(data, field_type, field_template):
            note = None

            query = f'deck:"{col.decks.name(deck)}" note:"{note_name}"'
            for k in note_index:
                query += f' {k}:'
                v = rec[k]
                if v:
                    query += f'"{v}"'

            notes = col.find_notes(query)
            if len(notes):
                note = Note(col=col,id=notes[0])
                note.load()
            else:
                note = col.new_note(model)

            note.tags.extend(tags)
            for k in rec:
                if not k in merge_fields:
                    note[k] = rec[k]
                    continue

                v = [i.strip() for i in note[k].split(';') if i]
                for i in rec[k].split(';'):
                    i = i.strip()
                    if i and not i in v:
                        v.append(i)

                note[k] = '; '.join(v)

            if note.id:
                col.update_note(note)
            else:
                col.add_note(note, deck)
