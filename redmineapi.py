""" Python library for interacting with a Redmine installation.

    This library will allow you to interact with Redmine issues and projects,
    including listing, creating and resolving issues.
    

PLEASE NOTE:  This project is nowhere near finished.  Still needs a lot of refinement.
As of now (6/11/11):
issue retrieval and posting work
project retrieval works

TODO:
finish Issue and Project classes
finish issue posting and updating
start project posting and updating
documentation
general clean up


    
"""

__author__ = "Brendan Smith (brendan@nationalpriorities.org)"
__version__ = "0.0.1"
__copyright__ = "Copyright (c) 2010 National Priorities Project"
__license__ = "BSD"



import sys
import warnings

if sys.version_info[0] == 3:
    from urllib.parse import urlencode
    from urllib.request import urlopen
    from urllib.error import HTTPError
else:
    from urllib import urlencode
    from urllib2 import urlopen, Request
    from urllib2 import HTTPError

import httplib2  #turns out httplib2 is actually a lot better at handling JSON POST connections

try:
    import json
except ImportError:
    import simplejson as json

import logging
logger = logging.getLogger('redmine-api')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


ISSUE_STATUS = {} 
ISSUE_STATUS['new'] = 1
ISSUE_STATUS['resolved'] = 3 
ISSUE_STATUS['closed'] = 5


class RedmineApiError(Exception):
            """ Exception for Redmine API errors """


class RedmineApiObject(object):
    def __init__(self, d):
        self.__dict__ = d


class Issue(RedmineApiObject):
    ''' Redmine Issue Object '''

    def __init__(self, d, redmine=None):
        self.__dict__ = d
        self.redmine = redmine
            
    def __repr__(self):
        return "Redmine Issue Object"    
        
    def __str__(self):
        return str(self.__dict__)
        #return '%s - %s - %s - %s' % (self.id,
        #                         self.project['name'],
        #                                self.author['name'], 
        #                                self.subject)

    def __unicode__(self):
        return '%s - %s - %s \n\n %s' % (self.id,
                                        self.author['name'],
                                        self.subject,
                                        self.description)

    def newFromApi(self, content):
        d = json.loads(content)['issue']
        self.__dict__.update(d)

    def save(self):
        ''' saves a new issue to the given API instance from Issue instance 
            if you need to update an issue, use update() instead.
        '''
        new_issue = {
                    'issue': self.__dict__}
        content = self.redmine._apiPost('issues', new_issue)
        return self.newFromApi(content)
    
    def update(self):
        issue = { 'issue': self.__dict__ }
        content = self.redmine._apiPut('issues/%s' % self.id, issue)
        if content.strip():
            return self.newFromApi(content)

    def close(self, notes=None):
        self.update_status(ISSUE_STATUS['closed'], notes=notes)
    
    def resolve(self, notes=None):
        self.update_status(ISSUE_STATUS['resolved'], notes=notes)

    def update_status(self, status_id, notes=None):
        issue_id = self.id
        issue = {
            "issue": {
                "status_id": status_id,
                'notes': '%s <br/><br/><br/>%s' % (notes, '*resolved from python-redmine api*') 
            }
        }
        content = self.redmine._apiPut('issues/%s' % issue_id, issue)

    def annotate(self, notes):
        issue_id = self.id
        issue = {"issue": {'notes':  notes}}
        content = self.redmine._apiPut('issues/%s' % issue_id, issue)
        
class Project(RedmineApiObject):
    ''' Redmine Project Object '''
    
    def __str__(self):
        #return '%s - %s - %s' % (self.id, self.name, self.description)
        return self.__dict__
    def __repr__(self):
        return "New Redmine Project Object"


class User(RedmineApiObject):
    ''' Redmine User Object '''
    
    def __str__(self):
        return '%s - %s - %s, %s' % (self.id, self.login, 
                                     self.lastname, self.firstname)
    
    def __repr__(self):
        return "New Redmine User Object"
    
