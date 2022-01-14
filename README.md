# Zettel Composer

This is a tool for combining notes in a "Zettelkasten" system.

## Basic features

The script takes as its argument the name of a file which will be used as an `index` note. Wiki links prepended with a section sign (`§ [[1234]]`) in the index will produce the combination of the specified notes in the output:

```sh
./zettel-compose.py "~/archive/2345 My index note.markdown"
```

With the above command, the script will simply print the combined notes and quit. You can though get a live preview using [Marked 2](https://marked2app.com/) and telling the script to keep watching the files for changes:

```sh
./zettel-compose.py --watch --stream-to-marked "~/archive/2345 My index note.markdown"
```

The `index` note will control the order in which notes will be printed. It is recommended that you include all the relevant notes in the index (but the script will also include others as it finds references while scanning the notes).

Usually when working with "Zettelkasten" notes, you'll want to make cross references to notes not necessarily intended for "public" consumption. This is why the default behaviour is to only reference and print notes using a non-standard notation of wiki links prefixed by the section mark (this character can usually be typed with `⌥ 6` on the mac, `C-x 8 S` in emacs):

```
This is a reference to § [[1234]].
```

You can override the default behaviour with the `--link-all` option if you don't want to print notes referenced with "standard" wiki links.

There's also a notation for references that necessarily will not be printed, even with the above option. It consists in a wiki link at the very beginning of a line, followed by a colon:

```
[[1234]]: This develops some thoughts from a cross-referenced note that should never be printed.
```

Other special notations are available for working with quotes and pandoc citations (see below).

By default, the script will threat every separate note as a "section" or "paragraph" and number them sequentially (`1.`, `2.`, `3.`). They can always be cross referenced with the `§ [[1234]]` notation (which yields `(§1)`, `(§2)`, `(§3)` etc. in the output).

Markdown headings in the beginning of the notes will be accomodated before the paragraph numbers, so that you can, e. g., break the output in different chapters and sections. You can also suppress paragraph headings by calling the script with the `-n` option.

### Basic parameters

| Parameter                     | Description                          |
| ----------                    | ----------                           |
| `-S`, `--suppress-index`      | Do not print the `index` note.       |
| `-W`, `--watch`               | Don't quit, watch files for changes. |
| `-M`, `--stream-to-marked`    | Stream to Marked 2.                  |
| `-O`, `--output=` *file name* | Specify *file name* as the output.   |
| `-v`                          | Verbose mode.                        |


### Some tweaks

| Parameter                               | Description                                                                                                          |
| ----------                              | ----------                                                                                                           |
| `--link-all` or `-L`                    | Link and print all wiki linked notes, even if not prefixed by `§`.                                                   |
| `-I`                                    | Only include notes linked from the `index` note. References in children notes will not be printed. (deprecated)      |
| `-H`, `--heading-identifier=` *string*  |                                                                                                                      |
| `-s`, `--sleep-time=` *seconds*         | How long to "sleep" between file watching cycles. Default is 2 seconds.                                              |
| `-n`, `--no-paragraph-headings`         | Do not print paragraph headings (`1.`, `2.`, `3.` etc.)                                                              |
| `--no-separator`                        | Do not separate notes in the output with a horizontal bar.                                                           |
| `--custom-url=` *string*                | A custom URL prepended to IDs in order to create links inside the CriticMarkup comments. Default: `thearchive://match/`. |
| `-C`, `--no-commented-references`       | Disable CriticMarkup comments.                                                                                       |



## Advanced features
### Quotes and text fragments ###


You may create a note (`1235` in this example) containing but a quote or fragment of text. You can then quote its actual contents inside another note in a line like this:

```
> [[1235]]
```

The quote will receive a sequential numerical identification (`T1`, `T2`, `T3` etc.) and may be later referenced (wiki links will be transformed in `T1`, `T2`, `T3` etc.).

This is very useful if you do translations, as you may work with them in notes separated from the text where they are to be included (e. g. a paper, lecture notes). You can also create handouts from the very same note (see below).

But if you just want to insert the contents of the body of a  note[^1], without any special handling, you can use the following:

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
| `-h +`    | Also print section headings.                |


### Parallel texts ###

Bilingual handouts can be created by inserting "left" and "right" parallel texts:

```
> [[1235]] :: [[1236]]
```

When not in handout mode, the "left" text will be printed first, followed by the "right" text (unless this behaviour is modified by `-G`).

Parallel texts are rendered in `LaTeX` output (via `pandoc`), requiring a `\ParallelTexts` macro you should define in your pandoc template (making use of `reledpar` or other package). 

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


[^1]: I speak of the "body" of a note because the script will recognize a YAML frontmatter and discard it.
### Pandoc citations ###

Notes may have bibliographical metadata in their frontmatter:

```
---
citekey:	Author1999
loc:		12-45
...
```

This information can be used elsewhere, creating  pandoc-style citations by making a refence to the notes with `@ [[1234]]` (parenthetical citation), `-@ [[1234]]` (publication year), `@@ [[1233]]` (inline citation).


