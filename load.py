import sys
import tkinter as tk
from ttkHyperlinkLabel import HyperlinkLabel
import webbrowser
import requests
import json
from l10n import Locale
from theme import theme
import plug

import logging
import os

from config import appname
import threading


"""
Triggered by Approach Settlement event
{ 
    "timestamp":"2023-01-07T20:39:05Z", 
    "event":"ApproachSettlement", 
    "Name":"$Ancient:#index=1;", 
    "Name_Localised":"Ancient Ruins (1)", 
    "SystemAddress":3515254557027, 
    "BodyID":13, 
    "BodyName":"Synuefe XR-H d11-102 1 b", 
    "Latitude":-46.576923, "Longitude":133.985107 
}

"""

this = sys.modules[__name__]

# This could also be returned from plugin_start3()
plugin_name = os.path.basename(os.path.dirname(__file__))

# A Logger is used per 'found' plugin to make it easy to include the plugin's
# folder name in the logging output format.
# NB: plugin_name here *must* be the plugin's folder name as per the preceding
#     code, else the logger won't be properly set up.
logger = logging.getLogger(f"{appname}.{plugin_name}")

# If the Logger has handlers then it was already set up by the core code, else
# it needs setting up here.
if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()

    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(
        f"%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s"
    )
    logger_formatter.default_time_format = "%Y-%m-%d %H:%M:%S"
    logger_formatter.default_msec_format = "%s.%03d"
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)


class postData(threading.Thread):
    def __init__(self, url, payload):
        threading.Thread.__init__(self)
        self.url = url
        self.payload = payload

    def run(self):
        logger.debug(self.url + self.payload)
        r = requests.get(self.url + self.payload)
        if not r.status_code == requests.codes.ok:
            logger.error(self.payload)
            headers = r.headers
            contentType = str(headers["content-type"])
            if "json" in contentType:
                logger.error(json.dumps(r.content))
            else:
                logger.error(r.content)
            logger.error(r.status_code)
        else:
            logger.debug("emitter.post success")


def post(url, payload):
    postData(url, payload).start()


class cycle:

    def __init__(self, list):
        self.values = list
        self.index = 0

    def current(self):
        return self.values[self.index]

    def next(self):
        self.index += 1
        self.index = self.index % len(self.values)
        return self.values[self.index]

    def prev(self):
        self.index -= 1
        self.index = self.index % len(self.values)
        return self.values[self.index]

    def set(self, value):
        if value in self.values:
            retval = value
            while self.current() != value:
                retval = self.next()
            return retval
        else:
            return None


def plugin_start3(plugin_dir):
    plugin_start(plugin_dir)


def plugin_start(plugin_dir):
    """
    Load this plugin into EDMC
    """
    this.plugin_dir = plugin_dir
    logger.info("I am loaded! My plugin folder is {}".format(plugin_dir))
    return "Test"


def destroy_titles(event=None):
    if this.startup:

        this.title.destroy()
        this.status.destroy()
        if not this.active:
            this.frame.grid_remove()
    this.startup = False


def create(type="alpha"):

    this.active = True
    destroy_titles()
    this.frame.grid()
    this.types.set(type)
    this.ruin = tk.Label(this.frame)
    this.ruin.grid(row=1, column=0, rowspan=3)
    this.ruin.bind("<Button-1>", ruin_next)
    this.ruin.bind("<Button-3>", ruin_prev)
    this.ruin_image = tk.PhotoImage(
        file=os.path.join(this.plugin_dir, "images", f"{this.types.current()}.png")
    )
    this.ruin["image"] = this.ruin_image

    this.desc = tk.Label(this.frame, text=this.types.current().title())
    this.desc.grid(row=1, column=1)

    this.submit = tk.Button(this.frame, text="Submit", foreground="green")
    this.submit.bind("<Button-1>", submit_event)
    this.submit.grid(row=2, column=1)

    this.dismiss = tk.Button(this.frame, text="Dismiss", foreground="red")
    this.dismiss.bind("<Button-1>", destroy)
    this.dismiss.grid(row=3, column=1)

    theme.update(this.frame)


def ruin_next(event=None):
    this.ruin_image = tk.PhotoImage(
        file=os.path.join(this.plugin_dir, "images", f"{this.types.next()}.png")
    )
    this.ruin["image"] = this.ruin_image
    this.desc["text"] = this.types.current().title()


def ruin_prev(event=None):
    this.ruin_image = tk.PhotoImage(
        file=os.path.join(this.plugin_dir, "images", f"{this.types.prev()}.png")
    )
    this.ruin["image"] = this.ruin_image
    this.desc["text"] = this.types.current().title()


def destroy(event=None):
    this.ruin.destroy()
    this.desc.destroy()
    this.submit.destroy()
    this.submit.destroy()
    this.dismiss.destroy()
    this.frame.grid_remove()


def submit_event(event=None):
    logger.info("submitting")
    if not this.testing:

        # url = f"https://docs.google.com/forms/d/e/1FAIpQLSfS2GwRdzqYfxbSrjU7hgJckDNJbHISgiHp1gWFEHXkrTmhXw/viewform?usp=pp_url&entry.2021507511={this.cmdr}&entry.1090208472={this.system}&entry.2118720333={this.entry.get('BodyName')}&entry.865635247={this.types.current().title()}"
        url = "https://docs.google.com/forms/d/e/1FAIpQLSfS2GwRdzqYfxbSrjU7hgJckDNJbHISgiHp1gWFEHXkrTmhXw/formResponse?usp=pp_url"

        payload = (
            f"&entry.2021507511={this.cmdr}"
            f"&entry.1090208472={this.system}"
            f"&entry.2118720333={this.entry.get('BodyName')}"
            f"&entry.1117125548={this.types.current().title()}"
            f"&entry.865635247={get_index(this.entry.get('Name'))}"
        )

        post(url, payload)

    destroy()


def get_index(value):
    a = []
    a = value.split("#")
    if len(a) == 2:
        dummy, c = value.split("#")
        dummy, index_id = c.split("=")
        index_id = index_id[:-1]
        return index_id
    return None


def plugin_app(parent):
    """
    Create a pair of TK widgets for the EDMC main window
    """
    this.frame = tk.Frame(parent)
    this.frame.columnconfigure(2, weight=1)
    # By default widgets inherit the current theme's colors
    this.title = tk.Label(this.frame, text="Ruins:")
    this.status = tk.Label(this.frame, text="Started", foreground="green")
    this.title.grid(row=0, column=0, sticky="NSEW")
    this.status.grid(row=0, column=1, sticky="NSEW")
    this.frame.after(30000, destroy_titles)

    this.types = cycle(["alpha", "beta", "gamma"])

    this.active = False
    this.startup = True

    return this.frame


def test_ruin(message):
    a = message.split(" ")
    if len(a) == 4:
        create(a[3])
    else:
        create()


def journal_entry(cmdr, is_beta, system, station, entry, state):
    rtest = (
        entry.get("event") == "SendText"
        and entry.get("Message")
        and "test ruin scanner" in entry.get("Message")
    )

    detected = entry.get(
        "event"
    ) == "ApproachSettlement" and "$Ancient:#index=" in entry.get("Name")

    if rtest:
        this.testing = True
        test_ruin(entry.get("Message"))

    if detected:
        this.testing = False
        this.entry = entry
        this.cmdr = cmdr
        this.system = system
        this.is_beta = is_beta
        create()
