#
# Copyright 2021 Bernhard Walter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import cadquery as cq
import requests

from ..utils.serializer import Serializer
from .server import start as start_viewer

SERVER = "localhost"
API_PORT = 8842
TOLERANCE = 0.1
ANGULAR_TOLERANCE = 0.1


def set_server(server="localhost", port=8842):
    global SERVER, API_PORT
    SERVER = server
    API_PORT = port


def set_tolerance(tolerance=0.1, angularTolerance=0.1):
    global TOLERANCE, ANGULAR_TOLERANCE
    TOLERANCE = tolerance
    ANGULAR_TOLERANCE = angularTolerance


def show_object(assy, reset=True, tolerance=0.01, angularTolerance=0.01):
    archive = Serializer().serialize(assy, tolerance=tolerance, angular_tolerance=angularTolerance)
    data = open(archive, "rb").read()
    headers = {"Content-Type": "application/binary"}
    params = f"?reset={reset}"
    requests.post(f"http://{SERVER}:{API_PORT}/{params}", data=data, headers=headers)
