import queue
import threading


#
# Resources about thread programming in Python:
#
#   - Learning Python, 5th Edition, Mark Lutz, ISBN: 9781449355739,
#     https://learning-python.com/about-pp.html
#   - https://realpython.com/python-concurrency/
#   - https://realpython.com/intro-to-python-threading/
#


thread_queue = queue.Queue()


def thread_wrapper(action, action_args, callback):
    # `action` is a callable that can be generally unaware that it is run in a
    # worker thread (unless it modifies shared, global state).
    result = action(*action_args)
    thread_queue.put((callback, [result]))


def start_thread(action, action_args, callback):
    thr = threading.Thread(target=thread_wrapper, args=(action, action_args, callback))
    thr.start()
