import pandas as pd
import numpy as np
import copy

class Form():

    """
    submissions
    repeats
    variable
    time_variable
    survey_name
    choices
    survey
    """

    def __init__(self, submissions, survey, choices, repeats, survey_name, variable, time_variable) -> None:
        self.submissions =submissions
        self.repeats = repeats
        self.variable = variable
        self.time_variable = time_variable
        self.survey_name = survey_name
        self.survey = survey
        self.choices = choices

    @property
    def _constructor(self):
        return Form

    def filter_variable(self, x):
        submissions = copy.copy(
            self.submissions.loc[self.submissions[self.variable] == x])
        set_not_rejected = list(submissions["KEY"])
        reps =copy.copy(self.repeats)
        for j in reps.keys():
            reps[j] = reps[j].loc[[True if reps[j]["PARENT_KEY"].iloc[i].split("/")[0] in set_not_rejected else False for i in range(len(reps[j]))]]
        return Form(submissions, repeats=reps, survey_name=self.survey_name, variable=self.variable, time_variable=self.time_variable, survey=self.survey, choices=self.choices)

    def date_time_filter(
            self,
            time_start=None,
            time_end=None,
            date_start=None,
            date_end=None,
            day=None):
        if date_start is not None:
            submissions = copy.copy(self.submissions.loc[self.submissions[self.time_variable] >= date_start])
        if date_end is not None:
            submissions = copy.copy(self.submissions.loc[self.submissions[self.time_variable] <= date_end])
        if (time_start is not None) & (time_end is not None):
            if time_start > time_end:
                submissions = copy.copy(self.submissions.loc[(self.submissions[self.time_variable].time >= time_start)
                                | (self.submissions[self.time_variable].time < time_end)])
            else:
                submissions = copy.copy(self.submissions.loc[(self.submissions[self.time_variable].time >= time_start)
                                & (self.submissions[self.time_variable].time < time_end)])
        if (time_start is not None) & (time_end is None):
            submissions = copy.copy(self.submissions.loc[self.submissions[self.time_variable].time >= time_start])
        if (time_start is None) & (time_end is not None):
            submissions = copy.copy(self.submissions.loc[self.submissions[self.time_variable].time <= time_end])

        if day is not None:
            submissions = copy.copy(self.submissions.loc[[a in day for a in [self.submissions[self.time_variable][i].date().isoweekday()
                                                for i in range(len(self.submissions[self.time_variable]))]]])
        set_not_rejected = list(submissions["KEY"])
        reps = copy.copy(self.repeats)
        for j in reps.keys():
            reps[j] = reps[j].loc[[True if reps[j]["PARENT_KEY"].iloc[i].split(
                "/")[0] in set_not_rejected else False for i in range(len(reps[j]))]]
        return Form(submissions, repeats=reps, survey_name=self.survey_name, variable=self.variable, time_variable=self.time_variable, survey=self.survey, choices=self.choices)