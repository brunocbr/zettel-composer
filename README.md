# Zettel Composer

A tool for combining notes in a "Zettelkasten" system based on Markdown and wiki links.

## Installation

Clone the project in a directory of your choosing (e. g. `~/GitHub`):

```shell
mkdir -p ~/GitHub
cd ~/GitHub
clone https://github.com/brunocbr/zettel-composer.git
```

If you want to use Marked Streaming Preview, you have to install the Python Objective-C bridge:

```shell
pip install -U pyobjc
```

## Basic features

The script takes as its argument the name of a file which will be used as an `index` note. Wiki links prepended with a section sign (`§ [[1234]]`) in the index will produce the combination of the corresponding notes in the output:

```sh
~/GitHub/zettel-composer/zettel-compose.py "~/archive/2345 My index note.markdown"
```

With the above command, the script will simply print the combined notes and quit. You can though get a live preview using [Marked 2](https://marked2app.com/) and telling the script to keep watching the files for changes:

```sh
~/GitHub/zettel-composer/zettel-compose.py --watch --stream-to-marked "~/archive/2345 My index note.markdown"
```

The `index` note will control the order in which notes will be printed. It is recommended that you include all the relevant notes in the index, e. g. in an outline (but the script will also include others as it finds references while scanning the notes).

Often when working with "Zettelkasten" notes, you'll want to make cross references to notes not necessarily intended for "public" consumption. This is why the default behaviour is to only reference and print notes using a non-standard notation of wiki links prefixed by the section mark (this character can usually be typed with `⌥ 6` on the mac, `C-x 8 S` in emacs):

```
This is a reference to § [[1234]].
```

You can override the default behaviour with the `--link-all` option if you want to print notes referenced with "standard" wiki links.

There's also a notation for references that necessarily will not be printed, even with the above option. It consists in a wiki link at the very beginning of a line, followed by a colon:

```
[[1234]]: This develops some thoughts from a cross-referenced note that should never be printed.
```

Other special conventions are available for working with quotes and pandoc citations (see below).

By default, the script will threat every separate note as a "section" or "paragraph" and number them sequentially (`1.`, `2.`, `3.`). They can always be cross referenced with the `§ [[1234]]` notation (which yields `(§1)`, `(§2)`, `(§3)` etc. in the output).

Markdown headings in the beginning of the notes will be accomodated before the paragraph numbers, so that you can, e. g., break the output in different chapters and sections. You can also suppress paragraph headings by calling the script with the `-n` option.

Footnote references will be adapted to avoid duplication.

### Basic parameters

| Parameter                     | Description                          |
| ----------                    | ----------                           |
| `-S`, `--suppress-index`      | Do not print the `index` note.       |
| `-W`, `--watch`               | Don't quit, watch files for changes. |
| `-M`, `--stream-to-marked`    | Stream to Marked 2.                  |
| `-O`, `--output=` *file name* | Specify *file name* as the output.   |
| `-v`                          | Verbose mode.                        |


### Some tweaks

| Parameter                              | Description                                                                                                              |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| `--link-all` or `-L`                   | Link and print all wiki linked notes, even if not prefixed by `§`.                                                       |
| `-n`, `--no-paragraph-headings`        | Do not print paragraph headings (`1.`, `2.`, `3.` etc.)                                                                  |
| `--no-separator`                       | Do not separate notes in the output with a horizontal bar.                                                               |
| `-I`                                   | Only include notes linked from the `index` note. References found in children notes will not be printed.                 |
| `--custom-url=` *string*               | A custom URL prepended to IDs in order to create links inside the CriticMarkup comments. Default: `thearchive://match/`. |
| `-C`, `--no-commented-references`      | Disable CriticMarkup comments.                                                                                           |
| `-s`, `--sleep-time=` *seconds*        | How long to "sleep" between file watching cycles. Default is 2 seconds.                                                  |
| `-H`, `--heading-identifier=` *string* |                                                                                                                          |
| `--section-symbol=` *string*           | Set symbol used in the output to print references to sections/paragraphs. Default is `§`.                                |
| `--no-title`                           | Do not create headings out of a note's `title` field                                                                     |



## Advanced features
### Quotes and text fragments ###


You may create a note (`1235` in this example) containing but a quote or fragment of text. You can then quote its actual contents inside another note in a line like the one below:

```
> [[1235]]
```


This is very useful if you do translations, as you may work with them in notes separated from the text where they are to be included (e. g. a paper, lecture notes). You can also create handouts from the very same note, using the handout option (`-h`).

The quote will receive a sequential numerical identification (`T1`, `T2`, `T3` etc.) and may be later referenced[^2] (wiki links will be transformed in `T1`, `T2`, `T3` etc.).

The quoted note's title is assumed to be a citation reference and will be printed either inside parentheses or in a heading (respectivelly in normal and handout modes)[^3].

If you just want to insert the contents of the body of a note[^1], without any special handling, you can use the following:

```
+ [[1235]]
```


| Parameter  | Description                         |
| ---------- | ----------                          |
| `-t` *n*   | Set the initial text number (`Tn`). |


### Handouts ###

| Parameter | Description                                 |
| --------- | ----------                                  |
| `-h`      | Handout mode (only quotes will be printed). |
| `-h+`     | Also print section headings.                |



### Parallel texts ###

Bilingual passages may be inserted by designating "left" and "right" texts:

```
> [[1235]] :: [[1236]]
```

In normal mode, the "left" text will be printed first, followed by the "right" text (unless this behaviour is modified by `-G`).

With option `-P`, proper parallel texts are rendered in `LaTeX` (via `pandoc`), the output requiring for later processing a `\ParallelTexts` macro that you should define e. g. in your pandoc template (making use of `reledpar` or other package). 

```latex
\ParallelTexts{%
... Left text ...
}{%
... Right text ...
}
```

| Parameter  | Description                                                                  |
| ---------  | ----------                                                                   |
| `-G` *opt* | Choose which texts(s) to print. *opt* should be `l`,  `r` or `lr` (default). |
| `-P`       | Render parallel texts in LaTeX.                                              |


### Pandoc citations ###

Notes may have bibliographical metadata in their frontmatter:

```
---
citekey:	Author1999
loc:		12-45
...
```

This information can be used elsewhere, creating  pandoc-style citations by making a refence to the notes with `@ [[1234]]` (parenthetical citation), `-@ [[1234]]` (publication year), `@@ [[1233]]` (inline citation).


## Use-Cases

You can create a shell script with preconfigured parameters for the `Zettel Composer`, passing the `index` file name as an argument. The examples below will assume this setup.

Tip: If you are on the mac, you may use scripts like these with the `Automator`, creating applications. You may then use those applications to open your `index` notes from your preferred editor (such as [The Archive](https://zettelkasten.de/the-archive/) or [nvAlt](https://brettterpstra.com/projects/nvalt/)).


Case 1: given a structure note, browse all wiki linked notes in Marked. This is very useful e. g. with a structure note related to annotations of a book, containing links for the individual chapter/section notes.

```bash
#!/bin/bash
open -a "Marked 2"
$HOME/GitHub/zettel-composer/zettel-compose.py -L --stream-to-marked "${1}"
```

Case 2: Continuously generate a handout, while at the same time having a live preview:

```bash
open -a "Marked 2"
pkill -f zettel-compose.py
$HOME/GitHub/zettel-composer/zettel-compose.py -W -h+ -P -O "$HOME/Downloads/Handout.md" "${1}" &
$HOME/GitHub/zettel-composer/zettel-compose.py -W --stream-to-marked -h+ "${1}"
```

You can use `Handout.md` as input for some other process, like converting it to PDF with `LaTeX` and `pandoc`.

Case 3: Compose a book consisting of many chapters distributed in different notes, but don't print the index itself. The output will be later processed with `LaTeX`, which will take care of creating a table of contents:

```bash
OUT=$HOME/Documents/My-Book.md
$HOME/GitHub/zettel-composer/zettel-compose.py -S -I -n --no-separator -O "${OUT}" "${1}"
```


[^1]: I speak of the "body" of a note because the script will recognize a YAML frontmatter and certain field declarations inside it, such as `title:`, `citekey:` or `loc:` (for the later fields, see below).


[^2]: The script doesn't currently support forwarding linking.

[^3]: I suggest that you use underline to format a note title, and avoid asterisks, e. g. `1234 PLATO. _Timaeus_, 29c.markdown`.
