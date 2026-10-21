
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
    st.session_state.screen = "home"
    st.session_state.recorder_version += 1
    st.rerun()


def get_audio_duration(audio_bytes):
    with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
        rate = wav.getframerate()
        return wav.getnframes() / rate if rate > 0 else 0


def show_request_error(error):
    if isinstance(error, requests.exceptions.ConnectionError):
        st.error("Cannot connect to FastAPI. Start your backend.")
    elif isinstance(error, requests.exceptions.Timeout):
        st.error("Request timed out. Please try again.")
    else:
        detail = str(error)
        response = getattr(error, "response", None)

        if response is not None:
            try:
                detail = response.json().get("detail", detail)
            except (ValueError, AttributeError):
                pass

        st.error(detail)


# --------------------------------------------------
# SQLITE -> AUDD RECOGNITION
# --------------------------------------------------

def identify_song(audio_bytes):
    try:
        with st.spinner("Identifying your song..."):
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
            raise ValueError("Invalid recognition response.")

        st.session_state.recognition_result = result
        st.session_state.screen = "results"
        st.rerun()

    except (requests.exceptions.RequestException, ValueError) as error:
        show_request_error(error)


# --------------------------------------------------
# CYANITE AUDIO UPLOAD
# --------------------------------------------------

def request_cyanite_analysis():
    audio_bytes = st.session_state.recording_bytes

    if not audio_bytes:
        raise ValueError("No recording is available.")

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
        raise ValueError("Cyanite did not return a track ID.")

    st.session_state.recommendation_track_id = track_id
    st.session_state.cyanite_result = None
    st.session_state.similar_songs_result = None

    return track_id


def wait_for_cyanite_analysis(track_id):
    progress = st.progress(0)
    message = st.empty()
    started = time.monotonic()

    while time.monotonic() - started < MAX_WAIT_SECONDS:
        message.info("🎶 Cyanite is analyzing your recording...")

        response = requests.get(
            f"{RECOMMEND_URL}/{track_id}",
            timeout=45,
        )
        response.raise_for_status()

        result = response.json()
        status = result.get("status")

        if status == "analysis_ready":
            progress.progress(100)
            message.success("Cyanite analysis complete!")
            return result

        if status == "analysis_failed":
            progress.empty()
            message.error("Cyanite analysis failed.")
            return result

        elapsed = time.monotonic() - started

        progress.progress(
            min(95, int(elapsed / MAX_WAIT_SECONDS * 100))
        )

        time.sleep(POLL_INTERVAL)

    progress.empty()
    message.warning("Analysis is taking longer than expected.")

    return {
        "status": "processing",
        "track_id": track_id,
    }


def start_cyanite_analysis():
    try:
        with st.spinner("Uploading recording to Cyanite..."):
            track_id = request_cyanite_analysis()

        st.session_state.cyanite_result = (
            wait_for_cyanite_analysis(track_id)
        )
        st.rerun()

    except (requests.exceptions.RequestException, ValueError) as error:
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
        with st.spinner("Finding similar songs..."):
            response = requests.get(
                f"{RECOMMEND_URL}/{track_id}/similar",
                timeout=60,
            )
            response.raise_for_status()

            st.session_state.similar_songs_result = response.json()

        st.rerun()

    except requests.exceptions.RequestException as error:
        show_request_error(error)


def display_similar_songs(result):
    status = result.get("status")

    if status == "processing":
        st.info("Cyanite is still processing.")
        return

    if status == "analysis_failed":
        st.error("Cyanite could not analyze this recording.")
        return

    if status != "recommendations_ready":
        st.warning("Similar songs are not available yet.")
        return

    songs = result.get("recommendations") or []

    st.subheader("🎵 Top 5 Similar Songs")

    if not songs:
        st.info("No similar songs were found.")
        return

    for index, song in enumerate(songs, start=1):
        st.markdown(
            f"**{index}. {song.get('title') or 'Unknown Song'}**"
        )

        spotify_url = song.get("spotify_url")

        if spotify_url:
            st.link_button("🎧 Listen on Spotify", spotify_url)

        st.divider()


# --------------------------------------------------
# GROQ -> TAVILY -> GROQ -> VERIFICATION
# --------------------------------------------------

