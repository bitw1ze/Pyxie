import abc
import re


class Modifier(metaclass=abc.ABCMeta):


    @abc.abstractmethod
    def modify(self, data):
        return

class CustomModifier(Modifier):
    def __init__(self, callback):
        self.callback = callback

    def modify(self, data):
        return self.callback(data)

class RegexModifier(Modifier):
    def __init(self, search_re, replace_re):
        self.search_re = search_re
        self.replace_re = replace_re

    def modify(self, data):
        return re.sub(self.search_re, self.replace_re, data)
