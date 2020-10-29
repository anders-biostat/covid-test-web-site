## Translations

This document is describing how to add or update translations for the application.

For the translation process a working instance (test server etc.) has to be installed.
This can be done like explained in the main `README.md`. To use the translation commands
it is recommended to use a virtual environment for the Python packages.

For each update in the templates that needs to be translated the commands `update` and `compile`
are needed.

### Preperations

The python environment needs to be activated (if virtual environments are used):

```bash
$ . venv/bin/activate
```

To execute the commands you need to change into the `src` directory:

```bash
$ cd src
```

To see all available commands for translations execute: 

```bash
$ flask translate
Usage: flask translate [OPTIONS] COMMAND [ARGS]...

  Translation and localization commands.

Options:
  --help  Show this message and exit.

Commands:
  compile  Compile all languages.
  init     Initialize a new language.
  update   Update all languages.
```


### Update

The most used command is the update command:
```bash
$ flask translate update
```
It is used to receive all strings from the sourcecode that needs to be translated.
It generates different `.po` files in the `translation` directory. After updating you can edit
the `.po` files to add translations. Many editors exists for this task (e.g. Poedit).

After running this command the percentage of already translated strings is displayed.

### Compile

To make the translations accessible for the server they need to be compiled. This can be done with
the compile command:

```bash
$ flask translate compile
```

### Init

To add new languages the init command is used. You need the two letter code for the 
language to use it. It creates the translation directory and initializes the `.po` file.

Example for english:
```bash
$ flask translate init en
```