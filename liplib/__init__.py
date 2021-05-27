"""
Interface module for Lutron Integration Protocol (LIP).

This module connects to a Lutron hub through the tcp/23 ("telnet") interface which
must be enabled through the integration menu in the Lutron mobile app.

Authors:
upsert (https://github.com/upsert)

Based on Casetify from jhanssen
https://github.com/jhanssen/home-assistant/tree/caseta-0.40
"""

import asyncio
import json
import logging
import re
from enum import IntEnum

CONF_ID = "id"
CONF_NAME = "name"
CONF_TYPE = "type"
CONF_SCENE_ID = "scene_id"
CONF_AREA_NAME = "area_name"
CONF_BUTTONS = "buttons"

_LOGGER = logging.getLogger(__name__)

def load_integration_report(integration_report) -> list:
    """Process a JSON integration report and return a list of devices.

    Each returned device will have an 'id', 'name', 'type' and optionally
    a list of button IDs under 'buttons' for remotes
    and an 'area_name' attribute if the device is assigned to an area.

    To generate an integration report in the Lutron (Radio Ra2 Select) app,
    click the gear, then Advanced, then "Send Integration Report."
    """
    devices = []
    lipidlist = integration_report.get("LIPIdList")
    assert lipidlist, integration_report

    # lights and switches are in Zones
    for zone in lipidlist.get("Zones", []):
        device_obj = {CONF_ID: zone["ID"],
                      CONF_NAME: zone["Name"],
                      CONF_TYPE: "light"}
        name = zone.get("Area", {}).get("Name", "")
        if name:
            device_obj[CONF_AREA_NAME] = name
        devices.append(device_obj)

    # remotes are in Devices, except ID 1 which is the bridge itself
    for device in lipidlist.get("Devices", []):
        # extract scenes from integration ID 1 - the smart bridge
        if device["ID"] == 1:
            for button in device.get("Buttons", []):
                if not button["Name"].startswith("Button "):
                    _LOGGER.info("Found scene %d, %s", button["Number"], button["Name"])
                    devices.append({CONF_ID: device["ID"],
                                    CONF_NAME: button["Name"],
                                    CONF_SCENE_ID: button["Number"],
                                    CONF_TYPE: "scene"})
        else:
            device_obj = {CONF_ID: device["ID"],
                          CONF_NAME: device["Name"],
                          CONF_TYPE: "sensor",
                          CONF_BUTTONS: [b["Number"] for b in device.get("Buttons", [])]}
            name = device.get("Area", {}).get("Name", "")
            device_obj[CONF_AREA_NAME] = name
            devices.append(device_obj)

    return devices