def discover_music(preference):
    st.session_state.groq_music_results = None
    st.session_state.groq_music_error = None
    st.session_state.groq_unverified = []
    st.session_state.groq_rejected = []

    try:
        with st.spinner("Finding and verifying songs..."):
            response = requests.post(
                DISCOVER_URL,
                json={"preference": preference},
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
                detail = response.json().get("detail", detail)
            except (ValueError, AttributeError):
                pass

        st.session_state.groq_music_error = detail

    except ValueError:
        st.session_state.groq_music_error = (
            "Invalid music discovery response."
        )


def display_groq_results():
    error = st.session_state.groq_music_error

    if error:
        st.error(f"Music discovery failed: {error}")
        return

    songs = st.session_state.groq_music_results

    if songs is None:
        return

    if songs:
        st.subheader("🎵 Verified Recommended Songs")

        for index, song in enumerate(songs, start=1):
            st.markdown(
                f"**{index}. {song.get('song') or 'Unknown Song'}**"
            )

            if song.get("artist"):
                st.caption(f"Artist: {song['artist']}")

            if song.get("movie"):
                st.caption(f"Movie: {song['movie']}")

            if song.get("release_date"):
                st.caption(f"Release date: {song['release_date']}")

            if song.get("listening_url"):
                st.link_button(
                    "🎧 Listen",
                    song["listening_url"],
                )

            st.divider()
    else:
        st.info("No fully verified songs were found.")

    unverified = st.session_state.groq_unverified or []

    if unverified:
        st.subheader("🔎 Possible Matches")

        st.caption(
            "These songs may match your preference, "
            "but some information remains unverified."
        )

        for index, song in enumerate(unverified, start=1):
            st.markdown(
                f"**{index}. {song.get('song') or 'Unknown Song'}**"
            )

            if song.get("artist"):
                st.caption(f"Artist: {song['artist']}")

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

            st.divider()

    rejected = st.session_state.groq_rejected or []

    if rejected:
        st.caption(
            f"{len(rejected)} candidate(s) excluded "
            "because of verification concerns."
        )


# --------------------------------------------------
# DISPLAY SONG RECOGNITION RESULT
# --------------------------------------------------

def display_recognition_result(result):
    status = result.get("status")

    if status == "song_found":
        st.success("🎉 Song Found!")
        st.subheader(result.get("song") or "Unknown Song")

        source = result.get("source", "SQLite")

        if source == "AudD":
            st.caption("🌐 Identified using AudD")
        else:
            st.caption("💾 Identified using local SQLite")

        if result.get("artist"):
            st.write("🎤 **Artist:**", result["artist"])

        if result.get("album"):
            st.write("💿 **Album:**", result["album"])

        if source != "AudD":
            speed = result.get("detected_playback_speed")

            if speed is not None:
                st.write("🎚️ **Playback speed:**", f"{speed}x")

            position = result.get("start_time")

            if position is not None:
                st.write(
                    "⏱️ **Song position:**",
                    f"{position:.1f} seconds",
                )

        if source == "AudD":
            spotify = result.get("spotify") or {}
            apple_music = result.get("apple_music") or {}

            album = spotify.get("album") or {}
            images = album.get("images") or []

            if images and images[0].get("url"):
                st.image(images[0]["url"], width=250)

            spotify_url = (
                spotify.get("external_urls") or {}
            ).get("spotify")

            if spotify_url:
                st.link_button(
                    "🎧 Listen on Spotify",
                    spotify_url,
                )

            apple_url = apple_music.get("url")

            if apple_url:
                st.link_button(
                    "🍎 Listen on Apple Music",
                    apple_url,
                )

    elif status == "song_not_found":
        st.warning("🎵 No Song Found")

        st.write(
            "We couldn't identify the song using SQLite or AudD."
        )

        st.info(
            "You can still find similar music from your "
            "recording or discover songs by preference."
        )

    elif status == "online_recognition_error":
        st.warning(
            "Online recognition is temporarily unavailable."
        )
        st.write(result.get("message", ""))

    else:
        st.error(
            result.get("message", "Unable to process recording.")
        )


# --------------------------------------------------
# THREE OPTIONS
# --------------------------------------------------

def display_next_options():
    st.divider()
    st.subheader("🎶 What would you like to do next?")

    option = st.session_state.selected_option

    if option is None:
        if st.button(
            "🎵 1. Find Similar Songs",
            use_container_width=True,
        ):
            st.session_state.selected_option = "similar"
            st.rerun()

        if st.button(
            "🔎 2. Search by Music Preferences",
            use_container_width=True,
        ):
            st.session_state.selected_option = "discover"
            st.rerun()

        if st.button(
            "🏠 3. Exit",
            use_container_width=True,
        ):
            go_home()

        return

    if st.button("← Back to Options"):
        st.session_state.selected_option = None
        st.rerun()

    # OPTION 1: CYANITE
    if option == "similar":
        st.subheader("🎵 Similar Songs")

        st.write(
            "Cyanite will analyze your recording "
            "and find similar Spotify songs."
        )

        track_id = st.session_state.recommendation_track_id

        if not track_id:
            if st.button(
                "🎶 Analyze My Recording",
                type="primary",
            ):
                start_cyanite_analysis()

            return

        analysis = st.session_state.cyanite_result or {}
        status = analysis.get("status")

        if status == "analysis_ready":
            st.success("Cyanite analysis complete!")

            if st.session_state.similar_songs_result is None:
                if st.button(
                    "🎵 Show Top 5 Similar Songs",
                    type="primary",
                ):
                    fetch_similar_songs(track_id)

        elif status == "processing":
            st.info("Cyanite is still processing.")

            if st.button("🔄 Retry Processing"):
                retry_cyanite_analysis(track_id)

        elif status == "analysis_failed":
            st.error("Cyanite analysis failed.")

        else:
            st.info("Recording submitted to Cyanite.")

            if st.button("🔄 Check Analysis"):
                retry_cyanite_analysis(track_id)

        similar = st.session_state.similar_songs_result

        if similar:
            st.divider()
            display_similar_songs(similar)

    # OPTION 2: GROQ + TAVILY + VERIFICATION
    elif option == "discover":
        st.subheader("🔎 Discover Different Songs")

        st.write(
            "Tell TuneFinder what kind of songs you want."
        )

        with st.form("music_preference_form"):
            preference = st.text_input(
                "Your music preference",
                placeholder=(
                    "Example: Telugu romantic songs "
                    "featuring Nani in 2026"
                ),
            )

            submitted = st.form_submit_button(
                "🎵 Find Songs",
                type="primary",
            )

        if submitted:
            preference = preference.strip()

            if not preference:
                st.warning("Please enter a music preference.")
            else:
                discover_music(preference)

        display_groq_results()


# --------------------------------------------------
# MAIN APPLICATION
# --------------------------------------------------

st.title("🎵 TuneFinder")
st.subheader("Discover what's playing")

if st.session_state.screen == "home":
    st.info(
        "🎤🎶 Please record at least "
        "10 seconds of music! 🎵"
    )

    st.divider()

    audio = st.audio_input(
        "Tap the microphone to record music",
        sample_rate=22050,
        key=f"microphone_{st.session_state.recorder_version}",
    )

    if audio is not None:
        audio_bytes = audio.getvalue()

        st.audio(audio)

        if st.session_state.recording_bytes != audio_bytes:
            clear_workflow()
            st.session_state.recording_bytes = audio_bytes

        try:
            duration = get_audio_duration(audio_bytes)
        except (wave.Error, EOFError, ZeroDivisionError):
            duration = 0
            st.error("Unable to read the recording.")

        st.caption(
            f"🎙️ Recording duration: {duration:.1f} seconds"
        )

        if duration < MIN_DURATION:
            st.warning(
                "Please record at least 10 seconds of music. "
                "Returning to the home page in 3 seconds..."
            )
            time.sleep(3)
            go_home()

        if st.button(
            "🔍 Identify Song",
            type="primary",
            disabled=duration < MIN_DURATION,
            use_container_width=True,
        ):
            identify_song(audio_bytes)

elif st.session_state.screen == "results":
    result = st.session_state.recognition_result

    if not result:
        st.warning("No recognition result is available.")

        if st.button("🏠 Return Home"):
            go_home()

    else:
        display_recognition_result(result)

        if result.get("status") in {
            "song_found",
            "song_not_found",
            "online_recognition_error",
        }:
            display_next_options()
        else:
            if st.button("🏠 Return Home"):
                go_home()
