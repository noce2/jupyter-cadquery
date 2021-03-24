import logging
import os
import signal
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import requests
from IPython.display import display, clear_output

from jupyter_cadquery.cad_display import CadqueryDisplay
from jupyter_cadquery.cadquery.cad_objects import from_assembly
from ..utils.serializer import Serializer

CAD_DISPLAY = None


class Handler(BaseHTTPRequestHandler):
    def reply(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def _params(self, query):
        def cast(val):
            try:
                return int(val)
            except:
                ...
            try:
                return float(val)
            except:
                ...
            if val in ("True", "False", "true", "false"):
                return val.lower() == "true"
            else:
                return val

        return {k: cast(v) for (k, v) in [q.split("=") for q in query.split("&")]}

    def do_GET(self):
        logging.info("GET request: %s", str(self.path))
        if self.path == "/stop":
            self.reply("Stopped")
            os.kill(os.getpid(), signal.SIGINT)
        elif self.path == "/status":
            CAD_DISPLAY.info.add_html("<b>Running</b>")
            self.reply("Running")
        else:
            self.reply("Ignored")

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        try:
            parsed_url = urlparse(self.path)
            params = self._params(parsed_url.query)
            logging.info("POST request: %s (content-length=%s)", parsed_url.path, len(post_data))
            logging.info("Params: %s", params)
        except Exception as ex:
            msg = "Parsing parameters failed: %s", str(ex)
            logging.warn(msg)

        try:
            with open(".jcq_serialized.tar.gz", "wb") as fd:
                fd.write(post_data)
            assy = Serializer().deserialize()
            logging.info("Assembly deserialized %s", assy.name)
        except Exception as ex:
            msg = "Storing POST data failed: %s", str(ex)
            logging.error(msg)
            self.reply(msg)
            return

        try:
            part_group = from_assembly(assy, assy)
            logging.info("Assembly converted to PartGroup")
        except Exception as ex:
            msg = "Converting of assembly to PartGroup failed: %s", str(ex)
            logging.error(msg)
            self.reply(msg)
            return

        try:
            mapping = part_group.to_state()
            shapes = part_group.collect_mapped_shapes(mapping)
            tree = part_group.to_nav_dict()
            CAD_DISPLAY.add_shapes(shapes, mapping, tree, **params)
            logging.info("Assembly view updated")
        except Exception as ex:
            msg = "Showing of objects failed: %s", str(ex)
            logging.error(msg)
            self.reply(msg)
            return

        self.reply("Done")


def start(start_server=True):
    global CAD_DISPLAY
    CAD_DISPLAY = CadqueryDisplay()

    def listen():
        server_address = ("", 8842)
        httpd = HTTPServer(server_address, Handler)
        try:
            logging.info("Starting httpd\n")
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Stopping httpd...\n")
            httpd.shutdown()
            httpd.server_close()
            logging.info("... httpd stopped\n")
        except Exception as ex:
            logging.info("Exception %s", ex)

    if start_server:
        logging.basicConfig(filename=".jcq-viewer.log", level=logging.INFO)
        logging.info("Starting ...")
        thread = threading.Thread(target=listen)
        thread.start()
        logging.info("... started")

    clear_output()
    display(CAD_DISPLAY.create())
    CAD_DISPLAY.info.add_html("<b>HTTP server started</b>")
