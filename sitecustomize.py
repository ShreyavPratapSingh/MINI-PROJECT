import pyngrok.ngrok as pyngrok_ngrok


def _safe_connect(*args, **kwargs):
    print("[pyngrok] Using local fallback because no ngrok auth token is configured.")
    return "http://127.0.0.1:5000"


pyngrok_ngrok.connect = _safe_connect
