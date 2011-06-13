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


class RedmineApiError(Exception):
            """ Exception for Redmine API errors """



class Issue(object):
    def __init__(self,
                id=None,
                project_id=None,
                author=None,
                subject=None,
                description=None,
                tracker_id=None):
        self.id = id
        self.author = author
        self.project_id = project_id
        self.subject = subject
        self.description = description
        self.tracker_id = tracker_id
    
    @staticmethod 
    def newFromApi(data):
        return Issue(data['id'],
              data['project']['id'],
              data['author']['name'],
              data['subject'],
              data['description'])
        
        
        
        
    def __str__(self):
        return '%s - %s - %s' % (self.id, 
                                        self.author, 
                                        self.subject)
      

    def __unicode__(self):
        return '%s - %s - %s \n\n %s' % (self.id, 
                                        self.author['name'], 
                                        self.subject, 
                                        self.description)

    def save(self,r):
        ''' saves a new issue to the given API instance from Issue instance 
            if you need to update an issue, use update() instead.
        '''
        new_issue = {
                    'issue': self.__dict__}
        content = r._apiPost('issues',new_issue)
        return self.newFromApi(content)
    
    
    
class Project(object):
    def __str__(self):
        return '%s - %s - %s' % (self.id, self.name, self.description)



class Redmine(object):
    def __init__(self,hostname=None,apikey=None):
        # Status ID from a default install
       self.ISSUE_STATUS = {} 
       self.ISSUE_STATUS['new'] = 1
       self.ISSUE_STATUS['resolved'] = 3 
       self.ISSUE_STATUS['CLOSE'] = 3
       self.apikey = apikey
       self.hostname = hostname
     
    def check_reqs(self,func=None):
        if self.hostname is None:
            raise RedmineApiError('You must supply a Hostname to your redmine installation.')
        if self.apikey is None:
            raise RedmineApiError('Missing Redmine API Key.')
        if func is None:
            raise RedmineApiError('Missing function call.')
    
    def _apiGet(self,func,params=None):
        self.check_reqs(func)
        
        api_url = 'http://%s/%s.json?key=%s' % (self.hostname,func,self.apikey)
        try:
            h = httplib2.Http()
            resp,content = h.request(api_url,
                            'GET',
                            json.dumps(params),
                            headers={'Content-Type': 'application/json'})
            return content
        except HTTPError, e:
            raise RedmineApiError("HTTPError - %s" % e.read())
        except (ValueError, KeyError), e:
            raise RedmineApiError('Invalid Response - %s', e.code())         
                


    def _apiPost(self,func,params=None):
        self.check_reqs(func)
        
        
        api_url = 'http://%s/%s.json?key=%s' % (self.hostname,func,self.apikey)
        try:
            
            h = httplib2.Http()
            resp, content = h.request(api_url,
                          'POST',
                          json.dumps(params),
                          headers={'Content-Type': 'application/json'})
            
            return content
        except HTTPError, e:
            raise RedmineApiError("HTTPError - %s" % e.read())
        except (ValueError, KeyError), e:
            raise RedmineApiError('Invalid Response - %s' % e.code())        


    
    def getIssue(self,id=None):
        if id is None:
            raise RedmineApiError("You must provide an id to get a specific issue")
        result = json.loads(self._apiGet('issues/%s' % id))['issue']
        return Issue.newFromApi(result)


    def getIssues(self,**kwargs):
        results = json.loads(self._apiGet('issues', kwargs))['issues']
        return [[Issue.newFromApi(i)] for i in results]


    
    
    class projects(object):
        @staticmethod
        def get(**kwargs):
            project_id = kwargs=['project_id']
            if project_id is None:
                raise RedmineApiError("You must provide a project_id")
            result = super(projects,self)._apiGet('projects/%s' % project_id)['project']
            return Project(result)
        

        def getList(self,**kwargs):
            results = super(projects,self)._apiGet('projects',kwargs)
            return [Project(p) for p in results['projects']]
    
    
