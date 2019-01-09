""" This script checks if a given survey is in all of the courses in a given
    semester.

    To run this script you will need:
    - a canvas API KEY
    - the qualtrics Survey ID (part of the URL that's like
                               `SV_aYwrUf4n5znh3X7`)
    - The term ID
    - The `Account_ID` (which is always 31, the DCE sub-account)
    - the `enrollment_term_id` which is canvas' way of saying 20185, 20191
        - the `enrollment_term_id` is in the URL when you search for a course
          in Canvas (as is the account_id)

    Here are the main Survey IDs:
    - Learner Readiness Survey  `SV_9Mr45KbxLqfcJdb`
    - Mid-Course survey         `SV_1AN0abATTLYgzel`
    - End of Course Survey      `SV_aYwrUf4n5znh3X7`

    The following comment is for reference, but will need to be updated in
    future semesters:

    This script has two parts (takes about 5 minutes):
    1. Get all the courses
    2. Search all the courses

    It is my understanding that these are the semester IDs
    `enrollment_term_id` is the value we will be setting
        - Winter 2018: 49
        - Fall 2018: 50
        - Spring 2018: 51
        - Summer 2018: 52

"""

import json
import requests as r
import time
import re

from fuzzywuzzy import fuzz

API_URL = 'https://byu.instructure.com/api/v1'
Account_ID = 31
term_id = '50'
API_KEY = input('Enter the Canvas API key below and type [ENTER]:\n')

header = {'Authorization': 'Bearer ' + '%s' % API_KEY}

qualtrics_survey_id = input('Enter the Qualtrics Survey ID below and '
                            'type [ENTER]:\n')
m_name = input('Enter the name of the module you are searching for '
               '`Mid-Course Survey`, `End of Course Survey` or '
               '`Learner Readiness Survey` and press [ENTER]\n')


print('Here are some options for the `enrollment_term_id`: ')
term_id_dict = {'49': ('Winter 2018', 20181),
                '50': ('Fall 2018', 20185),
                '51': ('Spring 2018', 20183),
                '52': ('Summer 2018', 20184)}
print('AIM Code', 'Name', 'canvas id', sep='\t')
for k, v in term_id_dict.items():
    print(k, v, sep='\t')
print()

term_id = input('enter the `term_id`: ')

print(f'You\'ve selected: {term_id_dict[term_id][0]}')
print('Getting all courses...')


def get_courses(Account_ID):
    """returns all the courses that are active in a given account.
    If you have more than 150 courses, make sure and set the counter to stop
    after more pages.
    Account_ID `31` is Continuing Education.
    """
    courses = []
    # optional paramters that can be useful
    payload = {'enrollment_term_id': f'{term_id}'}
    """
    'with_enrollments': 'True',
    'published': 'True',
    'completed': 'False',
    'hide_enrollmentless_courses': 'True',
    'state[]': 'available'}
    """

    page_no = 1
    loop_control = True
    while loop_control is True:
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


def get_modules(id_num, name):
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
                        f'/courses/{id_num}/modules?include[]=items'
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
all_courses = get_courses(31)
c_course_ids = []

for page in all_courses:
    for course in page:
        c_course_ids.append((course['id'], course['name']))

print('len(c_course_ids)', len(c_course_ids))
print('Got all courses, and course ids...')

counter = 1
course_data = []
total = len(c_course_ids)
for cid, name in c_course_ids:
    print(f'{counter}. ', f'({round(counter / total, 2)})', cid, name)

    course_data.append(get_modules(id, name))

    # Sleep to be nice with the API
    time.sleep(1)
    counter += 1

# This next block of code should be rewritten to handle all the module types
print('Iterating over results to find end of course surveys')

close_name = []
add_survey = []
wrong_type = []

for course in course_data:
    linky_link = (f'https://byu.instructure.com/courses/'
                  f'{course["id_num"]}/modules')
    good_match = False
    item_count = 0
    for page in course['paged_results']:
        for module in page:
            mod = dict(module)
            for item in mod['items']:
                item_count += 1
                # m_name = 'End of Course Survey'
                score = fuzz.token_sort_ratio(item['title'], m_name)
                try:
                    if score in range(60, 95):
                        # possible match, print thing
                        close_name.append(f'Fuzzy name: {item["title"]}, '
                                          f'{item["type"]}, {linky_link}')
                        print('close name')
                        good_match = True
                    elif score in range(95, 101):
                        # go look at the content of that page.
                        if item['type'] == 'Page':
                            payload = {'enrollment_term_id': f'{term_id}'}
                            request = r.get(item['url'],
                                            params=payload,
                                            headers=header)
                            json_request = request.json()
                            time.sleep(1)
                            has_lrs = re.findall(qualtrics_survey_id,
                                                 json_request['body'])
                            if len(has_lrs) == 0:
                                add_survey.append((f'Change survey in '
                                                   f'{course["name"]}, '
                                                   f'here: {linky_link}'))
                                print('wrong')
                            good_match = True
                        else:
                            wrong_type.append(f'Wrong type: {course["name"]}:'
                                              f' `{item["title"]}` '
                                              f'type({item["type"]}) isn\'t '
                                              f'a \"page\" {linky_link}')
                            print('wrong type')
                            good_match = True
                    else:
                        pass
                except KeyError:
                    print(f'\t---`{item["title"]}` type({item["type"]}) '
                          f'threw an error: {linky_link}')
    if good_match is False:
        add_survey.append(f'Check this course: {course["name"]}, '
                          f'{linky_link}, `item_count`: {item_count}')


print('CLOSE NAMES:====================================')
for close in close_name:
    print(close)

print('ADD SURVEY: ====================================')
for add in set(add_survey):
    print(add)

print('WRONG TYPE: ====================================')
for wrong in wrong_type:
    print(wrong)

print(f'All done, searched all courses for {m_name}')
