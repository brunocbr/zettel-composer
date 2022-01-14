# Zettel Composer

A tool for combining notes.

The "index". Linked notes: public and private. The `§` symbol. 

## Basic features

| Parameter                  | Description                          |
| ----------                 | ----------                           |
| '-S', '--suppress-index'   | Do not print the index note.         |
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

### Quotes and text fragments ###

| Parameter      | Description                  |
| ----------     | ----------                   |
| `-t` *integer* | Set the initial text number. |



### Handouts ###

| Parameter | Description                            |
| --------- | ----------                             |
| `-h+`     | Print section headings in the handout. |
| `-h`      | Handout mode (print only quotes).      |


### Paralell texts ###

| Parameter  | Description                  |
| ---------  | ----------                   |
| `-G` *opt* | *opt* should be `l` or  `r`. |

