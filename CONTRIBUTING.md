# Contributing

<!--toc:start-->
- [Ground rules](#ground-rules)
- [Checks](#checks)
- [Labeling AI-generated work](#labeling-ai-generated-work)
- [Code Formatting](#code-formatting)
<!--toc:end-->

This repository is AI-generated and not affiliated with pret (see [AI.md](AI.md)).
Issues and pull requests are welcome **here**. Please don't take anything from this
repository to pret, or ask pret about it.

## Ground rules

- **`main` builds matching ROMs.** This is a base for mods: a pull request must keep
  HeartGold and SoulSilver byte for byte identical to retail (`make` and
  `make soulsilver` pass). Changes to the game itself belong in your own fork.
- **New layouts and tools come with tests** that rebuild the original files from the
  new sources byte for byte, and with a guide in `docs/modding/` linked from
  [docs/WIKI.md](docs/WIKI.md).
- **Guides say what they're based on**: name the file and line, and list what wasn't
  tried in the game under a **Not verified** heading.
- **Follow pret's conventions where the DS allows it**, pokeemerald's in particular, so
  pret users feel at home.

## Checks

Build both versions with their checksums:

```bash
make
make soulsilver
```

Then the tool tests (some need a build first, for `nitrogfx` and `nitroarc`):

```bash
for t in tools/mapkit/tests/test_*.py tools/pokedata/test_*.py tools/sound/test_sound.py tools/progress/test_progress.py tools/npctrade/test_npctrade.py tools/narcgfx/test_narcgfx.py; do
    python3 "$t" || echo "FAILED: $t"
done
```

The map editor's tests need its PySide6 environment ([tools/mapeditor/README.md](tools/mapeditor/README.md)):

```bash
python3 -m venv tools/mapeditor/.venv && tools/mapeditor/.venv/bin/pip install PySide6   # once
QT_QPA_PLATFORM=offscreen tools/mapeditor/.venv/bin/python -m unittest discover -s tools/mapeditor/tests
```

## Labeling AI-generated work

AI-generated contributions are fine; label them:

- start new files you generated with a comment such as
  `// [AI-GENERATED / NOT AFFILIATED WITH PRET] <model>, <date>`;
- say in the pull request which model or tool wrote it and how you checked it;
- keep a `Co-Authored-By:` line for the model in the commit message if your tool adds one.

## Code Formatting

This repository includes an opinionated `clang-format` specification to ensure that we maintain a common code style. For convenience, a pre-commit hook is also provided in `.githooks` which will run `clang-format` against any staged changes prior to executing a commit.

### Requirements

- `clang-format@18` or newer

### Usage

To set up the pre-commit hook:

```sh
git config --local core.hooksPath .githooks/
```

To run the formatter on the full source tree:

```bash
./format.sh
```

### Nonmatching functions

clang-format does not recognize the syntax for inline asm that is required by mwccarm, so it should be disabled for non-matching functions specifically. clang-format accepts directives via comments of the form `// clang-format [on|off]`. Example:

```c
#ifdef NONMATCHING
void func() {
    // ...
}
#else
// clang-format off
asm void func() {
    push {lr}
    // ...
    pop {pc}
}
// clang-format on
#endif // NONMATCHING
```

### Ubuntu (WSL) Installation

On older versions of Ubuntu, clang-format will default to earlier versions.
To install clang-format-18 on Ubuntu (WSL), run the following:
```sh
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 18
sudo apt install clang-format-18
```
And then create a symbolic link:
```sh
ln -s /usr/bin/clang-format-18 /usr/bin/clang-format
```

If you're using the pre-commit hook, you also want to set up a symlink for git:
```sh
git config alias.clang-format clang-format-18
```
