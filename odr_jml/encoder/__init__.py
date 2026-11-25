"""Pure-Python DAB Journaline encoder (ETSI TS 102 979).

jml      JML objects: header, content section, escape sequences, data sections, deflate
toc      TOC management data blocks
msc      MSC data groups and DAB packet mode
service  validation, revision tracking and the weighted carousel for a whole service
decode   an independent decoder used for the receiver preview and tests
"""
