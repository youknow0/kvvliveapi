#!/usr/bin/env python
# author: Clemens "Nervengift"

import urllib2
from urllib import quote_plus,urlencode
import json
import re
import sys

API_KEY = "377d840e54b59adbe53608ba1aad70e8"
API_BASE = "http://live.kvv.de/webapp/"

class Stop:
    def __init__(self, name, stop_id, lat, lon):
        self.name = name
        self.stop_id = stop_id
        self.lat = lat
        self.lon = lon

    def from_json(json):
        return Stop(json["name"], json["id"], json["lat"], json["lon"])


class Departure:
    def __init__(self, route, destination, direction, time, lowfloor, realtime, traction):
        self.route = route
        self.destination = destination
        self.direction = direction
        self.time = time #TODO: to timestamp?
        self.lowfloor = lowfloor
        self.realtime = realtime
        self.traction = traction

    def from_json(json):
        time = json["time"]
        if time == "0":
            time = "sofort"
        return Departure(json["route"], json["destination"], json["direction"], time, json["lowfloor"], json["realtime"], json["traction"])

    def pretty_format(self):
        return self.time + ("  " if self.realtime else "* ") + (" " if self.time != "sofort" else "") + self.route + " " + self.destination


def _query(path, params = {}):
    params["key"] = API_KEY
    url = API_BASE + path + "?" + urlencode(params)
    #print(url)
    req = urllib.request.Request(url)

    #try:
    handle = urllib.request.urlopen(req)
    #except IOError as e:
    #    if hasattr(e, "code"):
    #        if e.code != 403:
    #            print("We got another error")
    #            print(e.code)
    #        else:
    #            print(e.headers)
    #            print(e.headers["www-authenticate"])
    #    return None; #TODO: Schoenere Fehlerbehandlung

    return json.loads(handle.read().decode())

def _search(query):
    json = _query(query)
    stops = []
    if json:
        for stop in json["stops"]:
            stops.append(Stop.from_json(stop))
    return stops

def search_by_name(name):
    """ Search for stops by name
        returns a list of Stop objects
    """
    return _search("stops/byname/" + quote_plus(name))

def search_by_latlon(lat, lon):
    """ Search for stops by latitude and longitude
        returns a list of Stop objectss
    """
    return _search("stops/bylatlon/" + lat + "/" + lon)

def search_by_stop_id(stop_id):
    """ Search for a stop by its stop_id
        returns a list that should contain only one stop
    """
    return [Stop.from_json(_query("stops/bystop/" + stop_id))]

def _get_departures(query, max_info=10):
    json = _query(query, {"maxInfo" : str(max_info)})
    departures = []
    if json:
        for dep in json["departures"]:
            departures.append(Departure.from_json(dep))
    return departures


def get_departures(stop_id, max_info=10):
    """ Return a list of Departure objects for a given stop stop_id
        optionally set the maximum number of entries 
    """
    return _get_departures("departures/bystop/" + stop_id, max_info)

def get_departures_by_route(stop_id, route, max_info=10):
    """ Return a list of Departure objects for a given stop stop_id and route
        optionally set the maximum number of entries 
    """
    return _get_departures("departures/byroute/" + route + "/" + stop_id, max_info)

def _errorstring(e):
    if hasattr(e, "code"):
        return {400: "invalid stop id or route",
                404: "not found"}.get(e.code, "http error " + str(e.code))
    else:
        return "unknown error"


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "search":
            if sys.argv[2].startswith("de:"):
                for stop in search_by_stop_id(sys.argv[2]):
                    print(stop.name + " (" + stop.stop_id + ")")
            else:
                for stop in search_by_name(sys.argv[2]):
                    print(stop.name + " (" + stop.stop_id + ")")
        elif len(sys.argv) == 4 and sys.argv[1] == "search":
            for stop in search_by_latlon(sys.argv[2], sys.argv[3]):
                print(stop.name + " (" + stop.stop_id + ")")
        elif len(sys.argv) == 3 and sys.argv[1] == "departures":
            for dep in get_departures(sys.argv[2]):
                print(dep.pretty_format())
        elif len(sys.argv) == 4 and sys.argv[1] == "departures":
            for dep in get_departures_by_route(sys.argv[2], sys.argv[3]):
                print(dep.pretty_format())
        else:
            print("No such command. Try \"search <name>/<stop_id>/<lat> <lon>\" or \"departures <stop stop_id> [<route>]\"")
    except IOError as e:
       print(_errorstring(e))
