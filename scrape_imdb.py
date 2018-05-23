import pandas as pd
import numpy as np
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

def nav_search_imdb(title, year):
    '''
    Using title(str) and year(int) as inputs, navigate to the appropriate IMDB page
    Requires chromedriver to already be initiated
    '''
    # create the search string format used by google and navigate with it
    search_str = 'IMDB+' + '+'.join(title.split(' ')) + '+' + str(year)
    driver.get('https://www.google.com/search?q=' + search_str)
    # generate a random wait time so maybe google will give fewer captchas
    wait_time = random.randint(10,25)
    time.sleep(wait_time)
    # pick the top search result and go to the IMDB page
    link_imdb = driver.find_element_by_id('ires').find_element_by_tag_name('a').get_attribute('href')
    driver.get(link_imdb)

def get_data_imdb(title, year):
    '''
    Using title(str) and year(int) as inputs, scrape some data from IMDB
    '''
    # run search and nav to IMDB URL
    nav_search_imdb(title, year)
    time.sleep(1)

    # film name
    title_block = driver.find_element_by_class_name('title_wrapper')
    title_str = title_block.find_element_by_tag_name('h1').text
    # the title text includes the year so that has to be removed
    try:
        year_str = title_block.find_element_by_tag_name('span').text
        title_imdb = title_str.replace(year_str,'').strip()
    except:
        title_imdb = np.nan
    
    # film year
    try:
        year_imdb = title_block.find_element_by_tag_name('a').text
    except:
        year_imdb = np.nan 
        
    # rating out of 10
    try:
        rating_block = driver.find_element_by_class_name('ratingValue')
        rating_imdb = rating_block.find_element_by_xpath("//span[@itemprop='ratingValue']").text
    except:
        rating_imdb = np.nan
    
    # genre list
    title_subblock = title_block.find_element_by_class_name('subtext')
    genre_list = []
    try:
        genre_grp = title_subblock.find_elements_by_class_name('itemprop')
        for genre in genre_grp:
            genre_list.append(genre.text)
    except:
        genre_list = np.nan
    
    # release date
    try:
        release_imdb = title_subblock.find_element_by_xpath("//a[@title='See more release dates']/meta").get_attribute('content')
    except:
        release_imdb = np.nan
    
    # MPAA rating
    try: 
        mpaa_imdb = title_subblock.find_element_by_xpath("//meta[@itemprop='contentRating']").get_attribute('content')     
    except:
        mpaa_imdb = np.nan
        
    # pull all the details text to find certain data
    details_block = driver.find_element_by_id('titleDetails')
    details_text = details_block.text
    # runtime
    try:
        runtime_str = details_block.find_element_by_xpath("//time[@itemprop='duration']").get_attribute('datetime')
        runtime_imdb = re.sub(r'[PTM]','',runtime_str)
    except:
        runtime_imdb = np.nan
    
    # regex to get some details because element identifiers are not uniquely named
    try:
        # identifies the line from details that has budget info
        budget_str = re.findall(r'Budget[\D]+[\d,]+',details_text)[0]
        # removes the commas and 'Budget: '
        budget_str = re.findall(r'[\d,]+', budget_str)[0].replace(',','')
        # changes the budget to type int from string
        budget_imdb = int(budget_str)
    except:
        budget_imdb = np.nan
        
    # identify the line from details that has production co info and picks the first
    try:
        producer_str = re.findall(r'Production[:\w\s\d]+,?',details_text)[0]
        # cleans the string so it is just the production company name
        producer_imdb = re.findall(r':[\w\s\d]+', producer_str)[0][1:-1].strip()
    except:
        producer_imdb = np.nan

    # identify director information
    director_list = []
    try:
        credit_block = driver.find_elements_by_class_name('credit_summary_item')
        for span_tag in credit_block[0].find_elements_by_class_name('itemprop'):
            director_list.append(span_tag.text)
        director_avg_gross = director_success(director_list, year_imdb)
    except:
        director_avg_gross = np.nan
    
    data_list = [title_imdb, year_imdb, release_imdb, mpaa_imdb, rating_imdb, budget_imdb, runtime_imdb, producer_imdb, genre_list, director_avg_gross]
    return(data_list)

def director_success(director_list, film_year):
    '''
    Using a director list associated with a film and the film year as inputs, 
    returns a calculated average adjusted domestic gross value that represents 
    the average adjusted domestic gross for each director, over the total number of directors
    '''
    tot_avg_gross = 0
    director_count = len(director_list)
    for director in director_list:
        director_str = director.replace(' ','')
        # navigate to director page on box office mojo
        try:
            driver.get('http://www.boxofficemojo.com/people/chart/?view=Director&id='+director_str+'.htm')
            time.sleep(1)
            if driver.current_url == 'http://www.boxofficemojo.com/people/':
                director_count -= 1
            else:
                table_data = pd.read_html(driver.current_url,header=0, parse_dates=True)
                table_index = len(table_data)
                match = 0
                index_counter = 0
                while (match == 0) and (index_counter < table_index):
                    df_dir_gross = table_data[index_counter]
                    try:
                        df_dir_gross['Adjusted Gross']
                        match = 1
                    except:
                        match = 0
                    index_counter += 1
                
                # convert YY to YYYY
                df_dir_gross['Release Date'] = [
                    x[:-2] + '20' + x[-2:] if x[-2:] < '20' 
                    else x[:-2] + '19' + x[-2:] 
                    for x in df_dir_gross['Release']]
                # convert date string to datetime, convert $ to int
                df_dir_gross['Adjusted Gross'] = df_dir_gross['Adjusted Gross'].str.strip('$').str.replace(',','').astype(int)
                df_dir_gross['Date'] = pd.to_datetime(df_dir_gross['Release Date'], format = '%m/%d/%Y', errors='ignore')
                # identify which films were released before the one being investigated
                df_dir_gross['Include'] = [x < datetime.strptime(release_imdb,'%Y-%m-%d') for x in df_dir_gross['Date']]
                # take the average of only the films that were released before
                tot_avg_gross += df_dir_gross[df_dir_gross['Include']==True]['Adjusted Gross'].mean()
        except:
            director_count -= 1
        
        time.sleep(2)

    if director_count > 0:
        avg_gross = round(tot_avg_gross/director_count,2)
    else:
        avg_gross = np.nan

    return(avg_gross)