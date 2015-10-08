__author__ = ''


class Repository:

    def __init__(self):
        self. name = ''

        self.master = Branch.Branch()

        self.branches = []


class Branch:

    def __init__(self):
        composerJson = ComposerJson()

        composerLock = ComposerLock()


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
