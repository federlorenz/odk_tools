#%% #@ Imports
from .classes import Form
import pandas as pd
from typing import Dict
import copy
from numpy import nan

#%% #@ Functions

def repeat_structure(survey):
    structure = {}
    for k in range(len(survey)):
        if survey['type'].iloc[k] in ["begin_repeat","begin repeat"]:
            structure[survey['name'].iloc[k]] = None
    levels = [None]
    for k in range(len(survey)):
        if survey['type'].iloc[k] in ["begin_repeat", "begin repeat"]:
            structure[survey['name'].iloc[k]] = levels[-1]
            levels.append(survey['name'].iloc[k])
        elif survey['type'].iloc[k] == "end_repeat":
            levels = levels[:-1]
    return structure

def form_merge(form: Form, language="English (en)") -> pd.DataFrame:
    form = form
    subs = form.submissions
    reps = form.repeats
    rstruct = repeat_structure(form.survey)
    survey = form.survey
    out = subs
    for k, v in reps.items():
        if len(v)>0:
            out = pd.merge(left=out.set_index(f"{'' if rstruct[k] == None else rstruct[k]+'-'}KEY", drop=False), right=v.rename(
                columns={"KEY": f"{k}-KEY"}).set_index('PARENT_KEY'), how='outer', left_index=True, right_index=True)
            drops = []
            for j in range(len(out.columns)):
                a = out.columns[j]
                for i in range(len(out.columns)):
                    b = out.columns[i]
                    if (a[:-2] == b[:-2]) & (a[-2:] == '_x') & (b[-2:] == '_y'):
                        out[a] = out[b]
                        out.rename(columns={a: a[:-2]}, inplace=True)
                        drops.append(b)
            out.drop(columns=drops, inplace=True)
            out.set_index("KEY", drop=False, inplace=True)

    rep_key_columns = [i for i in out.columns if (
        (i.split("-")[-1] == "KEY") and (i[:-4] in list(rstruct.keys())))]
    new_columns = list(out.columns)
    for i in rep_key_columns:
        old_location = new_columns.index(i)
        new_columns.insert(-1, i)
        new_columns.pop(old_location)
    out = out[new_columns]

    out.reset_index(inplace=True, drop=True)

    a = []
    for j in out.columns:
        if j in list(survey["name"]):
            x = survey[f"label::{language}"].loc[survey["name"]
                                                 == j].iloc[0]
            a.append(x)
        elif j in [i+"-KEY" for i in list(rstruct.keys())]:
            a.append(f"Unique KEYs for submissions to repeat section {j[:-4]}")
        else:
            a.append(nan)
    df_out = copy.deepcopy(out)
    df_out.loc[-1] = a
    df_out.sort_index(inplace=True)

    return df_out

def multi_merge(forms = Dict[Form,str])->pd.DataFrame:
    to_be_merged = []
    for key,value in forms.items():
        df = form_merge(key).set_index(value, drop=False)
        h = df.columns.to_frame()
        h['survey'] = [key.survey_name for i in range(len(h))]
        df.columns = pd.MultiIndex.from_frame(h).reorder_levels(['survey']+list(set(df.columns.names).difference(set('survey'))))
        to_be_merged.append(df)
    for j in range(len(to_be_merged)):
        out = copy.deepcopy(to_be_merged[j])
    if len(to_be_merged) == 1:
        return to_be_merged[0]
    else:
        out = to_be_merged[0].join(other = to_be_merged[1:],how='outer').reset_index(drop=True)
        return out
