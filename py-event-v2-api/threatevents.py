import requests
import jwt
import time

class IamParameters:
    def __init__(self, iamUrl, clientId, clientSecret, scopes):
        self.iamUrl = iamUrl
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.scopes = scopes

class ApiParameters:
    def __init__(self, apiUrl, apiKey):
        self.apiUrl = apiUrl
        self.apiKey = apiKey


iamParameters = IamParameters("iamUrl",
    "clientId",
    "clientSecret",
    "epo.evt.r epo.device.r epo.tags.r epo.tags.w epo.device.w")

apiParameters = ApiParameters("https://api.mvision.mcafee.com","apiKey")

def isValidToken(token) :
    if token is None : return False
    decoded = jwt.decode(token, options = { "verify_signature" : False})
    expiry = decoded["exp"]
    if expiry is None : return False
    if expiry < int(time.time()) : return False
    return True


'''
Checks the current token for expiry. If valid, returns token, else fetches a new one from IAM
'''
def getToken(current , iam : IamParameters) : 
    if not isValidToken(current):
        params = { 'grant_type' : 'client_credentials', 'scope' : iam.scopes }
        response = requests.get(iam.iamUrl, auth=(iam.clientId, iam.clientSecret), params=params)
        if response.status_code == 200 :
            r = response.json()
            return r["access_token"]
        else : 
            raise Exception('Unable to get token')        
    else:
        return current



def fetchEvents(token, iam : IamParameters, api : ApiParameters, startTime ) :
    url = api.apiUrl + "/epo/v2/events"
    nextItem = None
    hasMore = True
    events = []
    while (hasMore) :
        token  = getToken(token, iam)
        params = {
            'filter[timestamp][GE]' : startTime,
            'page[limit]' : 5
        }
        headers={ 
            "content-type" : "application/vnd.api+json", 
            "x-api-key" : api.apiKey,
            "authorization" : "Bearer " + token
        }        
        if nextItem: 
            url = nextItem
            params = {}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()            
            if data and data.get("links") and data.get("links").get("next"):
                nextItem = data["links"]["next"]
                hasMore = True
            else:
                hasMore=False
            events.extend( data["data"])
            return events
        else:
            raise Exception("Error getting threat events from MVISION")

startTime = "2021-03-13T00:00:00.000"
print(fetchEvents(None, iamParameters,apiParameters,startTime))