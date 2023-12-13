import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

from classes.view.View import ViewTk


def test_main_win_class():
    mw = ViewTk()
    mw.loop()


if __name__ == '__main__':
    test_main_win_class()