class Redmine(object):
    
    def __init__(self, hostname=None, apikey=None, ssl=False, easy_ssl=True):
        self.apikey = apikey
        self.hostname = hostname
        self.ssl = ssl
        self.easy_ssl = easy_ssl
        if self.ssl:
            self.scheme = 'https'
        else:
            self.scheme = 'http'
           
    def check_reqs(self, func=None):
        if self.hostname is None:
            raise RedmineApiError('You must supply a Hostname to your redmine installation.')
        if self.apikey is None:
            raise RedmineApiError('Missing Redmine API Key.')
        if func is None:
            raise RedmineApiError('Missing function call.')
    
    def _apiGet(self, func, params=None):
        self.check_reqs(func)
        
        api_url = '%s://%s/%s.json?key=%s' % (self.scheme, self.hostname, 
                                              func, self.apikey)
        try:
            h = httplib2.Http(disable_ssl_certificate_validation=self.easy_ssl)
            if params is not None:
                params['issue']['redmine'] = ''
            resp, content = h.request(api_url,
                            'GET',
                            json.dumps(params),
                            headers={'Content-Type': 'application/json'})
            return content
        except HTTPError, e:
            raise RedmineApiError("HTTPError - %s" % e.read())
        except (ValueError, KeyError), e:
            raise RedmineApiError('Invalid Response - %s', e.code())         
                
    def _apiPost(self, func, params=None):
        self.check_reqs(func)
    
        api_url = '%s://%s/%s.json?key=%s' % (self.scheme, self.hostname, 
                                              func, self.apikey)
        logger.info(api_url)
        try:
            h = httplib2.Http(disable_ssl_certificate_validation=self.easy_ssl)
            if params is not None:
                params['issue']['redmine'] = ''
            resp, content = h.request(api_url,
                          'POST',
                          json.dumps(params),
                          headers={'Content-Type': 'application/json'})
            return content
        except HTTPError, e:
            raise RedmineApiError("HTTPError - %s" % e.read())
        except (ValueError, KeyError), e:
            raise RedmineApiError('Invalid Response - %s' % e.code())        

    def _apiPut(self, func, params=None):
        self.check_reqs(func)
        api_url = '%s://%s/%s.json?key=%s' % (self.scheme, self.hostname, func, self.apikey)
        try:
            
            h = httplib2.Http(disable_ssl_certificate_validation=self.easy_ssl)
            if params is not None:
                params['issue']['redmine'] = ''
            resp, content = h.request(api_url,
                          'PUT',
                          json.dumps(params),
                          headers={'Content-Type': 'application/json'})
            #note: PUT doesn't include any content in the response
            if resp['status'] != '200':
                raise Exception('Invalid response %s', resp['status'])
            return content
        except HTTPError, e:
            raise RedmineApiError("HTTPError - %s" % e.read())
        except (ValueError, KeyError), e:
            raise RedmineApiError('Invalid Response - %s' % e.code())  

        
    class _issues(object):
        def __init__(self, redmine):
            self.redmine = redmine
        
        def get(self, issue_id):
            #issue_id = kwargs=['issue_id']
            if issue_id is None:
                raise RedmineApiError("You must provide an issue_id")
            result = json.loads(self.redmine._apiGet('issues/%s' % issue_id))
            return Issue(result['issue'], redmine=self.redmine)
        
        def set(self, **kwargs):
            issue_id = kwargs['issue_id']
            if issue_id is None:
                raise RedmineApiError("You must provide an issue_id")
            #get the issue first
            data = json.loads(self.redmine._apiGet('issues/%s' % issue_id))
            #update with k/v. Should probably only update the allowed ones.
            for k, v in kwargs.iteritems():
                data['issue'][k] = v
            result = self.redmine._apiPut('issues/%s' % issue_id, data)
            #PUT doesnt seem to return anything, so get the issue, and return it.
            return self.get(**kwargs)
            
        def getList(self, **kwargs):
            results = json.loads(self.redmine._apiGet('issues', kwargs))
            return [Issue(i, redmine=self.redmine) for i in results['issues']]
        
        def new(self, issue):
            if issue is None:
                raise RedmineApiError("You must provide an Issue Object or a dictionary")
            if isinstance(issue, Issue):
                new_issue = {'issue': issue.__dict__}
            else:
                new_issue = {'issue': issue }
            content = self.redmine._apiPost('issues', new_issue)

    @property
    def issues(self):
        return self._issues(self)    
    
    
    class _projects(object):
        def __init__(self, redmine):
            self.redmine = redmine
        
        def get(self, **kwargs):
            project_id = kwargs['project_id']
            if project_id is None:
                raise RedmineApiError("You must provide a project_id")
            result = json.loads(self.redmine._apiGet('projects/%s' % project_id))['project']
            return Project(result)
        
        def getList(self, **kwargs):
            results = json.loads(self.redmine._apiGet('projects', kwargs))
            return [Project(p) for p in results['projects']]
    
    @property
    def projects(self):
        return self._projects(self)

    
    class _users(object):
        def __init__(self, redmine):
            self.redmine = redmine
        
        def get(self, **kwargs):
            user_id = kwargs['user_id']
            if user_id is None:
                raise RedmineApiError("You must provide a user_id")
            result = json.loads(self.redmine._apiGet('users/%s' % user_id))['user']
            return User(result)
        
        def getList(self, **kwargs):
            results = json.loads(self.redmine._apiGet('users', kwargs))
            return [User(u) for u in results['users']]

    @property
    def users(self):
        return self._users(self)
    
    
