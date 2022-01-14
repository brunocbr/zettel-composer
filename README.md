# Zettel Composer

A tool for combining notes.

The "index". Linked notes: public and private. The `§` symbol. 

## Basic features

| Parameter                  | Description                          |
| ----------                 | ----------                           |
| `-S`, `--suppress-index`        | Do not print the index note.         |
| `-W`, `--watch`            | Don't quit, watch files for changes. |
| `-M`, `--stream-to-marked` | Stream to Marked 2.                  |
| `-O`, `--output=`          |                                      |
| `-v`                       | Verbose mode.                        |


## Some tweaks

| Parameter                               | Description                                  |
| ----------                              | ----------                                   |
| `--link-all` or `-L`                    |                                              |
| `-I`                                    | Only link from the index note. (deprecated?) |
| `'-H`, `--heading-identifier=` *string* |                                              |
| `-s`, `--sleep-time=`                   |                                              |
| `-n`, `--no-paragraph-headings`         |                                              |
| `--no-separator`                        |                                              |
| `-C`, `--no-commented-references`       |                                              |


## Advanced features

### Pandoc citations ###

Notes may have bibliographical metadata in their frontmatter:

```
citekey:	Author1999
loc:		12-45
```

This information can be used in elsewhere, creating  pandoc-style citations by making a refence to the notes with `@ [[1234]]` (parenthetical citation), `-@ [[1234]]` (publication year), `@@ [[1233]]` (inline citation).


### Quotes and text fragments ###


You may create a note (`1235`) containing but a quote or fragment of text. You can then quote its actual contents in another note with this:

```
> [[1235]]
```

The quote will receive a sequential numbering (`T1`, `T2`, `T3` etc.) and may be later referenced (wiki links will be transformed in `T1`, `T2`, `T3` etc.).

This is very useful if you work translations, as you may elaborate and review quotes or fragments in notes separated from the text where they are to be included (e. g. a paper, lecture notes). You can also create handouts from the very same note (see below).


| Parameter      | Description                  |
| ----------     | ----------                   |
| `-t` *integer* | Set the initial text number. |



### Handouts ###

| Parameter | Description                                 |
| --------- | ----------                                  |
| `-h`      | Handout mode (only quotes will be printed). |
| `-h+`     | Also print section headings.                |


### Paralell texts ###

| Parameter  | Description                  |
| ---------  | ----------                   |
| `-G` *opt* | *opt* should be `l` or  `r`. |

