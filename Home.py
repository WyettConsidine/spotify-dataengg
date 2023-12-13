# App Interface
import streamlit as st 
import time

# for spotify 
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

# os dependencies
import sys
import os


# Rendering 
from src.subtitle import makesubtitle
from src.title import maketitle
from src.font import setfonts



def load_keys():

    client_id = st.secrets['CLIENT_ID']
    client_secret = st.secrets['CLIENT_SECRET']
    
    keys = (client_id, client_secret)

    return keys



def instantiate_spotipy_object():

    client_id, client_secret = load_keys()

    # Instantiate Object
    SPOTIPY_CLIENT_ID = client_id
    SPOTIPY_CLIENT_SECRET = client_secret
    #SPOTIPY_REDIRECT_URI = 'https://inferential-spotify-dashboard.streamlit.app/'
    SPOTIPY_REDIRECT_URI = 'http://localhost:8501/callback' # for testing
    SCOPE= 'user-library-read user-library-modify playlist-read-private playlist-modify-private user-top-read'

    #Initialize the Spotify client
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=SCOPE,
        )
    )

    return sp, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SCOPE




def get_token(sp, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SCOPE):


    token_info = None

    try:
        token_info = st.session_state['token_info']
        
    except KeyError:
        pass

    if token_info and time.time() < token_info['expires_at']:
        print("Found cached token!")
        token_info['access_token']

    sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=SCOPE)
    url = sp_oauth.get_authorize_url()
    st.sidebar.link_button('Click Here to Authenticate!', url)

    if 'code' in st.experimental_get_query_params():
        st.write("inside if code")
        code = st.experimental_get_query_params()['code'][0]
        token_info = sp_oauth.get_access_token(code)
        st.session_state['token_info'] = token_info

        st.code(st.session_state)
        return token_info['access_token']
    
    return None

def spotipy_wrapped(sp):

    username = st.text_input("Your Username?")

    try:
        # Retrieve the user's top tracks
        time_range = 'long_term'  # Options: 'short_term', 'medium_term', 'long_term'
        top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=25)

        st.subheader("Your top tracks this year!")
        for idx, track in enumerate(top_tracks['items'], 1):
            st.code(f"{idx}. {track['name']} by {', '.join([artist['name'] for artist in track['artists']])}")


    except:
        st.error("something went wrong!")






def fetch_song_meta(sp):

    # Get the current user's username
    user_info = sp.current_user()
    user_id = user_info['id']
    # print(f"Logged in as {user_id}")

    # Search for a track
    track_name = st.text_input("Enter a Track Name", placeholder="Runaway",value="Runaway")
    search_results = sp.search(q=track_name, type='track', limit=1)

    if search_results and search_results['tracks']['items']:
        track = search_results['tracks']['items'][0]
        # Get album information
        # st.write(track)
        album_info = sp.album(track['album']['id'])
        track_id = track['id']
        cols = st.columns(2)

        with cols[0]:
            makesubtitle(f"{track['name']} by {', '.join([artist['name'] for artist in track['artists']])}", color='b',weight='bold')
            #st.code(f"Track: {track['name']} by {', '.join([artist['name'] for artist in track['artists']])}")
            album_art_url = album_info['images'][0]['url']
            st.image(album_art_url, width=450)

        # Get album art URL
        with cols[1]:
            
            
            # Get audio features for the track
            audio_features = sp.audio_features([track['uri']])[0]
            st.code(f"Audio Features for {track['name']}:")
            st.code(f"Danceability: {audio_features['danceability']}")
            st.code(f"Energy: {audio_features['energy']}")
            st.code(f"Tempo: {audio_features['tempo']}")

        

        

        
    else:
        st.warning(f"No track found with the name '{track_name}'")


##song recomendation system:
#Main Idea: add a tab to the app that allows the user to unput parameters for a new song recomendation. 
#Allows user to set speed of music, dancability, tone, etc.
#App then uses spotify to get song recomendations based on user input and user previous history. 

def song_recomender(sp):
    print("hello")
    def get_recommendations(genres, num_songs):
        seed_genres = genres
        print(f"Seed genres = " + str(seed_genres))
        recommendations = sp.recommendations(seed_genres=seed_genres, limit=num_songs)
        return recommendations['tracks']


    st.header("Song Recomendation System")
    st.subheader("Welcome to the song recomenadation page.")
    st.write("In this page, you can tune the parameters below to find the perfect songs for you right now! ")
    st.write("The song recomendtions will be based off of both the inputs you provide, and your previous listening history.")

    num_songs = st.slider("Number of Songs", min_value=1, max_value=20, value=5)
    # Dropdown 2
    genreList =  '''Pop
                    Rock
                    Hip-Hop
                    Rap
                    R&B (Rhythm and Blues)
                    Jazz
                    Blues
                    Country
                    Folk
                    Electronic
                    Dance
                    Indie
                    Alternative
                    Classical
                    Reggae
                    Metal
                    Punk
                    Funk
                    Soul
                    Gospel
                    World
                    Latin
                    Ambient
                    Dubstep
                    Techno
                    House
                    Trance
                    Ska
                    Grunge
                    Experimental'''
    genres = genreList.replace("\n", ", ").split(",")
    genres = [g.strip().lower() for g in genres]

    selectGeneres = st.multiselect("Select up to 5 genres", genres, max_selections = 5)

    # Dropdown 3
    #option3 = st.selectbox("Genre 2", ["Choose", "Option 3A", "Option 3B", "Option 3C"])

    # Submit button

    if st.button("Get Recommendations"):
        if not selectGeneres:
            st.warning("Please select at least one genre.")
        else:
            recommendations = get_recommendations(selectGeneres, num_songs)
            st.subheader("Recommended Songs:")
            for idx, track in enumerate(recommendations):
                st.write(f"{idx + 1}. {track['name']} by {', '.join([artist['name'] for artist in track['artists']])}")



# main interface -- app starts here
def main_cs():

    # Initialize session state    

    setfonts()
    maketitle()
    

    sp, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SCOPE = instantiate_spotipy_object()
    token = get_token(sp, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, SCOPE)
    st.write(token)
    st.sidebar.divider()

    with st.sidebar:
        makesubtitle("Control shelf ⏭️", weight='bold')

    st.divider()


    options = st.sidebar.selectbox("What do you want to know?", ["Select", "Song Recomender", "Current Trends", "Compare Playlists", "Playlist Variability Analysis",
                                                                 "Know the Artist", "Song Meta-Info", "Your Playlist Analysis", "Wrapped!"])


    st.sidebar.divider()

    


    if options == "Song Meta-Info":

        fetch_song_meta(sp)

    elif options == "Wrapped!":
        spotipy_wrapped(sp)
    elif options == "Song Recomender":
        song_recomender(sp)
   


if __name__ == '__main__':

    st.set_page_config(page_title="spotify dash", layout="wide", initial_sidebar_state="auto")

    main_cs()

    

