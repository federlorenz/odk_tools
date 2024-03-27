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

class DictionaryPlus(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    @property
    def _constructor(self):
        return DictionaryPlus
    
    def show(self, number=0):
        """
        return an element of a dictionary
        If number is not specified, returns the values associated with the first key
        """
        try:
            return(self[list(self.keys())[number]])
        except:
            print("something's wrong")


    def subset(self, filter_dict):
        """
        Return a subset of a dictionary, specified in filter_dict (itself a dictionary)
        filter_dict is {attrib:["attrib_value_x","attrib_value_y",..]}, where 
            attrib is an attribute of the elements of dictionary, and attrib_value is a list
            of the values of such attrib that the elements of returned dictionary can have    
        """
        if type(filter_dict) != type(dict()):
            print("subset function error: type filter_dict should be dict")
            return
        return_dict = self
        for i, j in filter_dict.items():
            a = {}
            for key, value in return_dict.items():
                try:
                    if value.__getattr__(i) in j:
                        a[key] = value
                except:
                    pass
            return_dict = a

        return DictionaryPlus(return_dict)


    def set_attrib(self, attribute):
        """
        returns the set of attribute values for dictionary
        """
        return_set = set()
        for i in self.values():
            try:
                return_set.add(i.__getattr__(attribute))
            except:
                pass

        return return_set
