#!/usr/bin/env python3

from aws_cdk import core

from mindlamp.mindlamp_stack import MindlampStack


app = core.App()
MindlampStack(app, "mindlamp")

app.synth()
