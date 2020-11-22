from bs4 import BeautifulSoup
from argparse import ArgumentParser
import requests
import pprint
import json
import re
import sys

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def getAllSubjects():
    '''get all subjects for notre dame'''

    codeToName = {}

    url = 'https://class-search.nd.edu/reg/srch/ClassSearchServlet'
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')

    subjNode = soup.find('select', id='SUBJ')
    subjOptions = subjNode.find_all('option')

    for option in subjOptions:

        subjCode = option['value']
        subjName = option.text
        
        codeToName[subjCode] = subjName.strip()

    return codeToName

def getAllCampuses():
    '''get all campuses for notre dame'''

    codeToName = {}

    url = 'https://class-search.nd.edu/reg/srch/ClassSearchServlet'
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')

    campusNode = soup.find('select', attrs={'name': 'CAMPUS'})
    campusOptions = campusNode.find_all('option')

    for option in campusOptions:

        campusCode = option['value']
        campusName = option.text

        codeToName[campusCode] = campusName
    
    return codeToName

def getCourseDetails(crn, termCode, courseId):
    '''explores detailed course page for more information about course'''

    result = {
        'courseLongTitle':      '',
        'courseDescription':    '',
        'courseAttributes':     []
    }

    # note courseId is unique per department
    url = f'https://class-search.nd.edu/reg/srch/ClassSearchServlet?CRN={crn}&TERM={termCode}&P={courseId}'

    html = requests.post(url).text
    soup = BeautifulSoup(html, 'lxml')

    tableNode = soup.find('table', attrs={'class': 'datadisplaytable'})
    trNodes = tableNode.find_all('tr')

    # get long course title
    try:

        courseLongTitle = trNodes[0].find(text=re.compile('Long Title:')) \
            .replace('Long Title:', '').strip()

        result['courseLongTitle'] = courseLongTitle
    
    except AttributeError: # probably NoneType error

        #print(f'{colors.WARNING}  could not fetch long title for {crn, termCode, courseId}{colors.ENDC}')

        pass

    # get course description
    try:
    
        courseDescription = trNodes[1].find('td').find('span', text='Course Description:')\
            .next_sibling.next_sibling.strip()

        result['courseDescription'] = courseDescription

    except AttributeError: # probably NoneType error

        # print(f'{colors.WARNING}  could not fetch description for {crn, termCode, courseId}{colors.ENDC}')

        pass
    
    # get course attributes
    try:

        courseAttrStr = trNodes[1].find('td').find('span', text='Course Attributes:')\
            .next_sibling.next_sibling.next_sibling.strip()

        courseAttrs = list(map(lambda x: x.strip(), courseAttrStr.split(',')))

        result['courseAttributes'] = courseAttrs
    
    except AttributeError: # probably NoneType error

        #print(f'{colors.WARNING}  could not fetch attributes for {crn, termCode, courseId}{colors.ENDC}')
        
        pass
    
    return result

