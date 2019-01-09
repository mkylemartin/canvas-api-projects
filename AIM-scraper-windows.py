import json
import os
import re

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import pandas as pd
import time

# you might need to change the path of the chromedriver below
# i've included the chrome driver in the tutorial files
driver = webdriver.Chrome()  # '/usr/chromedriver.exe')

with open('credentials.json') as f_in:
    creds = json.load(f_in)

credentials = {'username': creds['username'],
               'password': creds['password']}

tableau = pd.read_excel('fall_2018_courses_tableau_export.xlsx')

""" ==================================================================
    |                                                                |
    |                                                                |
    |                       SIGN IN TO AIM                           |
    |                                                                |
    |                                                                |
    ================================================================== """

url = 'https://aim.byu.edu'
driver.get(url)

signInXPATH = ('/html[@class=\' js flexbox canvas canvastext webgl no-touch '
               'geolocation postmessage websqldatabase indexeddb hashchange '
               'history draganddrop websockets rgba hsla multiplebgs '
               'backgroundsize borderimage borderradius boxshadow textshadow '
               'opacity cssanimations csscolumns cssgradients cssreflections '
               'csstransforms csstransforms3d csstransitions fontface '
               'generatedcontent video audio localstorage sessionstorage '
               'webworkers applicationcache svg inlinesvg smil '
               'svgclippaths\']/body/div[@id=\'main\']/form[@id='
               '\'duo_form\']/div[@id=\'login\']/iframe[@id=\'duo_iframe\']')

username = driver.find_element_by_name("username")
password = driver.find_element_by_name("password")

username.send_keys(credentials['username'])
password.send_keys(credentials['password'])
password.send_keys(Keys.ENTER)

time.sleep(3)

driver.switch_to.frame('duo_iframe')
driver.find_element_by_class_name('auth-button').send_keys(Keys.ENTER)

# wait to log in
time.sleep(7)

input('press [ENTER] to continue')

searchXPATH = ('/html/body/table[1]/tbody/tr/td/table[1]/'
               'tbody/tr/td[3]/table/tbody/tr/td[2]/input[3]')

search = driver.find_element_by_xpath(searchXPATH)
search.click()

""" ==================================================================
    |                                                                |
    |                                                                |
    |                       OPEN CLS 10                              |
    |                       - get the input fields and stuff         |
    |                                                                |
    ================================================================== """

# throws an error ^
search.send_keys('CLS10')
search.send_keys(Keys.ENTER)

print('waiting')
time.sleep(3)

""" ==================================================================
    |                                                                |
    |                                                                |
    |                       Iterate over courses                     |
    |                                                                |
    |                                                                |
    ================================================================== """


def parser(coursename):
    """ `coursename` should be:
            - C S 142
            - ENGL 300R
            or something in the similar layout. """
    split = re.split(r' (\d+R$)|(\d+)', coursename)
    parsed = [v for v in split if v is not None and len(v) > 0]
    return parsed


def window_checker():
    """ checks to see if other windows are open, if there are it closes them
        and returns False if there are multiple windows meaning that
        the course was not found, and True if everything is good. """
    if len(driver.window_handles) != 1:
        for window in driver.window_handles[1:]:
            driver.switch_to_window(window)
            driver.close()
        return False
    else:
        return True


def select_n_send(course):
    """ pass in the course tuple from pandas, select data, and send keys """
    teachingAreaXPATH = ('//*[@id="Content"]/table/tbody/tr/'
                         'td[2]/table/tbody/tr/td[2]/input[1]')
    catXPATH = ('//*[@id="Content"]/table/tbody/tr/td[2]'
                '/table/tbody/tr/td[2]/input[2]')
    sectionXPATH = ('//*[@id="Content"]/table/tbody/tr/td[2]'
                    '/table/tbody/tr/td[2]/input[6]')

    teachingArea = driver.find_element_by_xpath(teachingAreaXPATH)
    cat = driver.find_element_by_xpath(catXPATH)
    section = driver.find_element_by_xpath(sectionXPATH)

    # get the info from the tableau export
    teachingArea_STR = parser(course.name)[0]
    cat_STR = parser(course.name)[1]
    section_STR = course.section

    # send the info from the tableau to the input boxes
    teachingArea.send_keys(teachingArea_STR)
    cat.send_keys(cat_STR)
    section.send_keys(section_STR)

    # if there's an error... which, there shouldn't be.
    if window_checker() is False:
        print('=' * 78)
        print(f'{course.name}-{course.section} may not be a course... ? ')
        print('=' * 78)
        window_checker()
        pass
    else:
        section.send_keys(Keys.ENTER)
        time.sleep(2)
        # copy the table that has the info and get its innerHTML
        table_xpath = '//*[@id="Content"]/form/table[2]/tbody/tr[3]/td[1]/div'
        teacher_table = driver.find_element_by_xpath(table_xpath)
        tableHTML = teacher_table.get_attribute('innerHTML')

        # `pd.read_html` returns all tables in given HTML, hence df_s_
        dfs = pd.read_html(tableHTML, header=0)

        # The whole table
        df = dfs[0]
        # # just TAs in the table
        # cls_tas = df[df['Type'] == 'TEACHING ASSISTANT']
        # # just a list of TA-BYU Ids
        # CLS_id_list =  list(cls_tas['BYU Id'])
        print('=' * 78)
        print(f'Name: {course.name} Section: {course.section}')
        df['cousre'] = f'{course.name}-{course.section}'
        print(df)
        time.sleep(1)
        # input('press to continue')
        return df


# looping over classes begins here
everything = []
for course in tableau[['name', 'section']].itertuples():

    everything.append(select_n_send(course))


print('finished everything')
result = pd.concat(everything)
result.to_csv('CLS10.csv', index=False)

print('closing last opened window...')
driver.close()
