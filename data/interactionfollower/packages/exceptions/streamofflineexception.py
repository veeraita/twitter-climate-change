
class StreamOfflineException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None
    def __str__(self):
        if self.message:
            return 'StreamOfflineException: {}'.format(self.message)
        else:
            return 'StreamOfflineException has been raised.'
    pass