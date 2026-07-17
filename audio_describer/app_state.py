# audio_describer/app_state.py
import threading

# A thread-safe event object that will be used to signal shutdown to all parts of the application.
# When this event is set, any long-running background tasks should terminate themselves.
shutdown_event = threading.Event()