# pylint: disable=too-many-instance-attributes
class LipServer:
    """Communicate with a Lutron bridge, repeater, or controller."""

    READ_SIZE = 1024
    DEFAULT_USER = b"lutron"
    DEFAULT_PASSWORD = b"integration"
    DEFAULT_PROMPT = b"GNET> "
    LOGIN_PROMPT = b"login: "
    RESPONSE_RE = re.compile(b"~([A-Z]+),([0-9.]+),([0-9.]+),([0-9.]+)\r\n")
    OUTPUT = "OUTPUT"
    DEVICE = "DEVICE"

    class Action(IntEnum):
        """Action numbers for the OUTPUT command in the Lutron Integration Protocol."""

        SET      = 1    # Get or Set Zone Level
        RAISING  = 2    # Start Raising
        LOWERING = 3    # Start Lowering
        STOP     = 4    # Stop Raising/Lowering

        PRESET   = 6    # SHADEGRP for Homeworks QS

    class Button(IntEnum):
        """Action numbers for the DEVICE command in the Lutron Integration Protocol."""

        PRESS     = 3
        RELEASE   = 4
        HOLD      = 5   # not returned by Caseta or Radio Ra 2 Select
        DOUBLETAP = 6   # not returned by Caseta or Radio Ra 2 Select

        LEDSTATE = 9    # "Button" is a misnomer; this queries LED state

    class State(IntEnum):
        """Connection state values."""

        Closed = 1
        Opening = 2
        Opened = 3

    def __init__(self):
        """Initialize the library."""
        self._read_buffer = b""
        self._read_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._state = LipServer.State.Closed
        self._host = None
        self._port = 23
        self._username = LipServer.DEFAULT_USER
        self._password = LipServer.DEFAULT_PASSWORD
        self.prompt = LipServer.DEFAULT_PROMPT
        self.reader, self.writer = None, None

    def is_connected(self) -> bool:
        """Return if the connection is open."""
        return self._state == LipServer.State.Opened

    async def open(self, host, port=23, username=DEFAULT_USER,
                   password=DEFAULT_PASSWORD):
        """Open a telnet connection to the bridge."""
        async with self._read_lock:
            async with self._write_lock:
                if self._state != LipServer.State.Closed:
                    return
                self._state = LipServer.State.Opening

                self._host = host
                self._port = port
                self._username = username
                self._password = password

                def cleanup(err):
                    _LOGGER.warning(f"error opening connection to Lutron {host}:{port}: {err}")
                    self._state = LipServer.State.Closed

                # open connection
                try:
                    connection = await asyncio.open_connection(host, port)
                except OSError as err:
                    return cleanup(err)

                self.reader = connection[0]
                self.writer = connection[1]

                # do login
                if await self._read_until(self.LOGIN_PROMPT) is False:
                    return cleanup('no login prompt')
                self.writer.write(username + b"\r\n")
                await self.writer.drain()
                if await self._read_until(b"password: ") is False:
                    return cleanup('no password prompt')
                self.writer.write(password + b"\r\n")
                await self.writer.drain()
                if await self._read_until(self.prompt) is False:
                    return cleanup('login failed')

                self._state = LipServer.State.Opened

    async def _read_until(self, value):
        """Read until a given value is reached. Value may be regex or bytes."""
        while True:
            if hasattr(value, "search"):
                # detected regular expression
                match = value.search(self._read_buffer)
                if match:
                    self._read_buffer = self._read_buffer[match.end():]
                    return match
            else:
                assert isinstance(value, bytes), value
                where = self._read_buffer.find(value)
                if where != -1:
                    until = self._read_buffer[:where+len(value)]
                    self._read_buffer = self._read_buffer[where + len(value):]
                    return until
            try:
                read_data = await self.reader.read(LipServer.READ_SIZE)
                if not len(read_data):
                    _LOGGER.warning("bridge disconnected")
                    return False
                self._read_buffer += read_data
            except OSError as err:
                _LOGGER.warning(f"error reading from the bridge: {err}")
                return False

    async def read(self):
        """Return a list of values read from the Telnet interface."""
        async with self._read_lock:
            if self._state != LipServer.State.Opened:
                return None, None, None, None
            match = await self._read_until(LipServer.RESPONSE_RE)
            if match is not False:
                # 1 = mode, 2 = integration number,
                # 3 = action number, 4 = value
                try:
                    return match.group(1).decode("ascii"), \
                           int(match.group(2)), int(match.group(3)), \
                           float(match.group(4))
                except ValueError:
                    _LOGGER.warning(f"could not parse {match.group(0)}")
        if match is False:
            # attempt to reconnect
            _LOGGER.info(f"Reconnecting to the bridge {self._host}")
            self._state = LipServer.State.Closed
            await self.open(self._host, self._port, self._username,
                            self._password)
        return None, None, None, None

    async def write(self, mode, integration, action, *args, value=None):
        """Write a list of values to the bridge."""
        if hasattr(action, "value"):
            action = action.value
        async with self._write_lock:
            if self._state != LipServer.State.Opened:
                return
            data = f"#{mode},{integration},{action}"
            if value is not None:
                data += f",{value}"
            for arg in args:
                if arg is not None:
                    data += f",{arg}"
            try:
                self.writer.write((data + "\r\n").encode("ascii"))
                await self.writer.drain()
            except OSError as err:
                _LOGGER.warning(f"Error writing to the bridge: {err}")


    async def query(self, mode, integration, action):
        """Query a device to get its current state. Does not handle LED queries."""
        if hasattr(action, "value"):
            action = action.value
        _LOGGER.debug(f"Sending query {mode}, integration {integration}, action {action}")
        async with self._write_lock:
            if self._state != LipServer.State.Opened:
                return
            self.writer.write(f"?{mode},{integration},{action}\r\n".encode())
            await self.writer.drain()

    async def ping(self):
        """Ping the interface to keep the connection alive."""
        async with self._write_lock:
            if self._state != LipServer.State.Opened:
                return
            self.writer.write(b"#PING\r\n")
            await self.writer.drain()

    async def logout(self):
        """Close the connection to the bridge."""
        async with self._write_lock:
            if self._state != LipServer.State.Opened:
                return
            self.writer.write(b"LOGOUT\r\n")
            await self.writer.drain()
            self._state = LipServer.State.Closed
