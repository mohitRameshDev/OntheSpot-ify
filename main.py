import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from googleapiclient.discovery import build

#Login page of APP:
def loginPage(mySpotify):
        st.header('Spotify to Youtube')
        st.write(f'''
                Please login to your spotify
                ''')
        spotifyUrl = mySpotify.login()
        st.write(f'''
            <a target ="_self" href="{spotifyUrl}">
            <button style="background:#3630a3;color:white;">
            Login to Spotify
            <button></a>
            ''',
            unsafe_allow_html=True)

#Spotify Part
class mySpotify:
    
    def create_spotify_oauth(self):
        return SpotifyOAuth(
            client_id="946d958ef6b54bbaa547a36c15743c90",
            client_secret="1f677513266443a881a4115f0780e20f",
            redirect_uri="http://localhost:8000/error",
            scope='user-library-read playlist-read-private playlist-read-collaborative')

    def login(self):
        auth_url = self.create_spotify_oauth().get_authorize_url()
        return auth_url
    
    def getToken(self):
        now =  int(time.time())
        token_info = self.create_spotify_oauth().get_access_token()
        isExpired= token_info['expires_at'] - now < 60
        
        if not token_info:
            st.session_state.runpage=loginPage()
            st.experimental_rerun()
        if(isExpired):
            spotify_auth = self.create_spotify_oauth()
            token_info =  spotify_auth.create_spotify_oauth().get_access_token(token_info['refresh_token'])
        return token_info
    
    def getListOfPlaylists(self):
        try:
            token_info = self.getToken()
        except:
            print("User logged in!!")
            st.session_state.runpage=loginPage()
            st.experimental_rerun()

        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_playlists = sp.current_user_playlists()['items']
        userPlaylists = []
        for playlist in current_playlists:
            userPlaylists.append(playlist['name'])
        print(userPlaylists)
        return userPlaylists
    
    def getSongNames(self,selectedPlaylist):
        try:
            token_info  = self.getToken()
        except:
            print("User logged in!!")
            st.session_state.runpage=loginPage()
            st.experimental_rerun()

        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_playlists = sp.current_user_playlists()['items']
        for playlist in current_playlists:
            if(playlist['name'] == selectedPlaylist):
                playlistneeded_id = playlist['id']
            else:
                print('not found')
        
        neededplaylist = sp.playlist_items(playlistneeded_id)
        songNames = []
        for song in neededplaylist['items']:
            song_name =  song['track']['name']
            songNames.append(song_name)
        return songNames

#YouTube Part
class myYoutube:

    def __init__(self):
        self.creds=None
        if os.path.exists("token.pickle"):
            print("Loading Credentials from file...")
            with open("token.pickle","rb") as token :
                self.creds=pickle.load(token)
            self.service = build("youtube","v3",credentials=self.creds)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                print('Fetching New Tokens...')

                flow = InstalledAppFlow.from_client_secrets_file('client_secret.json',
                scopes=['https://www.googleapis.com/auth/youtubepartner',
                        'https://www.googleapis.com/auth/youtube',
                        'https://www.googleapis.com/auth/youtube.force-ssl'])

                flow.run_local_server(port=8000,prompt='consent')

                self.creds = flow.credentials
                print(self.creds.to_json())

                with open("token.pickle","wb") as f:
                    print("Saving Credentials...")
                    pickle.dump(self.creds,f)
                self.service = build("youtube","v3",credentials=self.creds)
                print('You are Ready to go!!')

    def makeNewPlaylist(self,title,description=None,priv = 'private'):
        request_body = {
                'snippet': {
                    'title': title,
                    'description': description,
                },
                'status': {
                    'privacyStatus': priv
                }
            }
        response = self.service.playlists().insert(
            part='snippet,status',
            body=request_body
        ).execute() 
        print(response)
        print("Check Your Youtube Playlists")
        return response['id']

    def getVideoId(self,keyword):
        request = self.service.search().list(
        part="snippet",
        maxResults=25,
        q=keyword
    )
        response = request.execute()
        songId = response['items'][0]['id']['videoId']
        print(songId)
        return songId

    def addSpotifySongs(self,playlist_title,songNames):

        playlist_id=self.makeNewPlaylist(playlist_title)
        
        for key in songNames:
            video_id = self.getVideoId(key)
            request_body = {
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                    }
                }
            }
            response = self.service.playlistItems().insert(
                part='snippet',
                body=request_body
            ).execute()
            video_title = response['snippet']['title']
            print(f'Video "{video_title}" inserted to {playlist_title} playlist')
        


    


if __name__ == '__main__':
    spot = mySpotify()
    you = myYoutube()
    loginPage(spot)

    userPlaylists = spot.getListOfPlaylists()
    selected_playlist = st.selectbox(
        "select a playlist",
        userPlaylists)
    

    songNames=spot.getSongNames(selected_playlist)
    playlist_title = st.text_input("Enter your the name of the playlist to be created")
    if st.button("Create Youtube Playlist of Spotify Songs"):
        try:
            you.addSpotifySongs(playlist_title,songNames)
            print('Done!!')
        except:
            st.error("Sorry couldnt fetch all the songs :(",icon="🚨")
        