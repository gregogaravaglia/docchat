# DocChat

DocChat is a chatbot you run in the terminal. It answers questions about the files in the folder where you start it, and it talks like a pirate.

To install it, run this command, then make a file called .env that contains the line GROQ_API_KEY=your-key-here.

```
python -m pip install -e . -r requirements.txt
```

Type chat to start. Ask a question, and the bot will look at your files to answer it. You can also run commands yourself without the API key: /ls lists files, /cat shows a file, /grep finds lines that contain a word, /calculate does math, /compact shortens the conversation, and /image adds a picture. For safety, the bot can only open files inside the folder where you started it.

Here is the bot looking at my personal website:

```
cd test_projects/lab-homepage
chat
chat> /ls .
IMG_1622.JPG  README.md  about.html  buenosaires.jpeg  destinations.html  iceland.jpeg  index.html  style.css  submission.toml
chat> which pages does this website have and how are they styled?
Arrr, the site be a modest trio of pages – the home page “index.html”, a “about.html”, and a “destinations.html”. All three use the same “style.css” to keep the look steady. The CSS sets a light‑gray background with Arial text, a dark nav bar with white links that turn a blue‑ish shade on hover, and big 40‑pixel h1 titles. The page content sits in white boxes with rounded corners, while images stretch to 100% of their container and tables get a simple border and padding. A media query tweaks the font size and stacks the nav links on tiny screens. Ye’re good to sail!
```

I learned that the site has three pages (home, about, and destinations) that all use the same style file.

Here is the bot looking at my Markdown compiler:

```
cd test_projects/markdown-compiler
chat
chat> /ls .
README.md  example  markdown_compiler  pyproject.toml  requirements.txt  submission.toml
chat> how are headings converted?
Headings are turned by the `compile_headers` routine. It walks the line from the start, counting how many `#` characters come in a row. If that count is 1‑6 and the next character is a space, it chops off the `#`s and the space, then wraps the rest of the line in `<h{count}>…</h{count}>`. Anything that doesn’t match that pattern is left untouched, so a line that starts with spaces before a `#` stays plain. Arr!
```

I learned that headings are converted one line at a time, and the number of # signs decides whether it becomes h1, h2, and so on.

Here is the bot looking at my eBay scraper:

```
cd test_projects/ebay-scraper
chat
chat> /ls .
README.md  drill press.csv  drill press.json  ebay-dl.py  garden tools.csv  garden tools.json  practice-pages  stuffed animal.csv  stuffed animal.json  submission.toml  test_ebay_dl.py
chat> what fields does ebay-dl.py save for each listing?
Arr, the script keeps a tidy booty of six pieces per listing: the name, the price in cents, the status, the shipping cost (also in cents), a Boolean for free returns, and the number of items sold. These six fields make up the JSON or CSV record for each eBay find.
```

I learned that each listing is saved with six fields: name, price, status, shipping, free returns, and items sold.
