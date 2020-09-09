#!/usr/bin/env python3

from aws_cdk import core

from mindlamp.mindlamp_stack import MindlampStack


app = core.App()
stack = MindlampStack(app, "mindlamp")
core.Tags.of(stack).add("Project", "LAMP Platform")
core.Tags.of(stack).add("Environment", "Development")
app.synth()