def getPartialCatalogue(termCode, subjCode, campCode):
    '''get all courses for a given subject at a given campus'''
    
    def parseDeptCodeAndCourseId(combined):
        '''helper function to turn i.e. IRLL10101 -> ('IRLL', '10101')'''

        for i in range( len(combined) ):
            if combined[i].isdigit():
                break # [:i] will not include the first digit

        return (combined[:i], combined[i:])

    courses = {}

    url = 'https://class-search.nd.edu/reg/srch/ClassSearchServlet'

    catalogueRequest = {
        'TERM':     termCode,
        'DIVS':     'A', # All divisions
        'CAMPUS':   campCode,
        'SUBJ':     subjCode,
        'ATTR':     '0ANY', # Any/all attribute(s)
        'CREDIT':   'A' # All credits
    }

    html = requests.post(url, data=catalogueRequest).text
    soup = BeautifulSoup(html, 'lxml')
    tableNode = soup.find('table', id='resulttable')
    
    if not tableNode: # table will not be there at all if there are no results
        # print('  no courses found for', termCode, subjCode, 'at', campCode)
        return courses
    
    bodyNode = tableNode.find('tbody')
    rowNodes = bodyNode.find_all('tr')

    for rowNode in rowNodes:

        colNodes = rowNode.find_all('td')

        if len(colNodes) != 14:
            # print('  ignoring rowNode with', len(colNodes), 'colNodes')
            continue
        
        # strip everything becuase there is inconsistency in whitespace
        courseSec   = colNodes[0].text.strip().split('\n')[0].strip()
        title       = colNodes[1].text.strip()
        cr          = colNodes[2].text.strip()
        st          = colNodes[3].text.strip()
        maxSeats    = colNodes[4].text.strip()
        openSeats   = colNodes[5].text.strip()
        xlst        = colNodes[6].text.strip()
        crn         = colNodes[7].text.strip()
        syl         = colNodes[8].text.strip()
        instructor  = colNodes[9].text.strip()
        when        = colNodes[10].text.strip()
        begin       = colNodes[11].text.strip()
        end         = colNodes[12].text.strip()
        where       = colNodes[13].text.strip()
        
        '''
        # uncomment for debug, not-so-neatly-tabular print
        print(courseSec, title, cr, st, maxSeats, openSeats, xlst, crn, syl, \
            instructor, when, begin, end, where)
        '''

        # parse i.e. ACCT10101
        deptAndCourseId = courseSec.split(' - ')[0]
        deptCode, courseId = parseDeptCodeAndCourseId(deptAndCourseId)
        sectNum = int(courseSec.split(' - ')[1])
        
        details = getCourseDetails(crn, termCode, courseId)

        # add unique course Id if not found yet
        if deptAndCourseId not in courses:
            
            # print('  found new unique course', deptAndCourseId)

            courses[deptAndCourseId] = {
                'department':   deptCode,
                'courseId':     courseId,
                'sections':     [],
                'title':        title,
                'semester':     termCode,
                'instructors':  [],
                'longTitle':    details['courseLongTitle'],
                'description':  details['courseDescription'],
                'attributes':   details['courseAttributes']
            }
        

        # parse when times (hybrid classes have multiple entries)
        when = list( filter(None, map( lambda x: x.strip(), re.compile('\([0-9]\)').split(when) )) )

        # parse where (hybrid classes have multiple entries)
        where = list( filter(None, map( lambda x: x.strip(), where.split('\n') )) )

        # do insert
        courses[deptAndCourseId]['sections'].append({
            'section':      sectNum,
            'crn':          crn,
            'instructor':   instructor,
            'maxSeats':     maxSeats,
            'openSeats':    openSeats,
            'where':        where,
            'when':         when
        })

        # add instructor uniquely to course-wide instructors
        setInstructors = set(courses[deptAndCourseId]['instructors'])
        setInstructors.add(instructor)
        courses[deptAndCourseId]['instructors'] = list(setInstructors)

        # check if we are still missing the long title, if so add it
        if courses[deptAndCourseId]['title'] == '':
            courses[deptAndCourseId]['title'] = details['courseLongTitle']

    return courses


def getAllCourses(termCode):
    '''get all courses for notre dame for a given term'''

    subjects = getAllSubjects()
    campuses = getAllCampuses()

    courses = {}

    # for campCode in campuses.keys(): # campus codes
    
    for subjCode in subjects.keys(): # subj codes

        print(f'{colors.HEADER}beginning fetch for subject code {subjCode}{colors.ENDC}')

        results = getPartialCatalogue(termCode, subjCode, 'M')

        # merge results with courses
        for resultCourse in results.keys():

            if resultCourse not in courses.keys():
                courses[resultCourse] = results[resultCourse]
            else:
                print('  COULD NOT DO SIMPLE MERGE FOR', resultCourse)

        pprint.pprint(results)

        print(f'{colors.OKGREEN}  found {len(results)} courses for subject code {subjCode}{colors.ENDC}')
    return courses

parser = ArgumentParser('a tool to scrape all nd courses')
parser.add_argument('ofn', help='the output file to write to')
parser.add_argument('sem', help='the semester code to get courses for')
args = parser.parse_args()

courses = getAllCourses(args.sem)
with open(args.ofn, 'w') as fp:
    json.dump(courses, fp, indent=4)