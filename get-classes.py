""" This script is supposed to return a list of all the classes in a given
    semester

    It is my understanding that these are the semester IDs
    `enrollment_term_id` is the value we will be setting
        - Winter 2018: 49
        - Fall 2018: 50
        - Spring 2018: 51
        - Summer 2018: 52

"""

import json
import requests as r
# Canvas API URL
API_URL = 'https://byu.instructure.com/api/v1'
# Canvas API Key
API_KEY = input('Enter the API Key below and type [ENTER]\n')

header = {'Authorization': 'Bearer ' + '%s' % API_KEY}

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

    while loop_control is True:
        request = r.get(API_URL +
                        '/accounts/' +
                        str(Account_ID) +
                        '/courses?per_page=1000&page=' +
                        str(page_no),
                        params=payload, headers=header)
        response = request.json()

        courses.append(response)
        page_no += 1
        if page_no == 6:
            loop_control = False

    return courses


all_courses = get_courses(31)

c_course_ids = [(course['id'], course['name'], )
                for course in all_courses[0]]

with open(f'{term_id}-{term_id_dict[term_id][0]}-course-export.csv', 'w') as f:
    print('course_id', 'course_name', 'course_link', sep=',', file=f)
    for k, v in c_course_ids:
        c = f'https://byu.instructure.com/courses/{k}'
        print(k, v, c, sep=',', file=f)
