import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from flask import current_app


def create_flow():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = current_app.config["OAUTHLIB_INSECURE_TRANSPORT"]
    flow = Flow.from_client_secrets_file(
        current_app.config["GOOGLE_CLIENT_SECRETS_FILE"],
        scopes=current_app.config["GOOGLE_SCOPES"],
        redirect_uri=current_app.config["GOOGLE_REDIRECT_URI"],
    )
    return flow


def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


def dict_to_credentials(data):
    return Credentials(
        token=data["token"],
        refresh_token=data.get("refresh_token"),
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"],
    )
