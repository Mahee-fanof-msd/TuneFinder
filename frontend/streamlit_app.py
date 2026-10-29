import io
import time
import wave

import requests
import streamlit as st


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_URL = "http://127.0.0.1:8000"

RECOGNIZE_URL = f"{BASE_URL}/recognize"
RECOMMEND_URL = f"{BASE_URL}/recommend"
DISCOVER_URL = f"{BASE_URL}/discover"

MIN_DURATION = 10
POLL_INTERVAL = 5
MAX_WAIT_SECONDS = 180

st.set_page_config(
    page_title="TuneFinder",
    page_icon="🎵",
    layout="centered",
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

DEFAULTS = {
    "screen": "home",
    "recording_bytes": None,
    "recognition_result": None,
    "selected_option": None,
    "recommendation_track_id": None,
    "cyanite_result": None,
    "similar_songs_result": None,
    "groq_music_results": None,
    "groq_music_error": None,
    "groq_unverified": [],
    "groq_rejected": [],
    "recorder_version": 0,
    "short_popup_shown": False,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def clear_workflow():
    for key in (
        "recognition_result",
        "selected_option",
        "recommendation_track_id",
        "cyanite_result",
        "similar_songs_result",
        "groq_music_results",
        "groq_music_error",
    ):
        st.session_state[key] = None

    st.session_state.groq_unverified = []
    st.session_state.groq_rejected = []


def go_home():
    clear_workflow()
    st.session_state.recording_bytes = None
    st.session_state.short_popup_shown = False
    st.session_state.screen = "home"
    st.session_state.recorder_version += 1
    st.rerun()


def open_option(option):
    st.session_state.selected_option = option
    st.session_state.screen = "results"
    st.rerun()


def get_audio_duration(audio_bytes):
    with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
        rate = wav.getframerate()
        return wav.getnframes() / rate if rate > 0 else 0


@st.dialog("⚠️ Recording too short")
def show_short_recording_popup(duration):
    st.write(
        f"Your recording is only **{duration:.1f} seconds**."
    )
    st.write(
        f"Please record at least **{MIN_DURATION} seconds** of music."
    )

    if st.button("OK", type="primary", key="short_popup_ok"):
        st.rerun()


def show_request_error(error):
    if isinstance(error, requests.exceptions.ConnectionError):
        st.error(
            "Cannot connect to FastAPI. "
            "Please start your backend."
        )
    elif isinstance(error, requests.exceptions.Timeout):
        st.error(
            "The request timed out. Please try again."
        )
    else:
        detail = str(error)
        response = getattr(error, "response", None)

        if response is not None:
            try:
                detail = response.json().get(
                    "detail", detail
                )
            except (ValueError, AttributeError):
                pass

        st.error(detail)


# --------------------------------------------------
# OPTION 1: IDENTIFY SONG
# SQLITE -> AUDD
# --------------------------------------------------

def identify_song(audio_bytes):
    try:
        with st.spinner(
            "Searching the local database, then AudD if needed..."
        ):
            response = requests.post(
                RECOGNIZE_URL,
                files={
                    "audio": (
                        "recording.wav",
                        audio_bytes,
                        "audio/wav",
                    )
                },
                timeout=180,
            )

            response.raise_for_status()
            result = response.json()

        if not isinstance(result, dict):
            raise ValueError(
                "Invalid recognition response from backend."
            )

        st.session_state.recognition_result = result
        st.session_state.selected_option = None
        st.session_state.screen = "results"
        st.rerun()

    except (
        requests.exceptions.RequestException,
        ValueError,
    ) as error:
        show_request_error(error)


# --------------------------------------------------
# OPTION 2: CYANITE SIMILAR SONGS
# --------------------------------------------------

def request_cyanite_analysis():
    audio_bytes = st.session_state.recording_bytes

    if not audio_bytes:
        raise ValueError(
            "No recording is available. Please record music first."
        )

    response = requests.post(
        RECOMMEND_URL,
        files={
            "audio": (
                "recording.wav",
                audio_bytes,
                "audio/wav",
            )
        },
        timeout=180,
    )

    response.raise_for_status()
    payload = response.json()

    track_id = payload.get("track_id")

    if not track_id:
        raise ValueError(
            "Cyanite did not return a track ID."
        )

    st.session_state.recommendation_track_id = track_id
    st.session_state.cyanite_result = None
    st.session_state.similar_songs_result = None

    return track_id


def wait_for_cyanite_analysis(track_id):
    progress = st.progress(0)
    message = st.empty()
    started = time.monotonic()

    while time.monotonic() - started < MAX_WAIT_SECONDS:
        message.info(
            "🎶 Cyanite is analyzing your recording..."
        )

        response = requests.get(
            f"{RECOMMEND_URL}/{track_id}",
            timeout=45,
        )

        response.raise_for_status()
        result = response.json()

        status = result.get("status")

        if status == "analysis_ready":
            progress.progress(100)
            message.success(
                "Cyanite analysis complete!"
            )
            return result

        if status == "analysis_failed":
            progress.empty()
            message.error(
                "Cyanite analysis failed."
            )
            return result

        elapsed = time.monotonic() - started

        progress.progress(
            min(
                95,
                int(elapsed / MAX_WAIT_SECONDS * 100),
            )
        )

        time.sleep(POLL_INTERVAL)

    progress.empty()
    message.warning(
        "Analysis is taking longer than expected."
    )

    return {
        "status": "processing",
        "track_id": track_id,
    }


def start_cyanite_analysis():
    try:
        with st.spinner(
            "Uploading recording to Cyanite..."
        ):
            track_id = request_cyanite_analysis()

        st.session_state.cyanite_result = (
            wait_for_cyanite_analysis(track_id)
        )

        st.rerun()

    except (
        requests.exceptions.RequestException,
        ValueError,
    ) as error:
        show_request_error(error)


def retry_cyanite_analysis(track_id):
    try:
        st.session_state.cyanite_result = (
            wait_for_cyanite_analysis(track_id)
        )

        st.rerun()

    except requests.exceptions.RequestException as error:
        show_request_error(error)


def fetch_similar_songs(track_id):
    try:
        with st.spinner(
            "Finding similar songs..."
        ):
            response = requests.get(
                f"{RECOMMEND_URL}/{track_id}/similar",
                timeout=60,
            )

            response.raise_for_status()

            st.session_state.similar_songs_result = (
                response.json()
            )

        st.rerun()

    except requests.exceptions.RequestException as error:
        show_request_error(error)


def display_similar_songs(result):
    status = result.get("status")

    if status == "processing":
        st.info(
            "Cyanite is still processing your recording."
        )
        return

    if status == "analysis_failed":
        st.error(
            "Cyanite could not analyze this recording."
        )
        return

    if status != "recommendations_ready":
        st.warning(
            "Similar songs are not available yet."
        )
        return

    songs = result.get("recommendations") or []

    st.subheader("🎵 Top 5 Similar Songs")

    if not songs:
        st.info(
            "No similar songs were found."
        )
        return

    for index, song in enumerate(songs[:5], start=1):
        st.markdown(
            f"**{index}. {song.get('title') or 'Unknown Song'}**"
        )

        spotify_url = song.get("spotify_url")

        if spotify_url:
            st.link_button(
                "🎧 Listen on Spotify",
                spotify_url,
                key=f"similar_spotify_{index}",
            )

        st.divider()


def display_similar_songs_options():
    # Diagram: "Similar Songs with Options" -> Discover or Home
    st.subheader("🎶 What would you like to do next?")

    if st.button(
        "🔎 Discover by Music Preferences",
        use_container_width=True,
        key="similar_to_discover",
    ):
        open_option("discover")

    if st.button(
        "🏠 Home",
        use_container_width=True,
        key="similar_to_home",
    ):
        go_home()


def display_cyanite_workflow():
    st.subheader("🎵 Find Similar Songs")

    st.write(
        "Cyanite will analyze your recorded audio "
        "and find similar songs."
    )

    track_id = st.session_state.recommendation_track_id

    if not track_id:
        if st.button(
            "🎶 Analyze My Recording",
            type="primary",
            use_container_width=True,
        ):
            start_cyanite_analysis()

        return

    analysis = st.session_state.cyanite_result or {}
    status = analysis.get("status")

    if status == "analysis_ready":
        st.success(
            "Cyanite analysis complete!"
        )

        if st.session_state.similar_songs_result is None:
            if st.button(
                "🎵 Show Top 5 Similar Songs",
                type="primary",
                use_container_width=True,
            ):
                fetch_similar_songs(track_id)

    elif status == "processing":
        st.info(
            "Cyanite is still processing."
        )

        if st.button("🔄 Check Again"):
            retry_cyanite_analysis(track_id)

    elif status == "analysis_failed":
        st.error(
            "Cyanite analysis failed."
        )

        if st.button("🔄 Try Analysis Again"):
            st.session_state.recommendation_track_id = None
            st.session_state.cyanite_result = None
            st.rerun()

    else:
        st.info(
            "Your recording has been submitted to Cyanite."
        )

        if st.button("🔄 Check Analysis"):
            retry_cyanite_analysis(track_id)

    similar = st.session_state.similar_songs_result

    if similar is not None:
        st.divider()
        display_similar_songs(similar)
        display_similar_songs_options()


# --------------------------------------------------
# OPTION 3: GROQ -> TAVILY -> GROQ
# --------------------------------------------------

def discover_music(preference):
    st.session_state.groq_music_results = None
    st.session_state.groq_music_error = None
    st.session_state.groq_unverified = []
    st.session_state.groq_rejected = []

    try:
        with st.spinner(
            "Searching and verifying music recommendations..."
        ):
            response = requests.post(
                DISCOVER_URL,
                json={
                    "preference": preference
                },
                timeout=240,
            )

            response.raise_for_status()
            result = response.json()

        st.session_state.groq_music_results = (
            result.get("recommendations", [])
        )

        st.session_state.groq_unverified = (
            result.get("unverified", [])
        )

        st.session_state.groq_rejected = (
            result.get("rejected", [])
        )

    except requests.exceptions.RequestException as error:
        detail = str(error)
        response = getattr(error, "response", None)

        if response is not None:
            try:
                detail = response.json().get(
                    "detail", detail
                )
            except (ValueError, AttributeError):
                pass

        st.session_state.groq_music_error = detail

    except ValueError:
        st.session_state.groq_music_error = (
            "Invalid music discovery response."
        )


def display_sources(song):
    # Diagram: "Display Results with Sources"
    sources = song.get("sources") or []

    if not sources:
        return

    with st.expander("📚 Sources", expanded=False):
        for source in sources[:5]:
            if isinstance(source, dict):
                url = source.get("url")
                title = source.get("title") or url
            else:
                url = source
                title = source

            if url:
                st.markdown(f"- [{title}]({url})")


def display_groq_results():
    error = st.session_state.groq_music_error

    if error:
        st.error(
            f"Music discovery failed: {error}"
        )
        return

    songs = st.session_state.groq_music_results

    if songs is None:
        return

    unverified = (
        st.session_state.groq_unverified or []
    )

    # Evidence sufficient -> results with sources
    if songs:
        st.subheader(
            "🎵 Verified Recommended Songs"
        )

        for index, song in enumerate(songs, start=1):
            st.markdown(
                f"**{index}. {song.get('song') or 'Unknown Song'}**"
            )

            if song.get("artist"):
                st.caption(
                    f"Artist: {song['artist']}"
                )

            if song.get("movie"):
                st.caption(
                    f"Movie: {song['movie']}"
                )

            if song.get("release_date"):
                st.caption(
                    f"Release date: {song['release_date']}"
                )

            if song.get("listening_url"):
                st.link_button(
                    "🎧 Listen",
                    song["listening_url"],
                    key=f"verified_listen_{index}",
                )

            display_sources(song)

            st.divider()

    # Nothing found at all -> show uncertainty and ask for details
    elif not unverified:
        st.warning(
            "⚠️ We couldn't find any songs "
            "for this preference."
        )

        st.info(
            "Please add more details and try again, for example: "
            "language, artist or actor, movie or album name, "
            "mood, or the year or decade."
        )

    if unverified:
        st.subheader("🔎 Possible Matches")

        st.caption(
            "Some details for these songs remain unverified."
        )

        for index, song in enumerate(unverified, start=1):
            st.markdown(
                f"**{index}. {song.get('song') or 'Unknown Song'}**"
            )

            if song.get("artist"):
                st.caption(
                    f"Artist: {song['artist']}"
                )

            checks = song.get("checks") or {}

            pending = [
                name.replace("_", " ")
                for name, status in checks.items()
                if status == "unverified"
            ]

            if pending:
                st.caption(
                    "Unconfirmed: " + ", ".join(pending)
                )

            if song.get("listening_url"):
                st.link_button(
                    "🎧 Listen (unverified)",
                    song["listening_url"],
                    key=f"unverified_listen_{index}",
                )

            display_sources(song)

            st.divider()

    rejected = (
        st.session_state.groq_rejected or []
    )

    if rejected:
        st.caption(
            f"{len(rejected)} candidate(s) excluded "
            "because of verification concerns."
        )


def display_discovery_workflow():
    st.subheader(
        "🔎 Discover by Music Preferences"
    )

    st.write(
        "Describe the type of songs you want. "
        "Groq and Tavily will help find and verify candidates."
    )

    with st.form("music_preference_form"):
        preference = st.text_input(
            "Your music preference",
            placeholder=(
                "Example: Telugu romantic songs "
                "featuring Nani"
            ),
        )

        submitted = st.form_submit_button(
            "🎵 Find Songs",
            type="primary",
        )

    if submitted:
        preference = preference.strip()

        if not preference:
            st.warning(
                "Please enter a music preference."
            )
        else:
            discover_music(preference)

    display_groq_results()


# --------------------------------------------------
# DISPLAY SONG RECOGNITION RESULT
# --------------------------------------------------

def display_recognition_result(result):
    status = result.get("status")

    if status == "song_found":
        st.success("🎉 Song Found!")

        st.subheader(
            result.get("song") or "Unknown Song"
        )

        source = result.get("source", "SQLite")

        if source == "AudD":
            st.caption(
                "🌐 Identified using AudD"
            )
        else:
            st.caption(
                "💾 Identified using local SQLite"
            )

        if result.get("artist"):
            st.write(
                "🎤 **Artist:**",
                result["artist"],
            )

        if result.get("album"):
            st.write(
                "💿 **Album:**",
                result["album"],
            )

        if source != "AudD":
            speed = result.get(
                "detected_playback_speed"
            )

            if speed is not None:
                st.write(
                    "🎚️ **Playback speed:**",
                    f"{speed}x",
                )

            position = result.get("start_time")

            if position is not None:
                st.write(
                    "⏱️ **Song position:**",
                    f"{position:.1f} seconds",
                )

        if source == "AudD":
            spotify = result.get("spotify") or {}
            apple_music = result.get("apple_music") or {}

            album_data = spotify.get("album") or {}
            images = album_data.get("images") or []

            if images and images[0].get("url"):
                st.image(
                    images[0]["url"],
                    width=250,
                )

            spotify_url = (
                spotify.get("external_urls") or {}
            ).get("spotify")

            if spotify_url:
                st.link_button(
                    "🎧 Listen on Spotify",
                    spotify_url,
                    key="recognition_spotify",
                )

            apple_url = apple_music.get("url")

            if apple_url:
                st.link_button(
                    "🍎 Listen on Apple Music",
                    apple_url,
                    key="recognition_apple",
                )

    elif status == "song_not_found":
        st.warning("🎵 No Song Found")

        st.write(
            "We couldn't identify the song using "
            "your local database or AudD."
        )

        st.info(
            "You can still find similar music "
            "or discover songs using your preferences."
        )

    elif status == "online_recognition_error":
        st.warning(
            "Online recognition is temporarily unavailable."
        )

        st.write(
            result.get("message", "")
        )

    else:
        st.error(
            result.get(
                "message",
                "Unable to process recording.",
            )
        )


# --------------------------------------------------
# DISPLAY OPTIONS (AFTER RECORDING)
# --------------------------------------------------

def display_home_options():
    st.divider()
    st.subheader(
        "🎶 What would you like to do?"
    )

    st.write(
        "Choose an option to continue with your recording."
    )

    if st.button(
        "🔍 1. Identify Song",
        type="primary",
        use_container_width=True,
    ):
        identify_song(
            st.session_state.recording_bytes
        )

    if st.button(
        "🎵 2. Similar Songs",
        use_container_width=True,
    ):
        open_option("similar")

    if st.button(
        "🔎 3. Discover by Music Preferences",
        use_container_width=True,
    ):
        open_option("discover")

    if st.button(
        "🚪 Exit / Record Again",
        use_container_width=True,
    ):
        go_home()


# --------------------------------------------------
# OPTIONS AFTER RECOGNITION RESULT
# --------------------------------------------------

def display_results_options():
    st.divider()
    st.subheader(
        "🎶 What would you like to do next?"
    )

    if st.session_state.selected_option is None:
        if st.button(
            "🎵 Similar Songs",
            use_container_width=True,
        ):
            st.session_state.selected_option = "similar"
            st.rerun()

        if st.button(
            "🔎 Discover by Music Preferences",
            use_container_width=True,
        ):
            st.session_state.selected_option = "discover"
            st.rerun()

        if st.button(
            "🏠 Home",
            use_container_width=True,
        ):
            go_home()

        return

    if st.button("← Back to Options"):
        st.session_state.selected_option = None
        st.rerun()

    if st.session_state.selected_option == "similar":
        display_cyanite_workflow()

    elif st.session_state.selected_option == "discover":
        display_discovery_workflow()


# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------

st.title("🎵 TuneFinder")
st.subheader("Discover what's playing")


# --------------------------------------------------
# HOME: RECORD 10 SECONDS, THEN DISPLAY OPTIONS
# --------------------------------------------------

if st.session_state.screen == "home":
    st.info(
        f"🎤 Record at least {MIN_DURATION} seconds of music "
        "to get started."
    )

    audio = st.audio_input(
        "Tap the microphone to record music",
        sample_rate=22050,
        key=f"microphone_{st.session_state.recorder_version}",
    )

    if audio is not None:
        audio_bytes = audio.getvalue()

        st.audio(audio)

        if (
            st.session_state.recording_bytes
            != audio_bytes
        ):
            clear_workflow()
            st.session_state.recording_bytes = audio_bytes
            st.session_state.short_popup_shown = False

        try:
            duration = get_audio_duration(audio_bytes)

        except (
            wave.Error,
            EOFError,
            ZeroDivisionError,
        ):
            duration = 0
            st.error(
                "Unable to read the recording."
            )

        st.caption(
            f"🎙️ Recording duration: {duration:.1f} seconds"
        )

        if duration < MIN_DURATION:
            st.warning(
                f"Please record at least {MIN_DURATION} seconds of music."
            )

            if not st.session_state.short_popup_shown:
                st.session_state.short_popup_shown = True
                show_short_recording_popup(duration)

        else:
            st.success(
                "Recording completed successfully!"
            )

            display_home_options()


# --------------------------------------------------
# RESULTS: RECOGNITION RESULT OR SELECTED OPTION
# --------------------------------------------------

elif st.session_state.screen == "results":
    result = st.session_state.recognition_result

    if result:
        display_recognition_result(result)

        if result.get("status") in {
            "song_found",
            "song_not_found",
            "online_recognition_error",
        }:
            display_results_options()

        else:
            if st.button("🏠 Home"):
                go_home()

    else:
        # User picked Similar Songs or Discover directly from the options
        if st.session_state.selected_option == "similar":
            display_cyanite_workflow()

        elif st.session_state.selected_option == "discover":
            display_discovery_workflow()

        if st.button("🏠 Home", key="results_home"):
            go_home()