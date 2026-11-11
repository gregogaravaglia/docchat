docchat is a chatbot you run in the terminal. It answers questions about the files in the folder where you start it, and it talks like a pirate.

to install it, run this command, then make a file called .env that contains the line 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.

```
python -m pip install -e . -r requirements.txt
```

type chat to start. Ask a question, and the bot will look at your files to answer it. You can also run commands yourself without the API key: /ls lists files, /cat shows a file, /grep finds lines that contain a word, /calculate does math, /compact shortens the conversation, and /image adds a picture. For safety, the bot can only open files inside the folder where you started it.

here is the bot looking at my personal website:

```
cd test_projects/lab-homepage
chat
chat> /ls .
IMG_1622.JPG  README.md  about.html  buenosaires.jpeg  destinations.html  iceland.jpeg  index.html  style.css  submission.toml
chat> which pages does this website have and how are they styled?
REPLY_HOMEPAGE
```

I learned that the site has three pages (home, about, and destinations) that all use the same style file.

here is the bot looking at my Markdown compiler:

```
cd test_projects/markdown-compiler
chat
chat> /ls .
README.md  example  markdown_compiler  pyproject.toml  requirements.txt  submission.toml
chat> how are headings converted?
REPLY_MARKDOWN
```

I learned that headings are converted one line at a time, and the number of # signs decides whether it becomes h1, h2, and so on.

here is the bot looking at my eBay scraper:

```
cd test_projects/ebay-scraper
chat
chat> /ls .
README.md  drill press.csv  drill press.json  ebay-dl.py  garden tools.csv  garden tools.json  practice-pages  stuffed animal.csv  stuffed animal.json  submission.toml  test_ebay_dl.py
chat> what fields does ebay-dl.py save for each listing?
REPLY_EBAY
```

I learned that each listing is saved with six fields: name, price, status, shipping, free returns, and items sold.
