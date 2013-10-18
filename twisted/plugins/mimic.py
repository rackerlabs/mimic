from twisted.application.service import ServiceMaker


mimicService = ServiceMaker(
    "mimic Service/",
    "mimic.tap",
    "Mocks for Autoscale.",
    "mimic")
