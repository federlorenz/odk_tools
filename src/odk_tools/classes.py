import pandas as pd
import copy
import matplotlib.gridspec as gridspec
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np


# class SurveyPlus(pd.DataFrame):
#     """
#     attribute = surveys \n
#     methods = surveyfilter, surveysubset, get_survey, merge_horizontal, merge_vertical
#     """

#     def __init__(self, *args, **kwargs):
#         pd.DataFrame.__init__(self, *args, **kwargs)

#     @property
#     def _constructor(self):
#         return SurveyPlus

#     _metadata = ["surveys"]

#     surveys = {'baseline': ['_B'],
#                'recruitment': ['_R'],
#                'diary': ['_D'],
#                'weekly': ['_W'],
#                'pay': ['_P'],
#                'end': ['_E']}

#     def check_surveys(x):
#         tocheck = x.surveys
#         suffix = list(set(pd.Series(x.columns).apply(
#             lambda a: "_"+a.split("_")[-1])))
#         for j in tocheck.keys():
#             for k in tocheck[j]:
#                 if k not in suffix:
#                     tocheck[j].remove(k)
#         new = {}
#         for j in tocheck.keys():
#             if len(tocheck[j]) != 0:
#                 new[j] = tocheck[j]
#         x.surveys = new

#     def survey_filter(self, survey_in=None, x=surveys):
#         """
#         Input list of surveys.
#         """
#         if survey_in == None:
#             return self
#         else:
#             get_extension = []
#             for j in survey_in:
#                 for k in x[j]:
#                     get_extension.append(k)
#             get_columns = []
#             for k in self.columns:
#                 if "_"+k.split("_")[-1] in get_extension:
#                     get_columns.append(k)
#             self = self.drop_duplicates(subset=get_columns).dropna(
#                 how="all", subset=get_columns)
#             self.surveys = {key: value for key,
#                             value in x.items() if key in survey_in}
#             return self

#     def survey_subset(self, survey_in=None, x=surveys, id_column=None):
#         if survey_in == None:
#             return self
#         else:
#             try:
#                 get_extension = []
#                 for j in survey_in:
#                     for k in x[j]:
#                         get_extension.append(k)
#                 get_columns = []
#                 for k in self.columns:
#                     if "_"+k.split("_")[-1] in get_extension:
#                         get_columns.append(k)
#                 if id_column == None:
#                     return self[get_columns]
#                 else:
#                     return self[[id_column]+get_columns]
#             except:
#                 print("error")

#     def get_survey(self, survey=None):
#         if survey == None:
#             return self
#         else:
#             self = self.survey_filter(survey_in=[survey])
#             self = self.survey_subset(survey_in=[survey])
#             self.surveys = {key: value for key,
#                             value in self.surveys.items() if key in [survey]}
#             return self

#     def merge_horizontal(self, other, set_index=None):
#         surveys = {key: [] for key in list(
#             set(self.surveys.keys()).union(set(other.surveys.keys())))}
#         for j in surveys.keys():
#             for k in (self.surveys, other.surveys):
#                 if j in k.keys():
#                     surveys[j] = surveys[j] + k[j]
#             surveys[j] = list(set(surveys[j]))
#         if set_index == None:
#             output = self.join(other, how="outer")
#         else:
#             output = self.set_index(set_index).join(
#                 other.set_index(set_index), how="other")
#         output.surveys = surveys
#         return output

