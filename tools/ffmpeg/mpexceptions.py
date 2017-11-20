
class ExceptionPygletMediaPlayerTesting(Exception):
    pass

class ExceptionUndefinedSamplesDir(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionSamplesDirDoesNotExist(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionSessionExistWithSameName(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionNoSessionIsActive(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionNoSessionWithThatName(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionAttemptToBreakRawDataProtection(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionAttemptToBrekReportsProtection(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionPlaylistFileDoNotExists(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionBadSampleInPlaylist(ExceptionPygletMediaPlayerTesting):
    def __init__(self, rejected):
        self.rejected = rejected
        super(ExceptionBadSampleInPlaylist, self).__init__()

class ExceptionUnknownReport(ExceptionPygletMediaPlayerTesting):
    def __init__(self, rpt_name):
        self.rpt_name = rpt_name

class ExceptionNoDbgFilesPresent(ExceptionPygletMediaPlayerTesting):
    pass

class ExceptionUnknownOutputFormat(ExceptionPygletMediaPlayerTesting):
    def __init__(self, output_format):
        self.output_format = output_format
