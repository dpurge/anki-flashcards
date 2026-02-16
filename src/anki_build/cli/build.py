import click

from ..lib import (
    AnkiPackage,
    AnkiProject,
)

@click.command('build')
@click.pass_context
@click.option('-o', '--output', type=click.Path(exists=False, readable=True, resolve_path=True, file_okay=True, dir_okay=False), default=None)
@click.argument('filename', nargs=1, type=click.Path(exists=True, readable=True, resolve_path=True, file_okay=True, dir_okay=False))
def build(ctx, filename: str, output: str) -> int:
    ctx.ensure_object(dict)
    if not output:
        output = f'{filename.rstrip('.yml').rstrip('.anki')}.apkg'
    project = AnkiProject(filename)
    with AnkiPackage() as pkg:
        pkg.load(project)
        pkg.save(output)
    return 0
