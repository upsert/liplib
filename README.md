# liplib

Interface module for Lutron Integration Protocol (LIP) over Telnet.

This module connects to a Lutron hub through the Telnet interface which must be enabled through the integration menu in the Lutron mobile app.

Supported bridges / main repeaters:
- [Lutron Caseta](http://www.casetawireless.com) Smart Bridge **PRO** (L-BDGPRO2-WH)
- [Ra2 Select](http://www.lutron.com/en-US/Products/Pages/WholeHomeSystems/RA2Select/Overview.aspx) Main Repeater (RR-SEL-REP-BL or RR-SEL-REP2S-BL)

Other bridges / main repeaters that use the Lutron Integration Protocol (e.g. Radio Ra2, HomeWorks QS) may also work with this library, but are untested.

This module is designed to use selected commands from the [Lutron Integration Protocol](http://www.lutron.com/TechnicalDocumentLibrary/040249.pdf). The command set most closely resembles RadioRa 2, but not all features listed for RadioRa 2 are supported.

In addition to sending and receiving commands, a function is provided to process a JSON Integration Report obtained by a user from the Lutron mobile app.

Authors:
upsert (https://github.com/upsert)

Based on 'Casetify' from jhanssen
https://github.com/jhanssen/home-assistant/tree/caseta-0.40

Note:
This module is not endorsed or affiliated with Lutron Electronics Inc.