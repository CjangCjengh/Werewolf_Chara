
from abc import ABC, abstractmethod
from typing import Any

from subscriber.subscriber import Subscriber
from observation.observation import Observation


class Broker(ABC):
    def __init__(self):
        self.subscribers = {}

    def register(self, subscriber: Subscriber, topic: str):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        if subscriber not in self.subscribers[topic]:
            self.subscribers[topic].append(subscriber)

    def unregister(self, subscriber: Subscriber, topic: str):
        if topic in self.subscribers:
            if subscriber in self.subscribers[topic]:
                self.subscribers[topic].remove(subscriber)

    @abstractmethod
    def publish(self, topic: str, message, image, observation):
        pass
