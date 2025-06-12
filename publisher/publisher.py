#!/usr/bin/env python 
# encoding: utf-8 
# @author: yihuai lan
# @fileName: base_publisher.py 
# @date: 2024/5/25 20:04 
#
# describe:
#
from abc import ABC, abstractmethod

from observation.observation import Observation
from subscriber.subscriber import Subscriber
from broker.broker import Broker


class Publisher(ABC):

    # def __init__(self, broker: Broker):
    #     self.broker = broker

    # def register(self, subscriber: Subscriber, topic: str):
    #     self.broker.register(subscriber, topic)

    # def unregister(self, subscriber: Subscriber, topic: str):
    #     self.broker.unregister(subscriber, topic)

    @abstractmethod
    def publish(self, topic: str, message: str, observation):
        pass
