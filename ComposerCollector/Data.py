__author__ = ''


class Repository:

    def __init__(self, name, path, master, branches=[]):
        self.name = name

        self.path = path

        self.master = master

        self.branches = []


class Branch:

    def __init__(self, composer_json, composer_lock):
        self.composer_json = composer_json

        self.composer_lock = composer_lock


class ComposerJson:

    def __init__(self, file):
        self.name = ''
        self.description = ''

        self.repositories = []

        self.require = []

        self.require_dev = []

        self.extra = []


class ComposerLock:

    def __init__(self, file):
        self.hash = ''
        self.version = ''

        self.packages = []

        self.aliases = []

        self.minimum_stability = False

        self.prefer_lowest = False

        self.platform = []

        self.platform_dev = []
