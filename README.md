# Anki flashcards

## Build

Build with `task`:

```sh
task clean build
```

Build with `anki-build`:

```sh
uv run anki-build --help
uv run anki-build build ./dat/lang-vocabulary/deu/flashcard.yml -o ./out/german.apkg
```
