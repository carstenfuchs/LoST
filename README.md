# LoST

A terminal solution for time recording, access control and employee
communication with touch display and RFID reader support.

LoST is a frontend software that implements the user interface of a time
recording terminal. Its features include:

  - displaying the graphical user interface
  - handling touch screen and other input
  - reading RFID tags
  - communication with the backend server
  - displaying the server feedback

Although primarily developed for a specific backend server implementation as
described below, LoST is intended to be generically useful: It runs on a wide
range of hardware, supports all major operating systems, can use many input
devices including barcode scanners and RFID readers and its communication
interface to the backend server is straightforward and easy to customize.

The name LoST is an acronym for “Lori Stempeluhr Terminal”.
Lori is the backend server software that LoST is primarily being developed for,
“Stempeluhr Terminal” is the german term for “time recording terminal”.

Note that Lori is not a part of LoST and is not publicly available. However,
LoST comes with its own minimal backend server implementation that is used for
development and testing and that can be used as a reference or starting point
for your own backend server.
