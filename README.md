# DocChat: a pirate that reads your files

DocChat is a command-line chatbot that answers questions about the files in whatever folder you start it in. It can list, read, and search files and do arithmetic, either automatically when the model asks for a tool or directly through slash commands like `/ls`.

## Install

```
python -m pip install -e . -r requirements.txt
```

Put your Groq API key in a `.env` file (`GROQ_API_KEY=...`) in the folder where you run `chat`, or export it in your shell. Slash commands work without a key.

## Usage

```
chat                     # interactive session
chat "what is in here?"  # send one message, print the reply, and exit
chat --debug             # print every tool the model calls
```

Inside a session:

| Command | What it does |
| --- | --- |
| `/ls [path]` | list the files in a folder |
| `/cat path` | print a text file |
| `/grep regex path` | print matching lines from files matching a glob |
| `/calculate expression` | evaluate arithmetic |
| `/compact` | replace the history with a five-line summary |
| `/image path` | attach a PNG for a vision model |

Every file tool refuses absolute paths and paths containing `..`, so the model can only see files inside the folder where `chat` was started.

## Examples

### Personal website

```
cd test_projects/lab-homepage
chat
chat> /ls .
IMG_1622.JPG  README.md  about.html  buenosaires.jpeg  destinations.html  iceland.jpeg  index.html  style.css  submission.toml
chat> which pages does this website have and how are they styled?
REPLY_HOMEPAGE
```

The site is three linked pages (home, about, and destinations) that all share one `style.css`, which uses `:hover` colors on the navigation links.

### Markdown compiler

```
cd test_projects/markdown-compiler
chat
chat> /ls .
README.md  example  markdown_compiler  pyproject.toml  requirements.txt  submission.toml
chat> how are headings converted?
REPLY_MARKDOWN
```

Headings are handled one line at a time in `markdown_compiler/util/line_functions.py`, where `compile_headers` counts the leading `#` characters (one to six, followed by a space) to pick the `<h1>`–`<h6>` tag, while paragraphs and code blocks need the whole document in `compile_lines`.

### eBay scraper

```
cd test_projects/ebay-scraper
chat
chat> /ls .
README.md  drill press.csv  drill press.json  ebay-dl.py  garden tools.csv  garden tools.json  practice-pages  stuffed animal.csv  stuffed animal.json  submission.toml  test_ebay_dl.py
chat> what fields does ebay-dl.py save for each listing?
REPLY_EBAY
```

Each listing is saved with six fields (name, price, status, shipping, free returns, and items sold), and prices and shipping are stored as whole cents instead of dollar strings.

## Development

```
python -m pytest --doctest-modules tools chat.py
python -m coverage run --source=tools -m pytest --doctest-modules tools
python -m coverage report -m
python -m flake8 chat.py tools --ignore=E501
```

After cloning, run `git submodule update --init --recursive` to download the example projects in `test_projects/`.
