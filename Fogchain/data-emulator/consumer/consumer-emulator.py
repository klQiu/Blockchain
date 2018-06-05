# -*- coding: utf-8 -*-
"""
Created by Qu Zhe on 2018-04-01

This module implements the consumer data emulator of the FogChain project. The time unit is minute.
The implementation is based on
    Bajada, J., Fox, M., & Long, D. Load modelling and simulation of household electricity consumption for the
    evaluation of demand-side management strategies. In Innovative Smart Grid Technologies Europe (ISGT EUROPE), 2013

Attributes:
    DEFAULT_TIME_PERIOD_NUM (int): the default number of time periods to simulate.
    DEFAULT_TIME_PERIOD_LEN (int): the default length of each time period.
    DEFAULT_EMULATION_FILE_PATH (str): the default path to store the emulation result.
"""

import argparse
import random
import csv
from scipy.stats import norm, expon

DEFAULT_TIME_PERIOD_NUM = 96
DEFAULT_TIME_PERIOD_LEN = 15
DEFAULT_EMULATION_FILE_PATH = 'emulation_res.csv'

appliances = []


class BaseAppliance:
    def __init__(self, name, on_mean, on_dev, on_watt, off_watt=0, init_state='off', last_on=0):
        self.name = name
        self.on_mean = on_mean
        self.on_dev = on_dev
        self.on_watt = on_watt
        self.off_watt = off_watt
        self.state = init_state
        self.last_on = last_on

    def get_rate(self, time):
        raise NotImplementedError("%s's usage rate function is not specified" % self.name)

    def get_max_rate(self):
        raise NotImplementedError("%s's max rate is not specified" % self.name)

    def get_on_duration(self):
        prob = random.random()
        duration = norm.ppf(prob, loc=self.on_mean, scale=self.on_dev)
        return int(round(duration))

    def get_next_on(self, current_time):
        max_rate = self.get_max_rate()
        exp_scale = 1 / max_rate
        next_on = current_time

        while True:
            prob = random.random()
            next_on += expon.ppf(prob, scale=exp_scale)
            next_on_in_day = next_on % (24*60)
            p_accept = random.random()
            if p_accept <= self.get_rate(next_on_in_day) / max_rate:
                break

        return round(int(next_on))

    def simulate(self, target_list):
        print('simulating electricity consumption of %s' % self.name)
        current_time = 0
        while current_time < len(target_list):
            if self.state == 'off':
                next_on = self.get_next_on(current_time % (24 * 60))
                for t in range(current_time, min(next_on, len(target_list))):
                    target_list[t] += self.off_watt
                self.state = 'on'
                current_time = next_on
            else:
                on_dur = self.get_on_duration()
                for t in range(current_time, min(current_time + on_dur, len(target_list))):
                    target_list[t] += self.on_watt
                self.state = 'off'
                current_time += on_dur


class Kettle(BaseAppliance):
    def __init__(self, name='Kettle', on_mean=20, on_dev=1, on_watt=1000):
        super(Kettle, self).__init__(name=name, on_mean=on_mean, on_dev=on_dev, on_watt=on_watt)

    def get_rate(self, time):
        if 11 * 60 <= time <= 15 * 60:
            return 1 / 60
        elif 15 * 60 < time <= 20 * 60:
            return 1 / 150
        else:
            return 1 / 5000

    def get_max_rate(self):
        return 1 / 60


appliances.append(Kettle)


class Computer(BaseAppliance):
    def __init__(self, name='Computer', on_mean=240, on_dev=30, on_watt=80, off_watt=5):
        super(Computer, self).__init__(name=name, on_mean=on_mean, on_dev=on_dev, on_watt=on_watt, off_watt=off_watt)

    def get_rate(self, time):
        if 8*60 <= time <= 24*60:
            return 1 / 60
        elif time <= 2*60+30:
            return 1 / 90
        else:
            return 1 / 1000

    def get_max_rate(self):
        return 1 / 120


appliances.append(Computer)


class Lighting(BaseAppliance):
    def __init__(self, name='Lighting', on_mean=240, on_dev=50, on_watt=200):
        super(Lighting, self).__init__(name=name, on_mean=on_mean, on_dev=on_dev, on_watt=on_watt)

    def get_rate(self, time):
        if 7*60 <= time <= 18*60:
            return 1/240
        elif 18*60 < time <= 24*60:
            return 1/30
        else:
            return 1/500

    def get_max_rate(self):
        return 1/30


appliances.append(Lighting)


class Lighting2(BaseAppliance):
    def __init__(self, name='Lighting2', on_mean=100, on_dev=50, on_watt=150):
        super(Lighting2, self).__init__(name=name, on_mean=on_mean, on_dev=on_dev, on_watt=on_watt)

    def get_rate(self, time):
        if 4*60 <= time <= 20*60:
            return 1/200
        elif 20*60 < time <= 24*60:
            return 1/100
        else:
            return 1/500

    def get_max_rate(self):
        return 1/100


appliances.append(Lighting2)
appliances.append(Lighting2)


class WaterHeater(BaseAppliance):
    def __init__(self, name='Water heater', on_mean=60, on_dev=4, on_watt=1000):
        super(WaterHeater, self).__init__(name=name, on_mean=on_mean, on_dev=on_dev, on_watt=on_watt)

    def get_rate(self, time):
        if 8*60 <= time <= 9*60:
            return 1/40
        elif 18*60 <= time <= 20*60:
            return 1/60
        else:
            return 0

    def get_max_rate(self):
        return 1/40


appliances.append(WaterHeater)


class WashingMachine(BaseAppliance):
    def __init__(self, name='Washing machine', on_mean=35, on_dev=1, on_watt=500):
        super(WashingMachine, self).__init__(name=name, on_mean=on_mean, on_dev=on_dev, on_watt=on_watt)

    def get_rate(self, time):
        if 12*60 <= time <= 13*60:
            return 1/30
        elif 18*60 <= time <= 19*60:
            return 1/30
        else:
            return 0

    def get_max_rate(self):
        return 1/30


appliances.append(WashingMachine)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--periods_num', type=int, default=DEFAULT_TIME_PERIOD_NUM,
                        help='the number of time periods to generate')
    parser.add_argument('-l', '--period_length', type=int, default=DEFAULT_TIME_PERIOD_LEN,
                        help='the length of each time period (minute)')
    parser.add_argument('-p', '--result_path', type=str, default=DEFAULT_EMULATION_FILE_PATH,
                        help='the path to store the emulation result')
    args = parser.parse_args()
    print('generating %d %d-minute period records\n' % (args.periods_num, args.period_length))

    total_time = args.period_length*args.periods_num
    sim_result = [0]*total_time

    for appliance in appliances:
        appliance().simulate(sim_result)
 
    csv_header = ['period_start(min)', 'period_end(min)', 'electricity consumption(kwh)']
    csv_rows = []
    for i in range(0, args.periods_num):
        cur_time = i*args.period_length
        next_time = cur_time+args.period_length
        period_watt_mnt = sum(sim_result[cur_time:next_time])
        period_kwh = period_watt_mnt / 60000
        csv_rows.append((cur_time, next_time, period_kwh))

    with open(args.result_path, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(csv_header)
        f_csv.writerows(csv_rows)

    print('\nThe emulation result is stored in %s' % args.result_path)
