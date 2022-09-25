class ZigBeeTimeout(RuntimeError):
    def __init__(self):
        super().__init__('ZigBee timeout')


class ZigBeeDeliveryFailure(RuntimeError):
    def __init__(self):
        super().__init__('ZigBee delivery failure')
