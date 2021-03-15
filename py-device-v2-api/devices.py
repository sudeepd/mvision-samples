import requests
import jwt
import time

cutoff = "2021-03-13T00:00:00.000"

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



'''
Get the list of devices that havent called back since the cutoff time
Paginates with a limit of 1000 entries per call, and returns the guid
'''
def getDevicesByLastUpdate(token, iam : IamParameters, api : ApiParameters, cutoffTime) :
    print(f"Getting devices with cutoff time {cutoffTime}")
    url = api.apiUrl + "/epo/v2/devices"
    devices = []
    nextItem=None
    hasMore=True
    while hasMore:
        token=getToken(token, iam)
        params={
            "filter[lastUpdate][GT]" : cutoffTime,
            "fields" : "agentGuid,computerName",
            "page[limit]" : 1000
        }
        if nextItem : 
            url = nextItem
        headers={ 
            "content-type" : "application/vnd.api+json", 
            "x-api-key" : api.apiKey,
            "authorization" : "Bearer " + token
        }        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()            
            if data and data.get("links") and data.get("links").get("next"):
                nextItem = data["links"]["next"]
                hasMore = True
            else:
                hasMore=False
            devices.extend(list(map(lambda x : { 
                "id" : x["id"] , 
                "agentGuid" : x["attributes"]["agentGuid"], 
                "computerName" : x["attributes"]["computerName"] },
                data["data"])))
        else:
            raise Exception("Unable to get devices by update time")
    print(f"Devices found {devices}")
    return devices

'''
Get a name given a tag
'''
def getTagWithName(token, iam : IamParameters, api : ApiParameters, tagName):
    print(f"Getting id of tag with name {tagName}")
    url = api.apiUrl + "/epo/v2/tags"
    token=getToken(token, iam)
    params={
        "filter[name][EQ]" : tagName,
        "page[limit]" : 1000
    }
    headers={ 
        "content-type" : "application/vnd.api+json", 
        "x-api-key" : api.apiKey,
        "authorization" : "Bearer " + token
    }        
    response = requests.get(url, headers=headers, params=params)

# Ideally we only have one tag with a given name, and so we do not iterate
# but simply take the first element and get the id of the tag
    if response.status_code == 200:
        data = response.json()            
        items = data["data"]
        if len(items) > 0 : 
            return items[0]["id"]
        else:
            raise Exception("Tag with specified name does not exists")
    else:
        raise Exception("Unable to get tag with the given name")    



'''
A tag can be assigned to a device either with a device api or with a tag api
In this case,we use the device api to asign tags
'''
def tagDevice(token, iam : IamParameters , api : ApiParameters, deviceId, tagId):
    url = api.apiUrl + "/epo/v2/devices/" + deviceId + "/relationships/assignedTags"
    print(f"Tagging device {deviceId} with tag {tagId} and url {url}")
    token=getToken(token, iam)
    headers={ 
        "content-type" : "application/vnd.api+json", 
        "x-api-key" : api.apiKey,
        "authorization" : "Bearer " + token
    }        
    payload={
        "data" :  [
            {
                "id" : int(tagId),
                "type" : "tags"
            }
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 204:
        print(f"status code {response.status_code} ")
        raise Exception("Unable to tag system")    

def untagDevice(token, iam : IamParameters , api : ApiParameters, deviceId, tagId):
    url = api.apiUrl + "/epo/v2/devices/" + deviceId + "/relationships/assignedTags"
    print(f"untagging device {deviceId} with tag {tagId} and url {url}")
    token=getToken(token, iam)
    headers={ 
        "content-type" : "application/vnd.api+json", 
        "x-api-key" : api.apiKey,
        "authorization" : "Bearer " + token
    }        
    payload={
        "data" :  [
            {
                "id" : int(tagId),
                "type" : "tags"
            }
        ]
    }
    response = requests.delete(url, headers=headers, json=payload)
    if response.status_code != 204:
        print(f"status code {response.status_code} ")
        raise Exception("Unable to untag system")    


t = getToken(None, iamParameters)
print(f"Token is {t}")
staleDevices = getDevicesByLastUpdate(t,iamParameters, apiParameters, cutoff)
deviceId = staleDevices[0]["id"]
tagId = getTagWithName(t, iamParameters, apiParameters, "deadagent")
untagDevice(t,iamParameters,apiParameters, deviceId, tagId)
