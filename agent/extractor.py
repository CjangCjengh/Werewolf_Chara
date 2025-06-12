#!/usr/bin/env python 
# encoding: utf-8 
# @author: yihuai lan
# @fileName: extractor.py 
# @date: 2024/5/30 10:52 
#
# describe:
#
from agent.agent import Agent


class Extractor(Agent):
    def make_decision(self, message):
        answer = self.call_api(message)
        # print( answer)
        return answer
