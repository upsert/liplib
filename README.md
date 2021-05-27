# liplib

Interface module for Lutron Integration Protocol (LIP) over Telnet.

This module connects to a Lutron hub through the Telnet interface which must be enabled through the integration menu in the Lutron mobile app.

Supported bridges / main repeaters / controllers:
- [Lutron Caseta](http://www.casetawireless.com) Smart Bridge **PRO** (L-BDGPRO2-WH)
- [Radio Ra2 Select](http://www.lutron.com/en-US/Products/Pages/WholeHomeSystems/RA2Select/Overview.aspx) Main Repeater (RR-SEL-REP-BL or RR-SEL-REP2S-BL)
- Radio Ra2
- Homeworks QS

Other bridges / main repeaters that use the Lutron Integration Protocol (e.g. Quantum, Athena, myRoom) should also work with this library, but are untested.

This module is designed to use selected commands from the [Lutron Integration Protocol](http://www.lutron.com/TechnicalDocumentLibrary/040249.pdf). Not all features documented in the protocol are supported by this module. If you implement an extension, please submit a pull request.

In addition to sending and receiving commands, a function is provided to process a JSON Integration Report obtained by a user from the Lutron mobile app.

An interface to the obsolete Lutron Homeworks Illumination system is [available here](https://github.com/dulitz/porter/blob/main/illiplib.py). It is drop-in compatible with this interface.

Authors:
upsert (https://github.com/upsert)

Based on 'Casetify' from jhanssen
https://github.com/jhanssen/home-assistant/tree/caseta-0.40

Note:
This module is not endorsed or affiliated with Lutron Electronics Inc.