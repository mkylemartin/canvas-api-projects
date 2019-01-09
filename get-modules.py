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
import time
# Canvas API URL
API_URL = 'https://byu.instructure.com/api/v1'

Account_ID = 31
term_id = '50'
API_KEY = input('Enter your API Key and type Enter\n')

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
    paged_results = []
    loop_control = True
    while loop_control is True:
        request = r.get(API_URL + ''
                        f'/courses/{id_num}/modules?include[]=items'
                        f'&page={page_no}',
                        params=payload, headers=header)
        json_request = request.json()
        # print(len(json_request), type(json_request))
        if len(json_request) != 0:
            page_no += 1
            paged_results.append(json_request)
        else:
            loop_control = False

    # sr == 'string response'
    sr = ''

    sr += '=' * 25 + '\n'
    sr += str(name) + ', ' + str(id_num) + '\n'
    sr += f'https://byu.instructure.com/courses/{id_num}' + '\n'
    sr += '=' * 25 + '\n'

    rows = []
    for page in paged_results:
        # print(len(page))
        for module in page:
            mod = dict(module)
            # print(mod)
            # input('how about them apples??')
            happy = mod['name']
            for item in mod['items']:
                try:
                    sr += ('\t' + '\t' + str(happy) + '\t' +
                           str(item['type']) + '\t' +
                           str(item['published']) + '\t' +
                           str(item['title']) + '\t' + str(item['url']))
                    sr += '\n'
                except KeyError:
                    sr += ('\t' + '\t' + str(happy) + '\t' +
                           str(item['type']) + '\t' +
                           str(item['published']) + '\t' +
                           str(item['title']) + '\t' + 'NO URL AVAILABLE')
                    sr += '\n'

    return str(sr)


# Get a list of all the courses
all_courses = get_courses(31)

c_course_ids = []


for page in all_courses:
    for course in page:
        c_course_ids.append((course['id'], course['name']))

print('len(c_course_ids)', len(c_course_ids))

# print(c_course_ids)

print('Got all courses, and course ids...')


with open(f'{term_id}-{term_id_dict[term_id][0]}-course-module-export.txt',
          'w') as f:
    # print the modules of all the course IDs
    total = len(c_course_ids)
    print(total)
    counter = 1
    for id, name in c_course_ids:
        print(f'{counter}. ', f'({round(counter / total, 3)})', id, name)
        rows = print(get_modules(id, name), file=f)
        print(rows, file=f)
        # Sleep to be nice with the API
        time.sleep(1)
        counter += 1
