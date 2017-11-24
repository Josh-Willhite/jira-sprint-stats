#!/usr/bin/env python
from datetime import datetime
import json
import sys

import click
from jira import JIRA
import matplotlib.pyplot as plt
import pandas as pd
from pandas import DataFrame


class SprintStats(object):
    def __init__(self, config):
        self.cfg = config
        self.jira = self.get_jira()
        self.issues = self.get_issues()

    def get_jira(self):
        return JIRA(server=self.cfg['server'], basic_auth=(self.cfg['user'], self.cfg['password']))

    def sum_tickets_created(self, user):
        issues = self.jira.search_issues(
                'sprint = {} and creator = {}'.format(
                    self.cfg['sprint'],
                    user
                )
        )
        return len(issues)

    def total_points(self):
        return sum([i.raw['fields'][self.cfg['points_field']] for i in self.issues])

    def total_tickets(self):
        return len(self.issues)

    def get_issues(self):
        return self.jira.search_issues('sprint = {}'.format(self.cfg['sprint']))

    def sum_points_complete(self, user):
        issues = self.jira.search_issues(
                'sprint = {} and assignee changed from {} and status = resolved'.format(
                    self.cfg['sprint'],
                    user
                )
        )
        return sum([i.raw['fields'][self.cfg['points_field']] for i in issues])


class PlotSprintStats(object):
    def __init__(self, config):
        self.cfg = config
        self.stats = self.get_sprint_stats()
        self.plot()

    def get_sprint_stats(self):
        stats = []
        for sprint in self.cfg['sprints']:
            self.cfg['sprint'] = sprint
            ss = SprintStats(self.cfg)
            sprint_stats = {
                    'sprint': sprint,
            }
            for user in self.cfg['users']:
                sprint_stats['points_completed({})'.format(user)] = ss.sum_points_complete(user)
                sprint_stats['tickets_created({})'.format(user)] = ss.sum_tickets_created(user)
            stats.append(sprint_stats)
        return stats

    def plot(self):
        data = DataFrame(self.stats)
        data.index = data.sprint
        del data['sprint']
        points_df = data.copy()
        for column in points_df.columns:
            if 'points_completed' not in column:
                del points_df[column]
        created_df = data.copy()
        for column in created_df.columns:
            if 'tickets_created' not in column:
                del created_df[column]
        fig, axes = plt.subplots(nrows=2, ncols=1)
        ax_points = points_df.plot(
            kind='bar',
            title='Points Completed',
            ax=axes[0]
        )
        ax_points.set_xlabel('Sprint')
        ax_points.set_ylabel('Points Completed')
        ax_created = created_df.plot(
            kind='bar',
            title='Tickets Created',
            ax=axes[1]
        )
        ax_created.set_xlabel('Sprint')
        ax_created.set_ylabel('Tickets Created')
        fig.tight_layout()
        fig.set_size_inches(18.5, 10.5, forward=True)
        plt.savefig('sprint_stats.png', dpi=100)


@click.command()
@click.argument('config_file', type=click.File('r'))
def main(config_file):
    pss = PlotSprintStats(json.load(config_file))

main()


