#!/usr/bin/env python 
# encoding: utf-8 
# @author: yihuai lan
# @fileName: base_subcriber.py 
# @date: 2024/5/25 20:04 
#
# describe:
#
from abc import ABC, abstractmethod
from typing import Any

from observation.observation import Observation
from abc import ABC, abstractmethod
from typing import Any
from observation.observation import Observation


class Subscriber(ABC):

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    @abstractmethod
    def notify(self, topic: str, message: str, image: Any, observation: Observation):
        pass
