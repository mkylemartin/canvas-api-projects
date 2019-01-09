""" This script returns a number of select details about all the quizzes
    in a given semester. 

    It is my understanding that these are the semester IDs
    `enrollment_term_id` is the value we will be setting
        - Winter 2018: 49
        - Fall 2018: 50
        - Spring 2018: 51
        - Summer 2018: 52

    etc. You can check this number by looking in Canvas in the URL.
    Select the semester you want and note the value of the
    `enrollment_term_id` variable:
                                               _____________________
    https:// byu.instructure.com/ accounts/31? enrollment_term_id=50
                                               ^^^^^^^^^^^^^^^^^^^^^
"""

import json
import requests as r
import time
import re

import pandas as pd

# Canvas API URL
API_URL = 'https://byu.instructure.com/api/v1'


"""
    CHANGE THE VARIABLES BELOW
"""
Account_ID = 31
# Canvas API Key
API_KEY = input('Paste your api-key here.\n')
"""
    END OF VARIALBES
"""
header = {'Authorization': 'Bearer ' + '%s' % API_KEY}

print('Here are some options for the `enrollment_term_id`: ')
term_id_dict = {'49': ('Winter 2018', 20181),
                '50': ('Fall 2018', 20185),
                '51': ('Spring 2018', 20183),
                '52': ('Summer 2018', 20184)}
print('Canvas Code', 'Name', 'canvas id', sep='\t')
for k, v in term_id_dict.items():
    print(k, v, sep='\t')
print()

term_id = input('enter the `term_id`: ')

print(f'You\'ve selected: {term_id_dict[term_id][0]}')
print()


def get_courses(Account_ID):
    """returns all the courses that are active in a given account.
    If you have more than 150 courses, make sure and set the counter to stop
    after more pages.
    Account_ID `31` is Continuing Education.
    """
    courses = []
    payload = {'enrollment_term_id': f'{term_id}'}
    # 'with_enrollments': 'True',
    # 'published': 'True',
    # 'completed': 'False',
    # 'hide_enrollmentless_courses': 'True',
    # 'state[]': 'available',

    page_no = 1
    loop_control = True

    while loop_control:
        request = r.get(API_URL +
                        '/accounts/' +
                        str(Account_ID) +
                        '/courses?per_page=100&page=' +
                        str(page_no),
                        params=payload, headers=header)
        response = request.json()

        courses.append(response)
        page_no += 1
        if page_no == 5:
            loop_control = False
    return courses


def get_quizzes(id_num, name):
    """ takes course_id, and name then all canvas modules associated with the
        given course_id. """
    payload = {'enrollment_term_id': f'{term_id}'}
    page_no = 1
    data = {'name': name,
            'id_num': id_num,
            'paged_results': []}

    loop_control = True
    while loop_control:
        request = r.get(API_URL +
                        f'/courses/{id_num}/quizzes?include[]=items' +
                        f'&page={page_no}',
                        params=payload, headers=header)
        json_request = request.json()
        # print(len(json_request), type(json_request))
        if len(json_request) != 0:
            page_no += 1
            data['paged_results'].append(json_request)
        else:
            loop_control = False

    return data


# Get a list of all the courses
print('Getting all courses...')
all_courses = get_courses(31)
print('Got all courses, and course ids...')
print()
c_course_ids = []

for page in all_courses:
    for course in page:
        c_course_ids.append((course['id'], course['name']))

print(f'There are: {len(c_course_ids)} courses to look up.')

counter = 1
course_data = []
total = len(c_course_ids)
for id, name in c_course_ids:
    print(f'{counter}. ', f'({round(counter / total, 2):.0%})', id, name)
    course_data.append(get_quizzes(id, name))
    # Sleep to be nice with the API
    time.sleep(1)
    counter += 1

print('Iterating over Quizzes')


def quiz_dict_constructor(quiz, course, linky_link):
    """ Takes xyz and returns a dictionary of quiz details to be appended to
        the big dataframe which is called `all_quizzes` """
    description = str(re.sub(r'<.*?>', '', str(quiz['description'])))
    try:
        due = quiz['all_dates'][0]['due_at']
        unlock = quiz['all_dates'][0]['unlock_at']
        lock = quiz['all_dates'][0]['lock_at']
    except (IndexError, KeyError):
        print(f'{course["name"]}, doesn\'t have complete data.')
        due = 0
        unlock = 0
        lock = 0

    d = {'course': course['name'],
         'course_link': linky_link,
         'due_at': due,
         'unlock_at': unlock,
         'lock_at': lock,
         'access_code': quiz['access_code'],
         'time_limit': quiz['time_limit'],
         'title': quiz['title'],
         'description': description,
         'points_possible': quiz['points_possible']}

    return d


all_quizzes = pd.DataFrame()
for course in course_data:
    linky_link = (f'https://byu.instructure.com/courses/'
                  f'{course["id_num"]}/quizzes')
    for page in course['paged_results']:
        for quiz in page:
            quiz_dict = quiz_dict_constructor(quiz, course, linky_link)
            all_quizzes = all_quizzes.append(quiz_dict, ignore_index=True)
    print(f'Added {course["name"]}')
print('Creating .csv')
file_name = f'{term_id_dict[term_id][0]}-canvas-quiz-export.csv'
all_quizzes.to_csv(file_name, encoding='utf-8', index=False)
print('.csv created')
