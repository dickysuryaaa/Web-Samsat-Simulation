import midtransclient
from flask import current_app


def get_snap_client():
    return midtransclient.Snap(
        is_production=current_app.config["MIDTRANS_IS_PRODUCTION"],
        server_key=current_app.config["MIDTRANS_SERVER_KEY"],
        client_key=current_app.config["MIDTRANS_CLIENT_KEY"],
    )


def get_core_client():
    return midtransclient.CoreApi(
        is_production=current_app.config["MIDTRANS_IS_PRODUCTION"],
        server_key=current_app.config["MIDTRANS_SERVER_KEY"],
        client_key=current_app.config["MIDTRANS_CLIENT_KEY"],
    )

