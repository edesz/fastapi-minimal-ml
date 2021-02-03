#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Verification of handling invalid requests."""


import json
import logging
import os
from urllib.parse import urljoin

import pandas as pd
import requests

import api_dummy_data_loader as adl

pd.set_option("display.max_columns", 5000)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    ENV_PORT = int(os.environ.get("PORT", 8050))
    # SERVICE_NAME = os.environ.get("SERVICE_NAME", "api-db")  # inside container
    HOST_URL = "0.0.0.0"
    HOST_PORT = f"http://{HOST_URL}:{ENV_PORT}"  # local
    # HOST_PORT = f"http://{SERVICE_NAME}:{ENV_PORT}"  # inside container

    PROJ_ROOT_DIR = os.path.abspath(os.getcwd())
    dummy_data_filepath = os.path.join(PROJ_ROOT_DIR, "dummy_url_inputs.json")
    _, multi_obs_list = adl.get_dummy_url_data(dummy_data_filepath)

    # Create user and Generate token
    USERNAME = os.environ.get("USERNAME", "tom")
    PASSWORD = os.environ.get("PASSWORD", "mythirdsecret")
    response_dict = adl.create_user(USERNAME, PASSWORD, HOST_PORT)
    # print(response_dict)

    token = {
        "access_token": response_dict["access_token"],
        "token_type": "bearer",
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{token['token_type']} {token['access_token']}",
    }

    # Predict Species
    url = urljoin(f"{HOST_PORT}/api/v1/topics/", "predict").lower()
    r = requests.post(
        url,
        data=json.dumps(multi_obs_list),
        headers=headers,
    )
    assert r.status_code == 200
    r_text = json.loads(r.text)
    assert list(r_text) == [
        "msg",
        "duplicate_predictions_posted",
        "current_user",
    ]
    assert len(list(r_text["duplicate_predictions_posted"])) == 1
    assert r_text["current_user"] == USERNAME

    # Read Predictions
    url = urljoin(f"{HOST_PORT}/api/v1/topics/", "read_predictions").lower()
    r = requests.get(url, headers=headers)
    r_text = json.loads(r.text)
    assert r.status_code == 200
    assert len(r_text["msg"]) >= len(multi_obs_list)
    assert list(r_text) == ["msg", "current_user"]
    assert list(r_text["msg"][0].keys()) == ["id", "url", "text", "user_id"]
    assert r_text["current_user"] == USERNAME

    # Read Prediction
    url = urljoin(
        f"{HOST_PORT}/api/v1/topics/",
        "read_prediction?url={multi_obs_list[0]['url']}",
    ).lower()
    r = requests.get(url, headers=headers)
    r_text = json.loads(r.text)
    assert r.status_code == 200
    assert list(r_text) == ["msg", "current_user"]
    assert list(r_text["msg"][0].keys()) == ["id", "url", "text", "user_id"]
    assert r_text["current_user"] == USERNAME

    # Verify response of /auths/users/me GET endpoint with authentication
    url = urljoin(f"{HOST_PORT}/api/v1/auths/users/", "me").lower()
    r = requests.get(url, headers=headers)
    assert r.status_code == 200
    assert list(json.loads(r.text)) == ["username", "password_hash"]

    # Verify response of /auths/user/{user_id} GET endpoint with authentication
    id = 3
    url = urljoin(f"{HOST_PORT}/api/v1/auths/user/", str(id)).lower()
    r = requests.get(url, headers=headers)
    assert r.status_code == 200
    r_text = json.loads(r.text)
    assert list(r_text) == ["msg", "current_user"]
    assert list(r_text["msg"]) == ["id", "username", "password_hash"]
    assert r_text["msg"]["username"] == USERNAME
    assert r_text["current_user"] == USERNAME

    # Verify response of /users GET endpoint with authentication
    url = urljoin(f"{HOST_PORT}/api/v1/auths/", "users").lower()
    r = requests.get(url, headers=headers)
    r_text = json.loads(r.text)
    assert r.status_code == 200
    assert list(r_text) == ["msg", "current_user"]
    assert list(r_text["msg"][0].keys()) == ["id", "username", "password_hash"]
    assert len(r_text["msg"]) == 3
    assert r_text["current_user"] == USERNAME
