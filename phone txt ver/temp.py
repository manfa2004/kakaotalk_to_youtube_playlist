import re
from Google import Create_Service
import pandas as pd
from googleapiclient.discovery import build
import httplib2
import os
import sys
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

api_key = 'AIzaSyAEgqbLkwhov_hbQWPM02MhxM-hbziKHKY'

CLIENT_SECRETS_FILE = "client_secret.json"
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))


YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

API_NAME  =  'youtube'
API_VERSION  =  'v3'
SCOPES  = ['https://www.googleapis.com/auth/youtube']

service =  Create_Service(CLIENT_SECRETS_FILE, API_NAME, API_VERSION, SCOPES)

flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
    message=MISSING_CLIENT_SECRETS_MESSAGE,
    scope=YOUTUBE_READ_WRITE_SCOPE)

storage = Storage("%s-oauth2.json" % sys.argv[0])
credentials = storage.get()

if credentials is None or credentials.invalid:
    flags = argparser.parse_args()
    credentials = run_flow(flow, storage, flags)

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))


def video_id(value):
    host = value.split('/')
    if host[2] == 'youtu.be':
        return host[3]
    if host[2] == 'www.youtube.com':
        temp = host[3].replace('watch?v=','').replace('watch?app=desktop&v=','')
        tmp = temp.split('&ab_channel')[0]
        return tmp
    if host[2] == 'music.youtube.com':
        temp = host[3].replace('watch?v=','').replace('&feature=share','')
        return temp
    return None

def add_playlist(query,id):
    try:
        result=youtube.playlistItems().insert(
            part="snippet",
            body={
                'snippet': {
                    'playlistId': query, 
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': id
                    }
                }
            }
        ).execute()
    except Exception:
        result = 'error'
    return result

text = open('manji.txt', 'rt', encoding='UTF8')

name = open("name.txt",'rt', encoding='UTF8')

latestupdate = open("latestupdate.txt",'rt', encoding='UTF8')

lt = []
txt = {}
nm = {}
music = {}
state = 0


l = latestupdate.readlines()
luname = l[0].replace('\n','')
lulink = l[1].replace('\n','')
latestname = ''
latestlink = ''

latestupdate.close()

nick = name.readlines()

for i in nick:
    temp = i.split(':')
    nm[temp[0]] = temp[1].replace('\n','')


mn = {v:k for k,v in nm.items()}

name.close()


lines = text.readlines()

print('check1 : 코드에 필요한 요소 받아오기')

for line in lines:
    if len(line) >= 5:
        if line[0] == '2' and line[4] == '년':
            lt.append(line)

print('check2 : 텍스트 읽어오기')

for j,i in nm.items():
    playlist_id = i
    response = service.playlistItems().list(
        part='contentDetails',
        playlistId=playlist_id,
        maxResults=50
    ).execute()

    playlistItems = response['items']
    nextPageToken = response.get('nextPageToken')
    while nextPageToken:
        response = service.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPageToken
        ).execute()

        playlistItems.extend(response['items'])
        nextPageToken = response.get('nextPageToken')

    df_playlistItems = pd.DataFrame(playlistItems)
    df_contentDetails = df_playlistItems['contentDetails'].apply(pd.Series)

    for k in playlistItems:
        temp = k['contentDetails']
        temp2 = temp['videoId']
        if temp['videoId'] in music:
            print(mn[playlist_id],' 의 플레이리스트가 https://www.youtube.com/watch?v=',temp['videoId'],' 에서 ',music[temp2] ,'의 플레이리스트와 중복입니다',sep="")
        else:
            music[temp['videoId']] = mn[playlist_id]
        
        if 'videoPublishedAt' in temp:
            continue
        service.playlistItems().delete(id=k['id']).execute()
        print(j)

    for videoItem in df_playlistItems[df_contentDetails.duplicated()].iterrows():
        service.playlistItems().delete(id=videoItem[1]['id']).execute()
        print(j)


print('check3 : 플레이리스트 음악 중복 확인')

for i in lt:
    if ' : ' in i:
        n = i.replace("\n","")
        n = n.split(' : ')
        name = n[0].split(', ')[1]
    else:
        continue

    if n[1] == lulink and name == luname:
        state = 1
        continue
    if state == 0:
        continue

    check = n[1].split('/')[0]
    
    if check == 'https:':
        latestname = name
        latestlink = n[1]
        if name in txt:
            txt[name].append(n[1])
        else:
            txt[name] = [n[1]]
        print(name, video_id(n[1]))

print('check4 : 리스트에서 유튜브 링크만 추가')

for key, value in txt.items():
    for i in value:
        id = video_id(i)
        if id in music:
            print(key,'의 ', i,'는 ',music[id],'와 중복입니다',sep='')
            continue
        add_playlist(nm[key],id)
        print(key,'의 ',i,' 가 재생목록에 추가되었습니다',sep='')

f1 = open('latestupdate.txt','w',encoding="UTF-8")

print('check5 : 음악 추가')

if latestname == '':
    print(luname,file=f1)
    print(lulink,file=f1)

else:
    print(latestname,file=f1)
    print(latestlink,file=f1) #프로그램 끝날때 메모장에 박아 넣는걸로

# f1.close()
text.close()

print("\n플레이리스트 업데이트 완료!")