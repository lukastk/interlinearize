#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.4.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

from googletrans import Translator
import math
from threading import Thread
from queue import Queue
import time
import string
import subprocess
from pathlib import Path
import os
from bs4 import BeautifulSoup, Tag, NavigableString
import tempfile
import configparser
import nltk
from nltk.tokenize import word_tokenize
import pickle
import sys
import csv

# ## Functions

default_config ="""
[requests]
service_URL_country_codes = be,ca,dk,fi,fr,de,gr,hk,it,jp,no,sk,si,se,ch,es,com,co.uk
words_per_request = 1

[translation]
ignorable_punctuation_tokens = !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~«»‘’”“–

[formatting]
exclude_spaces = False
class_translation = il_translation
class_word = il_word
class_paragraph = il_paragraph
class_space = il_space

[misc]
default_editor = gedit
"""

default_interlinear_css ="""

.il_paragraph {
    width: 100%;
    overflow-wrap: anywhere;
    font-size: 1.7em !important;
    text-indent: 1.3em !important;
}

.il_word {
    font-size: 1em;
    position: relative;
    display: inline-block;
    padding-left: 0px;
    padding-right: 0px;
    text-align: center;
    overflow-wrap: normal;
    height: 60px;
}

.il_word:first-child {
    padding-left: 0px;
}

.il_word:last-child {
    padding-right: 0px;
}

.il_translation {
    width: 100%;
    position: absolute;
    top: 30px;
    left: 0;
    font-size: 0.6em;
    text-align: center;
    color: #999;

    -webkit-user-select: none;  
    -moz-user-select: none;    
    -ms-user-select: none;      
    user-select: none;
    /* line-height: 0; */
    overflow-wrap: normal;
}

.not-word, .missing-translation {
    padding-left: 0;
    padding-right: 0;
}
"""


# +
def get_config(get_path = False):
    # First check in the current directory 
    config_path = Path(".", 'interlinearize.config')
    if not config_path.is_file():
        # Otherwise check in the app settings directory
        config_path = Path(settings_path, 'interlinearize.config')
        
        # And if that doesn't work, create a new config file in the app settings directory
        if not config_path.is_file():
            Path(settings_path).mkdir(parents=True, exist_ok=True)

            with open(str(config_path), "w") as f:
                f.write(default_config)
    
    config = configparser.RawConfigParser()
    config.read(str(config_path))

    if not get_path:
        return config
    else:
        return str(config_path), config

def load_word_dict(src, dest, get_path=False):
    # First check in the current directory
    word_dict_folder_path = Path(".", 'dicts')
    
    if not word_dict_folder_path.is_dir():
        # Otherwise check in the app settings directory
        word_dict_folder_path = Path(settings_path, 'dicts')
        
    if word_dict_folder_path.is_dir():
        
        # Check if src_dest.txt is there
        word_dict_path = Path(word_dict_folder_path, "%s_%s.txt" % (src,dest))
        
        if word_dict_path.is_file():
            with open(str(word_dict_path), "r") as csv_file:
                csv_r = csv.reader(csv_file, delimiter='\t')
                word_dict = {}

                for src_w, dest_w in csv_r:
                    word_dict[src_w] = dest_w
                    
                ret = str(word_dict_folder_path), word_dict
        else:
            ret = str(word_dict_folder_path), {}
    else:
        ret = str(word_dict_folder_path), {}

    if get_path:
        return ret
    else:
        return ret[1]
    
