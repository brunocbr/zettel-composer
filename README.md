# Zettel Composer

This is a tool for combining notes in a "Zettelkasten" system.

## Basic features

The script takes as its argument the name of a file which will be used as an `index` note. Wiki links prepended with a section sign (`§ [[1234]]`) in the index will produce the combination of the specified files in the output:

```sh
./zettel-compose.py "~/archive/2345 My index note.markdown"
```

With the above command, the script will simply print the combined notes and quit. You can get a live preview using [Marked 2](https://marked2app.com/) and telling the script to keep watching the files for changes:

```sh
./zettel-compose.py --watch --stream-to-marked "~/archive/2345 My index note.markdown"
```

The "index" note will control the order in which notes will be printed. It is recommended that you include all the relevant notes in the index (but the script will also include others as it finds references while scanning the notes, under certain conditions).

Usually when working with "Zettelkasten" notes, you'll want to make cross references to notes not necessarily intended for "public" consumption. This is why the default behaviour is to only reference and print the contents linked in children notes using a non-standard notation of wiki links prefixed by a section mark (it can usually be type with `⌥6` on the mac, `C-x 8 s` in emacs):

```
This is a reference to § [[1234]].
```

There's also a notation for references that necessarily will never be printed:

```
[[1234]]: This develops some thoughts from a cross-referenced note that should not be printed.
```

Other notations may be used for working with quoting text passages and pandoc citations extracted from bibliographical metadata (see below).

By default, the script will threat every separate note as a "paragraph" (that can also be back-referenced) and number them sequentially (`1.`, `2.`, `3.`). Markdown headings in the beginning of the notes will be accomodated before paragraph numbers, so that you can, e. g., break the output in different chapters.


### Basic parameters

| Parameter                     | Description                          |
| ----------                    | ----------                           |
| `-S`, `--suppress-index`      | Do not print the index note.         |
| `-W`, `--watch`               | Don't quit, watch files for changes. |
| `-M`, `--stream-to-marked`    | Stream to Marked 2.                  |
| `-O`, `--output=` *file name* | Specify *file name* as the output.   |
| `-v`                          | Verbose mode.                        |


### Some tweaks

| Parameter                               | Description                                                                                                          |
| ----------                              | ----------                                                                                                           |
| `--link-all` or `-L`                    | Link and print all wiki linked notes, even if not prefixed by `§`.                                                   |
| `-I`                                    | Only include notes linked from the index note. References in children notes will not be printed.                     |
| `'-H`, `--heading-identifier=` *string* |                                                                                                                      |
| `-s`, `--sleep-time=` *seconds*         | How long to "sleep" between check cycles when watching files. Default is 2 seconds.                                  |
| `-n`, `--no-paragraph-headings`         | Do not print paragraph headings (`1.`, `2.`, `3.` etc.)                                                              |
| `--no-separator`                        | Do not separate notes in the output with an horizontal bar.                                                          |
| `--custom-url=` *string*                | A custom URL prepended to IDs in order to create links inside CriticMarkup comments. Default: `thearchive://match/`. |
| `-C`, `--no-commented-references`       | Disable CriticMarkup comments.                                                                                       |



## Advanced features

### Pandoc citations ###

Notes may have bibliographical metadata in their frontmatter:

```
citekey:	Author1999
loc:		12-45
```

This information can be used elsewhere, creating  pandoc-style citations by making a refence to the notes with `@ [[1234]]` (parenthetical citation), `-@ [[1234]]` (publication year), `@@ [[1233]]` (inline citation).


### Quotes and text fragments ###


You may create a note (`1235`) containing but a quote or fragment of text. You can then quote its actual contents in another note with this:

```
> [[1235]]
```

The quote will receive a sequential numerical identification (`T1`, `T2`, `T3` etc.) and may be later referenced (wiki links will be transformed in `T1`, `T2`, `T3` etc.).

This is very useful if you do translations, as you may elaborate work with them in notes separated from the text where they are to be included (e. g. a paper, lecture notes). You can also create handouts from the very same note (see below).


| Parameter      | Description                  |
| ----------     | ----------                   |
| `-t` *integer* | Set the initial text number. |



### Handouts ###

| Parameter | Description                                 |
| --------- | ----------                                  |
| `-h`      | Handout mode (only quotes will be printed). |
| `-h+`     | Also print section headings.                |


### Parallel texts ###

Bilingual handouts can be created by quoting "left" and "right" parallel texts:

```
> [[1235]] :: [[1236]]
```

When not in handout mode, the "left" text will be printed first, followed by the "right" text (unless this behaviour is modified by `-G`).

Parallel texts are created as a `LaTeX` output, requiring a `\ParallelTexts` macro you should define in your pandoc template (making use of `reledpar` or other package). 

```latex
\ParallelTexts{%
... Left text ...
}{%
... Right text ...
}
```

| Parameter  | Description                                                  |
| ---------  | ----------                                                   |
| `-G` *opt* | Choose which texts(s) to print. *opt* should be `l`,  `r` or `lr` (default). |


