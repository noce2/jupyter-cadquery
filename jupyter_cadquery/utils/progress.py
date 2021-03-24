import time
import ipywidgets as widgets


class Timer:
    def __init__(self, timeit, activity):
        self.timeit = timeit
        self.activity = activity
        self.start = time.time()

    def stop(self):
        if self.timeit:
            print("%-20s %7.2f sec" % (self.activity + ":", time.time() - self.start))


class Progress:
    def __init__(self, max_, width):
        self.max = max_
        self.progress = widgets.IntProgress(
            0,
            0,
            max_,
            layout=widgets.Layout(
                width=f"{width}px", height="10px", padding="0px 4px 0px 0px !important", margin="-3px 0px -3px 2px"
            ),
        )
        self.progress.add_class("jc-progress")

    def reset(self, max_):
        self.max = max_
        self.progress.value = 0
        self.progress.max = max_

    def update(self):
        if self.progress.value < self.max:
            self.progress.value += 1