def save_word_dict(src, dest, word_dict):
    word_dict_folder_path, _ = load_word_dict(src, dest, get_path=True)
    Path(word_dict_folder_path).mkdir(parents=True, exist_ok=True)
    
    word_dict_path = Path(word_dict_folder_path, "%s_%s.txt" % (src, dest))

    src_words = list(word_dict.keys())
    dest_words = [word_dict[w] for w in src_words]

    with open(str(word_dict_path), "w") as csv_file:
        csv_w = csv.writer(csv_file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for src_w, dest_w in zip(src_words, dest_words):
            csv_w.writerow([src_w, dest_w])
    
def get_interlinear_css(get_path=False):
    # First check in the current directory 
    css_path = Path(".", 'interlinear.css')
    if not css_path.is_file():
        # Otherwise check in the app settings directory
        css_path = Path(settings_path, 'interlinear.css')
        
        # And if that doesn't work, create a new config file in the app settings directory
        if not css_path.is_file():
            Path(settings_path).mkdir(parents=True, exist_ok=True)

            with open(str(css_path), "w") as f:
                f.write(default_interlinear_css)
    
    with open(str(css_path), "r") as f:
        css = f.read()
    
    if get_path:
        return str(css_path), css
    else:
        return css

def convert_book_to_HTML(book_path):
    """Takes any file supported by ebook-convert, and converts it into an HTML file and returns it."""
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_dir_path = tmp_dir.name

    book_title = Path(book_path).stem
    htmlz_title = book_title + ".htmlz"

    # Convert
    process = subprocess.Popen(['ebook-convert', book_path, os.path.join(tmp_dir_path, htmlz_title) ],
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stderr:
        er_msg = "Error from ebook-convert when converting the input. Error message:\n\n\t" + stderr.decode("utf-8")
        raise Exception(er_msg)

    # Create folder for unzip
    process = subprocess.Popen(['mkdir', os.path.join(tmp_dir_path, book_title)],
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stderr:
        er_msg = "Error:\n\n\t" + stderr.decode("utf-8")
        raise Exception(er_msg)

    # Unzip
    process = subprocess.Popen(['unzip', os.path.join(tmp_dir_path, htmlz_title), "-d", os.path.join(tmp_dir_path, book_title)],
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if stderr:
        er_msg = "Error:\n\n\t" + stderr.decode("utf-8")
        raise Exception(er_msg)

    book_html_path = os.path.join(tmp_dir_path, book_title, "index.html")
    page = open(book_html_path)
    soup = BeautifulSoup(page.read(), "html.parser")
    #tmp_dir.cleanup()
    return tmp_dir, soup
    
def get_word_list(text, ignorable_punctuation_tokens):
    """Gets a list of unique words in the given text, using
    the NLTK tokenizer."""
    words = word_tokenize(text, language='french')
    words = list(set([w.lower() for w in words]))
    new_words = []
    
    for w in words:
        if w.isnumeric():
            continue
        if len(set(w) - ignorable_punctuation_tokens) == 0: # Check if word is just punctuation
            continue
            
        new_words.append(w)
    return new_words

def lookup_word(word_dict, word, ignorable_punctuation_tokens):
    """Given a word dictionary, return the word's translation.
    Using `ignorable_punctuation_tokens`, any prefixed or affixed
    punctuation is removed.
    
    Error codes:
    0 - Not a word (just numbers, or punctuation)
    1 - Missing translation"""
    w_tok = word_tokenize(word, language='french')
    
    w = None
    
    for _w in w_tok:
        if _w.isnumeric():
            continue
        if len(set(_w) - ignorable_punctuation_tokens) == 0:
            continue
        w = _w.lower()
        
    if not w is None:
        if w in word_dict:
            return word_dict[w]
        else:
            return 1
    else:
        return 0
    
def construct_word_list_from_text(words, word_dict, src, dest, service_urls, words_per_request):
    """Adds entries to the word_dict by translating the words in the given text.
    The function uses googletrans.Translator to get the translations of each words.
    `service_urls` is a list of URLs that the requests are divided over."""
    
    # Remove words that are already in word_dict
    
    words_already_found = set(word_dict.keys())
    words = list( set(words) - words_already_found )
    
    # Translate!

    words_per_thread = int(len(words) / len(service_urls))

    thread_word_list = []
    for i in range(len(service_urls)):
        if i != len(service_urls) - 1:
            thread_word_list.append( words[ i*words_per_thread: (i+1)*words_per_thread ] )
        else:
            thread_word_list.append( words[ i*words_per_thread : ] )

    def translate_words(words, src, dest, words_per_request, service_url, que):
        t1 = time.time()
        translations = {}

        translator = Translator(service_urls=[service_url])

        for i in range( math.ceil(len(words) / words_per_request) ):
            if (i+1)*words_per_request <= len(words):
                words_to_translate = words[ i*words_per_request : (i+1)*words_per_request ]
            else:
                words_to_translate = words[ i*words_per_request :  ]

            ts = translator.translate(words_to_translate, src=src, dest=dest)

            for translation in ts:
                translations[translation.origin] = translation.text.lower()

        que.put(translations)
        t2 = time.time()


    que = Queue()

    que_times = Queue()

    threads = []
    for thread_words, service_url in zip(thread_word_list, service_urls):
        thread = Thread(target=translate_words, args=( thread_words, src, dest, words_per_request, service_url, que ))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
        
    for i in range(len(threads)):
        t_dict = que.get()
        word_dict.update(t_dict)


# -

def add_subtitle_to_text(text, word_dict, class_translation, class_word, class_paragraph, class_space):
    word_list = str(text).split()
    tag_list = []

    for w in word_list:
        w_translated = lookup_word(word_dict, w, ignorable_punctuation_tokens)
        trans_status = ""
        word_status = ""

        if w_translated == 0:
            trans_status = "not-word"
            word_status = "not-word"
            w_translated = ""
        elif w_translated == 1:
            trans_status = "missing-translation"
            word_status = "missing-translation"
            w_translated = ""
        
        word_span = Tag(builder=book_soup.builder,  name='div', attrs={'class':class_word + " " + word_status})
        trans_div = Tag(builder=book_soup.builder,  name='div', attrs={'class':class_translation + " " + trans_status})
        trans_div.insert(0, w_translated)
        word_span.insert(0, trans_div)
        word_span.insert(0, w)    
        tag_list.append(word_span)
    
        if not exclude_spaces:
            space_tag = Tag(builder=book_soup.builder,  name='div', attrs={'class':class_space})
            space_tag.insert(0, "&nbsp;")
            tag_list.append(NavigableString(" "))
        
    if len(word_list) > 0:
        word_list = word_list[:-1] # Remove last space
    
    return tag_list


def add_subtitle_to_soup(book_soup, word_dict, class_translation, class_word, class_paragraph, class_space):
    for paragraph in book_soup.find_all("p"):

        new_paragraph_contents = []

        for i in range(len(paragraph)):
            elem = paragraph.contents[i]

            # Convert text directly in <p>
            if type(elem) == NavigableString:
                tag_list = add_subtitle_to_text(elem, word_dict, class_translation, class_word, class_paragraph, class_space)
                new_paragraph_contents.append(tag_list)
            elif type(elem) == Tag and elem.name == 'span':
                tag_list = add_subtitle_to_text(elem.text, word_dict, class_translation, class_word, class_paragraph, class_space)
                # Replace contents inside span with the subtitled content
                elem.clear()
                for t in tag_list:
                    elem.insert( len(elem.contents), t )
                #new_paragraph_contents.append([elem])
                new_paragraph_contents.append(tag_list)
            else:
                new_paragraph_contents.append([elem])
                continue

        paragraph.name = "div"
        paragraph['class'] = paragraph.get('class', '') + [class_paragraph]
        paragraph.clear()

        for elem_l in new_paragraph_contents:
            for elem in elem_l:
                paragraph.insert( len(paragraph.contents), elem )

    book_soup.find('head').insert(0, Tag(builder=book_soup.builder,  name='link', attrs={'rel':'stylesheet', 'href' : 'interlinear.css'}))


def write_translation(book_soup, tmp, book_path, out_path):
    ## Overwrite the original index.html of the book

    tmp_dir_path = tmp_dir.name
    book_title = Path(book_path).stem

    book_path = os.path.join(tmp_dir_path, book_title)
    book_html_path = os.path.join(tmp_dir_path, book_title, "index.html")

    with open(book_html_path, "w") as f:
        f.write(str(book_soup))

    ## Copy the interlinear.css file to the folder

    with open(os.path.join(book_path, "interlinear.css"), "w") as f:
        f.write(get_interlinear_css())

    ## Convert index.html to the desired output
    
    # If the output format is not specified, then the output will just be the copied folder
    
    if Path(out_path).suffix == "":
        process = subprocess.Popen(['cp', '-r', book_path, out_path ],
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

    
    # else, use calibre
    
    else:
        # ebook-convert doesn't deal with ~ properly, so we convert it
        if out_path[:2] == '~/':
            out_path = str(Path( Path.home(), out_path[2:] ))

        process = subprocess.Popen(['ebook-convert', book_html_path, out_path ],
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if stderr:
            er_msg = "Error from ebook-convert. Error message:\n\n\t" + stderr.decode("utf-8")
            raise Exception(er_msg)

    tmp_dir.cleanup()

# ## Code

settings_path = str(Path(Path.home(), '.interlinearize'))


# +
def is_interactive():
    import __main__ as main
    return not hasattr(main, '__file__')

if is_interactive():
    src_lan = "fr"
    dest_lan = "en"
    book_path = "examples/original/Candide - Voltaire.epub"
    out_path = "examples/interlinearized/Candide - Voltaire (interlinearized).epub"
else:

    # Commands
    if sys.argv[1] == "-c":
        cmd = sys.argv[2]

        config_path, config = get_config(get_path=True)
        css_path, _ = get_interlinear_css(get_path=True)
        word_dict_path, _ = word_dict = load_word_dict("", "", get_path=True)
        default_editor = config['misc']['default_editor']

        if cmd == "config":
            os.system(default_editor + " " + str(config_path))

        elif cmd == "css":
            os.system(default_editor + " " + str(css_path))

        elif cmd == "dict":
            src = sys.argv[3]
            dest = sys.argv[4]
            os.system(default_editor + " " + str(Path( word_dict_path, "%s_%s.txt" % (src, dest) )))

        elif cmd == "clear":
            clear_item = sys.argv[3]
            if clear_item == "config" or clear_item == "all":
                os.remove(str(config_path))
            elif clear_item == "css" or clear_item == "all":
                os.remove(str(css_path))

        elif cmd == "cleardict":
            src = sys.argv[3]
            dest = sys.argv[4]
            word_dict_path, _ = load_word_dict(src, dest, get_path=True)

            os.remove(Path( word_dict_path, "%s_%s.txt" % (src, dest) ))

        sys.exit(0)

    # Interlinearize
    else:
        src_lan, dest_lan, book_path, out_path = sys.argv[1:5]
# -

# Check if book exists

if not Path(book_path).is_file():
    print("'%s' cannot be found." % book_path)
    sys.exit(0)

# Load config file

# +
config = get_config()

## requests

country_codes = config['requests']['service_URL_country_codes'].split(",")
service_urls = []
for co in country_codes:
    service_urls.append( "translate.google.%s" % co )
    
words_per_request = int( config['requests']['words_per_request'] )

## translation

ignorable_punctuation_tokens = set(config['translation']['ignorable_punctuation_tokens'])

## formatting

exclude_spaces = config['formatting']['exclude_spaces'] == "True"
class_translation = config['formatting']['class_translation']
class_word = config['formatting']['class_word']
class_paragraph = config['formatting']['class_paragraph']
class_space = config['formatting']['class_space']
# -

# Translate

# +
print("Converting book to HTMLZ")
tmp_dir, book_soup = convert_book_to_HTML(book_path)

word_dict = load_word_dict(src_lan, dest_lan)

word_list = get_word_list(book_soup.text, ignorable_punctuation_tokens)

print("Finding translations of new words")
construct_word_list_from_text(word_list, word_dict, src_lan, dest_lan, service_urls, words_per_request)

save_word_dict(src_lan, dest_lan, word_dict)
# -

# Construct translated book

# +
print("Constructing interlinearized version")

add_subtitle_to_soup(book_soup, word_dict, class_translation, class_word, class_paragraph, class_space)

write_translation(book_soup, tmp_dir, book_path, out_path)
