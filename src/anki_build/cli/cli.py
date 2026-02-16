import click

from .build import build

@click.group()
@click.pass_context
def cli(ctx) -> None:
    ctx.ensure_object(dict)

cli.add_command(build)
