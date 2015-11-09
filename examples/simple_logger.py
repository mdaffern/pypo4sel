from datetime import datetime

from pypo4sel.core.log2l import ListenerMixin, Options, listeners


class Step(object):
    def __init__(self, message):
        super(Step, self).__init__()
        self.message = message
        self.start_time = self.end_time = datetime.today()
        self.sub_steps = []


class SimpleLogger(ListenerMixin):
    steps = []
    """ :type: list[Step]"""
    stack = []
    """ :type: list[Step]"""
    suppress = None

    def start_step(self, step_id, **options):
        if self.suppress is None:
            self.suppress = step_id if options.get(Options.SUPPRESS_CHILD_LOGS, False) else None
            if Options.STEP_MESSAGE in options:
                message = options[Options.STEP_MESSAGE].format(**options)
            elif Options.ELEMENT_NAME in options:
                params = str(options[Options.ARGS][1:]) if len(options[Options.ARGS]) > 1 else ""
                params += str(options[Options.KWARGS]) if len(options[Options.KWARGS]) > 0 else ""
                message = "on {} do {} with {}" if params else "on {} do {}"
                message = message.format(options[Options.ARGS][0].name, options[Options.STEP_NAME], params)
            else:
                message = options[Options.STEP_NAME]
            self.stack.append(Step(message))

    def end_step(self, step_id):
        if self.suppress is None or self.suppress == step_id:
            self.suppress = None
            step = self.stack.pop()
            step.end_time = datetime.today()
            self._add_step(step)

    def message(self, msg, **kwargs):
        self._add_step(Step(msg))

    def exception(self, step_id, exc_type, exc_val, exc_tb):
        self.message(str(exc_val))

    def _add_step(self, step):
        if self.stack:
            self.stack[-1].sub_steps.append(step)
        else:
            self.steps.append(step)


from nose.plugins import Plugin


# noinspection PyPep8Naming
class PypoNose(Plugin):
    name = 'pyponose'

    def __init__(self):
        super(PypoNose, self).__init__()
        self.log_store = SimpleLogger()
        listeners.append(self.log_store)

    def addError(self, test, err):
        pass

    def addFailure(self, test, err):
        pass

    def addSuccess(self, test):
        print str(test), getattr(test, 'testcontext', None)

    def beforeTest(self, test):
        self.log_store.start_step(-1, **{Options.STEP_NAME: str(test)})
        self.log_store.message('before test' + str(test))

    def afterTest(self, test):
        self.log_store.end_step(-1)

    def startContext(self, context):
        self.log_store.start_step(-1, **{Options.STEP_NAME: context.__name__})

    def stopContext(self, context):
        self.log_store.end_step(-1)

    def finalize(self, res):
        print res, self.log_store