#     def merge_vertical(self, other, set_index=None):
#         shared = list(set(self.columns).intersection(set(other.columns)))
#         surveys = {key: [] for key in list(
#             set(self.surveys.keys()).union(set(other.surveys.keys())))}
#         for j in surveys.keys():
#             for k in (self.surveys, other.surveys):
#                 if j in k.keys():
#                     surveys[j] = surveys[j] + k[j]
#             surveys[j] = list(set(surveys[j]))
#         if set_index == None:
#             output = pd.concat(
#                 [self[[i for i in self.columns if i in shared]], other[[i for i in other.columns if i in shared]]])
#         else:
#             output = pd.concat([self.set_index(set_index)[[i for i in self.columns if i in shared]], other.set_index(
#                 set_index)[[i for i in other.columns if i in shared]]])
#         output.surveys = surveys
#         SurveyPlus.check_surveys(output)
#         return output

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

    def pdf_summary(self, directory=''):

        def filter_text(s, filter=["""<span style="color:red">""", "</span>", "**"]):
            for j in filter:
                s = s.replace(j, "")
            return s

        def insert_newline(s):
            if len(s) < 2:
                return s[0]
            else:
                b = range(1, len(s))
                for i in range(len(b)):
                    s.insert(b[i]+i, "\n")
                z = "".join(s)
                return z

        def group_text(s, no):
            a = filter_text(s).split()
            if len(a) < no:
                return s
            else:
                b = [" ".join(a[x:x+no]) for x in range(0, len(a), no)]
                return insert_newline(b)

        def question_type(var, survey=self.survey):
            return survey["type"].loc[survey["name"] == var].iloc[0].split()

        def reindex(input, var, choices=self.choices):
            if question_type(var)[0] == "select_one":
                selects = choices["label::English (en)"].loc[choices["list_name"]
                                                            == question_type(var)[1]]
                input = input.reindex(selects)
            if question_type(var)[0] == "integer":
                input = input.sort_index()
            if question_type(var)[0] == "decimal":
                input = input.sort_index()
            if question_type(var)[0] == "select_multiple":
                selects = choices["label::English (en)"].loc[choices["list_name"]
                                                            == question_type(var)[1]]
                input = input.reindex(selects)
            return input

        def multiprocess(series):
            out = []
            for j in series.index:
                if not pd.isna(series[j]):
                    step = series[j].split(" \n")
                    for i in step:
                        out.append(i)
            out = pd.Series(out)
            return (out)

        def getIndexLength(var, data):
            if question_type(var)[0] != "select_multiple":
                a = data[var].loc[~data[var].isna()].value_counts()
                a = reindex(a, var).fillna(0)
            else:
                a = multiprocess(data[var].loc[~data[var].isna()]).value_counts()
                a = reindex(a, var).fillna(0)
            return len(a.index)

        def pie(ax, var, data, survey=self.survey, title_group=4, label_group=3):
            if question_type(var)[0] != "select_multiple":
                a = data[var].loc[~data[var].isna()].value_counts()
                a = reindex(a, var).fillna(0)
            else:
                a = multiprocess(data[var].loc[~data[var].isna()]).value_counts()
                a = reindex(a, var).fillna(0)
            title = group_text(
                survey["label::English (en)"].loc[survey["name"] == var].iloc[0], title_group)
            labels = [group_text(str(i), label_group) for i in a.index]
            if max(a, default=0) == 0:
                ax.set_title(title)
                ax.set_xlabel("(total="+str(a.sum())+")", labelpad=1)
            else:
                ax.pie(x=a.values, labels=labels,
                    autopct=lambda x: '{:.0f}'.format(x*a.values.sum()/100))
                ax.set_title(title)
                ax.set_xlabel("(total="+str(a.sum())+")", labelpad=1)

        def bar(ax, var, data, survey=self.survey, title_group=4, label_group=3):
            if question_type(var)[0] != "select_multiple":
                a = data[var].loc[~data[var].isna()].value_counts()
                a = reindex(a, var).fillna(0)
            else:
                a = multiprocess(data[var].loc[~data[var].isna()]).value_counts()
                a = reindex(a, var).fillna(0)
            title = group_text(
                survey["label::English (en)"].loc[survey["name"] == var].iloc[0], title_group)
            label = [group_text(str(i), label_group) for i in a.index]
            y = range(len(a))
            width = a.values
            if max(a, default=0) == 0:
                ax.set_title(title)
                ax.set_xlabel("Count (total="+str(a.sum())+")", labelpad=1)
            else:
                bars = ax.barh(y=y, width=width, tick_label=label)
                ax.bar_label(bars)
                ax.set_title(title)
                ax.set_xlabel("Count (total="+str(a.sum())+")", labelpad=1)

        def hist(ax, var, data, survey=self.survey, title_group=4, label_group=3):
            a = data[var].loc[~data[var].isna()]
            title = group_text(
                survey["label::English (en)"].loc[survey["name"] == var].iloc[0], title_group)
            if len(a) == 0:
                ax.set_title(title)
                ax.set_ylabel("Count", labelpad=1)
                ax.set_xlabel("Participant's reply", labelpad=1)
            else:
                align = "mid"
                ax.hist(x=a, align=align, bins=int(max(a)-min(a)+1),
                        range=(min(a)-0.5, max(a)+0.5))
                ax.set_title(title)
                ax.set_ylabel("Count (total="+str(len(a))+")", labelpad=1)
                ax.set_xlabel("Participant's reply", labelpad=1)

        def inches(cm):
            return cm/2.54

        def fig_wrap(var, data, typ="bar", title_group=4, label_group=3, width=20, height=12):

            indexLength = getIndexLength(var, data=data)
            if indexLength > 7:
                height = min(height + (height/7)*(indexLength-7), 27)

            gs = gridspec.GridSpec(nrows=1, ncols=1)
            fig = plt.figure(figsize=(inches(width)*gs.nrows,
                                    inches(height)*gs.ncols))

            for i in range(0, gs.nrows*gs.ncols):
                ax = plt.subplot(gs[i//gs.ncols, i % gs.ncols])
                if typ == "bar":
                    bar(ax, var, data=data, title_group=title_group,
                        label_group=label_group)
                elif typ == "pie":
                    pie(ax, var, data=data, title_group=title_group,
                        label_group=label_group)
                elif typ == "hist":
                    hist(ax, var, data=data, title_group=title_group,
                        label_group=label_group)
            gs.tight_layout(fig)
            b = BytesIO()
            plt.savefig(b, format="png")
            plt.close()
            return b, height

        pdf = FPDF()

        pdf.add_page()
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(w=210, txt=self.survey_name, align="C")
        pdf.ln(h=20)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(w=210, txt='Total number of submissions = ' +
                 str(len(self.submissions)), align="L")

        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)

        ty = ['select_one', 'select_multiple', 'integer']

        print_dic = {self.survey['name'].iloc[j]: 'bar' for j in range(
            len(self.survey)) if question_type(self.survey['name'].iloc[j])[0] in ty}

        for i in print_dic.keys():
            figu, figuHeight = fig_wrap(
                i, data=self.submissions, typ=print_dic[i])

            pdf.set_x(105-100)
            pdf.image(figu, w=200, h=figuHeight*10)
            pdf.ln(10)

        pdf.output(directory+self.survey_name+'.pdf', 'F')

    def add_headers(self, questions=True, variable=None):
        df = self.submissions
        repeats = self.repeats
        survey = self.survey

        if questions == True:
            a = []
            for j in df.columns:
                if j in list(survey["name"]):
                    x = survey["label::English (en)"].loc[survey["name"]
                                                          == j].iloc[0]
                    a.append(x)
                else:
                    a.append(np.nan)
            df_out = copy.deepcopy(df)
            df_out.loc[-1] = a
            df_out.sort_index(inplace=True)

            reps = copy.copy(repeats)
            for k in reps.keys():
                a = []
                for j in reps[k].columns:
                    if j in list(survey["name"]):
                        x = survey["label::English (en)"].loc[survey["name"]
                                                              == j].iloc[0]
                        a.append(x)
                    else:
                        a.append(np.nan)
                rep_out = copy.deepcopy(repeats[k])
                rep_out.loc[-1] = a
                rep_out.sort_index(inplace=True)
                reps[k] = rep_out

        if variable != None:
            a = []
            for j in df.columns:
                if j in list(survey["name"]):
                    x = survey[variable].loc[survey["name"]
                                                          == j].iloc[0]
                    a.append(x)
                else:
                    a.append(np.nan)
            if not questions:
                df_out = copy.deepcopy(df)
                df_out.loc[-1] = a
                df_out.sort_index(inplace=True)
            else:
                df_out.loc[-2] = a
                df_out.sort_index(inplace=True)

            if not questions:
                reps = copy.copy(repeats)
            for k in reps.keys():
                a = []
                for j in reps[k].columns:
                    if j in list(survey["name"]):
                        x = survey[variable].loc[survey["name"]
                                                              == j].iloc[0]
                        a.append(x)
                    else:
                        a.append(np.nan)
                if not questions:
                    rep_out = copy.deepcopy(reps[k])
                    rep_out.loc[-1] = a
                    rep_out.sort_index(inplace=True)
                else:
                    rep_out.loc[-2] = a
                    rep_out.sort_index(inplace=True)
                reps[k] = rep_out


        if variable == None:
            new_labels = pd.MultiIndex.from_arrays(
                [df_out.columns, df_out.iloc[0]], names=['code', 'question'])
            df_out = df_out.set_axis(new_labels, axis=1).iloc[1:]
            for k in reps.keys():
                new_labels = pd.MultiIndex.from_arrays(
                    [reps[k].columns, reps[k].iloc[0]], names=['code', 'question'])
                reps[k] = reps[k].set_axis(new_labels, axis=1).iloc[1:]
        elif not questions:
            new_labels = pd.MultiIndex.from_arrays(
                [df_out.columns, df_out.iloc[0]], names=['code', 'variable'])
            df_out = df_out.set_axis(new_labels, axis=1).iloc[1:]
            for k in reps.keys():
                new_labels = pd.MultiIndex.from_arrays(
                    [reps[k].columns, reps[k].iloc[0]], names=['code', 'variable'])
                reps[k] = reps[k].set_axis(new_labels, axis=1).iloc[1:]
        else:
            new_labels = pd.MultiIndex.from_arrays(
                [df_out.columns, df_out.iloc[0], df_out.iloc[1]], names=['code', 'variable','question'])
            df_out = df_out.set_axis(new_labels, axis=1).iloc[2:]
            for k in reps.keys():
                new_labels = pd.MultiIndex.from_arrays(
                    [reps[k].columns, reps[k].iloc[0],reps[k].iloc[1]], names=['code', 'variable','question'])
                reps[k] = reps[k].set_axis(new_labels, axis=1).iloc[2:]


        return Form(submissions=df_out, repeats=reps, survey=survey, survey_name=self.survey_name, variable=self.variable, time_variable=self.time_variable,  choices=self.choices)
