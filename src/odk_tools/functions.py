#%% #@ Imports
from .classes import Form
import pandas as pd
from typing import Dict
import copy

#%% #@ Functions

def form_merge(form:Form) -> pd.DataFrame:

    subs = form.submissions
    reps = form.repeats
    if type(subs.columns) == pd.core.indexes.base.Index:
        if len(reps) == 0:
            subs = subs.set_index('KEY', drop=False)
            return subs
        else:
            subs = subs.set_index('KEY', drop=False)
            out = subs.join(other=[value.set_index('PARENT_KEY').rename(columns={
                            'KEY': 'KEY'+key.split('-')[-1]}) for key, value in reps.items()], how='outer', validate='one_to_many')
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
            return out
    else:
        if len(reps) == 0:
            subs = subs.set_index('KEY', drop=False)
            return subs
        else:
            subs = subs.set_index('KEY', drop=False)
            out = subs
            for key,value in reps.items():
                middle = out.join(value.set_index('PARENT_KEY').rename(columns={
                    'KEY': 'KEY'+key.split('-')[-1]}, level='code'), how='outer', lsuffix='_x', rsuffix='_y')
                out = middle
            drops = []
            for j in range(len(out.columns.get_level_values('code'))):
                a = out.columns.get_level_values('code')[j]
                for i in range(len(out.columns.get_level_values('code'))):
                    b = out.columns.get_level_values('code')[i]
                    if (a[:-2] == b[:-2]) & (a[-2:] == '_x') & (b[-2:] == '_y'):
                        out[a] = out[b]
                        out.rename(columns={a: a[:-2]}, inplace=True,level='code')
                        drops.append(b)
            out.drop(columns=drops, inplace=True,level='code')
            return out

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
