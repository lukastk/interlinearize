# Interlinearizer

An [interlinear](https://www.wikiwand.com/en/Interlinear_gloss) book is an
annotaded version of a text, where each word of the original text
is accompanied with a translation just underneath. `interlinearizer`
is a tool with which we can convert EPUB files (or any other format
supported by Calibre) into their respective interlinearized versions.

For example, see below the interlinearized version of the
first passage of Voltaire's *Candide*:

<img width="100%" src="docs/interlinearizer_sample.png">

Each word is
translated *individually* and without context. This means that
in most cases the translations will read awkardly and sometimes
imprecisely as well. For the purposes of its intended usage this is
not much of an issue, as a competent reader in a target language
only looks up the occasional low-frequency word, and
should in most cases be able to contextualize it within the larger
sentence.

The program uses [Calibre's](https://calibre-ebook.com/) `ebook-convert` to convert between formats and[`googletrans`](https://pypi.org/project/googletrans/) to translate words. So far `interlinearizer` has only been tested on books in the `.epub`
format, and translations from French to English. Although in theory
the program should work fine with any book format supported by Calibre,
and any languages supported by Google Translate. `interlinearizer`
has only been tested on Linux.

The repository comes with two examples. *Candide* by Voltaire and
*Madame Bovary* by Gustave Flaubert, along with their interlinear
versions. You can find them inside the compressed folder
[`interlinearized_books.zip`](interlinearized_books.zip).

## Installation

`interlinearizer` does not need to be installed and can be run straight
out of the repository. However, a few dependencies needs to be staisfied.
The interlinearizer depends on `googletrans`, `BeautifulSoup` and `nltk`.
To install these, `cd` into the repository and run the command

    pip install requirements.txt

You will also have to install [Calibre](https://calibre-ebook.com/),
as `interlinearizer` makes use of its `ebook-convert`.
Furthermore, you'll need to have Python 3 installed.

If you do want to "install" `interlinearizer` (i.e. make it accessible
from anywhere within the terminal), you can move `interlinearizer.py`
to `/usr/local/bin`:

    chmod +x interlinearizer.py
    cp interlinearizer.py /usr/local/bin/interlinearizer

or any other folder that is in your `PATH` environmental variable. If you
do this, then `interlinearizer` will automatically generate configuration
files in `~/.interlinearizer/` the first time it is run.

## Usage

Use the interlinearizer in the following way:

```bash
python interlinearizer.py src dest book.format1 output.format2
```

where `src` and `dest` are the source and destination languages
respectively, and `book.format1` the input book of a given format
and `output.format2` the output of the desired format.

For example, to translate the copy of *Candide* in the repository
execute the following command

```bash
python interlinearizer.py fr en "Candide - Voltaire.epub" "Candide - Voltaire (interlinearized).epub"
```

If you want an HTML version of the interlinearized book, then omit the
file extension for the output

```bash
python interlinearizer.py fr en "Candide - Voltaire.epub" "Candide - Voltaire (interlinearized)"
```

Whenever you use the `interlinearizer`, the dictionaries it assembles
will always be stored as text files in the `dict` folder (for more
details see the section below), so the more books you use it on
the less time it will take to translate.

## Settings

You can change the formatting of the interlinearized text by editing
the `interlinear.css` style file. Other settings can be found in the
`interlinearizer.config` file.

You can also edit the dictionaries directly in the `dict` folder. Each
dictionary is named in the format `src_dest.txt`, so a French to English dictionary would be in `dict/fr_en.txt` for example. See
[here](./docs/language_codes.md) for a list of language codes.

`interlinearizer` always looks for the configuration and dictionary
files within the execution folder first. If it cannot find the files
there, it will then look in `~/.interlinearizer`. If that folder
does not exist, it will then create it and place default config files
there.
