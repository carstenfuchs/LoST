Program design
==============

Our terminals follow the *MVC design pattern*:

  - Class `Terminal` is the model,
  - event providers such as the smartcard reader and the GUI are the controllers,
  - the view is mainly the GUI, which is an observer of the model.

Other event providers (controllers) are incoming network messages and periodic
timers. Even more are conceivable, for example external buttons, fingerprint
sensors, speech input, etc.

Also additional views are possible, e.g. external lights, buzzers, door
openers, etc. Note that the GUI has a double role: It acts both as a controller
and as a view.

For implementing the views, we employ the *Observer design pattern*:
Controllers (e.g. the GUI) update the model (the terminal representation) which
in turn notifies its observers about the change so that they can update their
internal state.


Threading
---------

With Tkinter, GUI events occur and are handled in the main thread: Touching the
screen causes the "button click" handler to be run in the main thread. Thus,
the handler can directly update the terminal's state which in turn notifies all
observers about the change.

Most other event providers however sit in their own thread, waiting for events
to occur, e.g. the smartcard reader. Such threads cannot directly modify the
terminal's state and thus depend on putting a callback that implements the
update of the terminal into the `thread_queue`.


Variants
--------

Besides a variety of controllers and views, LoST also supports variants of
terminal implementations: For example, the terminals for office or logistics
staff may have different requirements and a different look and feel.

This raises the question how all other components in the program can cope with
variable implementations of terminals.

It seems that a two-fold approach might work well: We need an abstract terminal
base class `BaseTerminal` from with concrete terminals such as `OfficeTerminal`
derive.

  - Most components, for example the smartcard reader, should then be able to
    fully function with the only the `BaseTerminal`.
  - Component that are more complex and specific, such as the GUI, should be
    re-implemented or also derived from their own base class in order to be
    able to exploit all the specifics.


Tests
-----

TODO: Revise the section!

# Kette für Tests:
#
# Server
# Terminal
# Smartcard --> NetworkHandler --> Terminal --> Observer
#                              \
#                               --> Server --> Queue
#
# later:
#
# Queue --> NetworkHandler --> Terminal --> Observer
#
