import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import string
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os
import datetime
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
import random

chromedriver = "/chromedriver"
os.environ["webdriver.chrome.driver"] = chromedriver
driver = webdriver.Chrome(chromedriver)

def get_data_author(title,year):
    '''
    Using film title(str) and film release year(int) as inputs, 
    find the book author and return in a list of [book title, book author]
    '''
    search_str = '+'.join(title.split(' '))
    driver.get('https://en.wikipedia.org/w/index.php?search=' + search_str + '+film+' + str(year))
    time.sleep(1)
    try:
        wiki_result = driver.find_element_by_class_name('mw-search-result-heading')
        wiki_url = wiki_result.find_element_by_tag_name('a').get_attribute('href')
        driver.get(wiki_url)
        time.sleep(1)
        page_soup = BeautifulSoup(driver.page_source, 'lxml')
        book_info = page_soup.find('th', text='Based on').find_parent()
        book_text = book_info.find_all('i')[0].find_parent().text
        book_title = book_text.split("\n")[0]
        author_str = book_text.split("\n")[1]
        book_author = re.sub(r'["by"]*[:]*','',author_str).strip()
        data_list = [book_title,book_author]
    except:
        data_list = [np.nan,np.nan]
    return(data_list)