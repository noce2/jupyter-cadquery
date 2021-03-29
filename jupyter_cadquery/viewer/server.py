from datetime import datetime
from time import localtime
import os
import signal
import threading

import asyncio
from watchgod import awatch


from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import ipywidgets as widgets
from IPython.display import display, clear_output

from jupyter_cadquery.cad_display import CadqueryDisplay
from jupyter_cadquery.cadquery.cad_objects import from_assembly
from ..utils.serializer import Serializer

CAD_DISPLAY = None
HTTPD = None
LOG_OUTPUT = None
WATCHER = None


def log(typ, *msg):
    ts = datetime(*localtime()[:6]).isoformat()
    prefix = f"{ts} ({typ}) "
    if LOG_OUTPUT is not None:
        LOG_OUTPUT.append_stdout(prefix + " ".join(msg) + "\n")
    else:
        print(prefix, *msg)


def info(*msg):
    log("I", *msg)


def warn(*msg):
    log("W", *msg)


def error(*msg):
    log("E", *msg)


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
        info("GET request: %s" % str(self.path))
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
            info("POST request: %s (content-length=%s)" % (parsed_url.path, len(post_data)))
            info("Params: %s" % params)
        except Exception as ex:
            msg = "Parsing parameters failed: %s" % str(ex)
            warn(msg)

        try:
            with open(".jcq_serialized.tar.gz", "wb") as fd:
                fd.write(post_data)
            assy = Serializer().deserialize()
            info("Assembly deserialized %s" % assy.name)
        except Exception as ex:
            msg = "Storing POST data failed: %s" % str(ex)
            error(msg)
            self.reply(msg)
            return

        try:
            part_group = from_assembly(assy, assy)
            info("Assembly converted to PartGroup")
        except Exception as ex:
            msg = "Converting of assembly to PartGroup failed: %s" % str(ex)
            error(msg)
            self.reply(msg)
            return

        try:
            mapping = part_group.to_state()
            shapes = part_group.collect_mapped_shapes(mapping)
            tree = part_group.to_nav_dict()
            CAD_DISPLAY.add_shapes(shapes, mapping, tree, **params)
            info("Assembly view updated")
        except Exception as ex:
            msg = "Showing of objects failed: %s" % str(ex)
            error(msg)
            self.reply(msg)
            return

        self.reply("Done")


def stop_viewer():
    if HTTPD is not None:
        try:
            info("Stopping httpd...")
            HTTPD.shutdown()
            HTTPD.server_close()
            info("... httpd stopped\n")
            if CAD_DISPLAY is not None and CAD_DISPLAY.info is not None:
                CAD_DISPLAY.info.add_html("<b>HTTP server stopped</b>")
        except Exception as ex:
            error("Exception %s" % ex)


def start_viewer(server=False):
    global CAD_DISPLAY, LOG_OUTPUT, WATCHER

    CAD_DISPLAY = CadqueryDisplay()
    cad_view = CAD_DISPLAY.create()
    width = CAD_DISPLAY.cad_width + CAD_DISPLAY.tree_width + 6
    LOG_OUTPUT = widgets.Output(layout=widgets.Layout(height="400px", overflow="scroll"))

    def listen():
        global HTTPD
        server_address = ("", 8842)
        httpd = HTTPServer(server_address, Handler)
        HTTPD = httpd
        try:
            info("Starting httpd")
            httpd.serve_forever()
        except KeyboardInterrupt:
            info("Stopping httpd...")
            httpd.shutdown()
            httpd.server_close()
            info("... httpd stopped\n")
        except Exception as ex:
            error("Exception %s" % ex)

    async def watch():
        async for changes in awatch("/tmp/jcq"):
            change, filename = list(changes)[0]
            info(change.name, filename)

    clear_output()
    log_view = widgets.Accordion(children=[LOG_OUTPUT], layout=widgets.Layout(width=f"{width}px"))
    log_view.set_title(0, "Log")
    log_view.selected_index = None
    display(widgets.VBox([cad_view, log_view]))

    stop_viewer()

    if server:
        thread = threading.Thread(target=listen)
        thread.setDaemon(True)
        thread.start()
        CAD_DISPLAY.info.add_html("<b>HTTP server started</b>")

    else:
        if WATCHER is not None:
            WATCHER.cancel()
        WATCHER = asyncio.run_coroutine_threadsafe(watch(), loop=asyncio.get_event_loop())

        CAD_DISPLAY.info.add_html("<b>File watcher started</b>")
