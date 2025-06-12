#!/usr/bin/env python 
# encoding: utf-8 
# @author: yihuai lan
# @fileName: base_observation.py 
# @date: 2024/5/25 20:13 
#
# describe:
#
import copy
from abc import ABC, abstractmethod

from abc import ABC, abstractmethod


class Observation(ABC):

    def __init__(self):
        pass

    # @abstractmethod
    # def init(self):
    #     pass

    @abstractmethod
    def create_image(self):
        pass

    def to_json(self):
        # Use __dict__ to get all instance variables and their values
        return copy.deepcopy(self.__dict__)