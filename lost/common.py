from datetime import date, datetime
import time


FAKE_DATETIME_FOR_TESTS = None
FAKE_TIMETIME_FOR_TESTS = None


def get_date_today():
    if FAKE_DATETIME_FOR_TESTS:
        return FAKE_DATETIME_FOR_TESTS.date()

    return date.today()


def get_datetime_now():
    if FAKE_DATETIME_FOR_TESTS:
        return FAKE_DATETIME_FOR_TESTS

    return datetime.now()


def get_time_time():
    if FAKE_TIMETIME_FOR_TESTS is not None:
        return FAKE_TIMETIME_FOR_TESTS

    return time.time()
