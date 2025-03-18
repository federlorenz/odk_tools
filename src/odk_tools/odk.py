#%% #@ Libraries imports

import pandas as pd
import numpy as np
import requests
import json
from io import BytesIO
import copy
import zipfile as zip
import xlsxwriter
import xml.etree.ElementTree as ET
import uuid
from types import FunctionType
from .classes import Form

#%% #@ Functions

def save_to_excel(data, filename="output.xlsx", column_width=25, include_index=False, row_colours={0: "#D8E4BC", 1: "#C5D9F1"}, row_bold=[0], row_wrap=[1], autofilter=True, freeze_panes=True):

    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()

    for i in range(len(data.columns)):
        worksheet.write(0, i, data.columns[i])

    for i in range(len(data)):
        for j in range(len(data.columns)):
            if pd.isna(data.iloc[i, j]):
                pass
            else:
                worksheet.write(i+1, j, data.iloc[i, j])

    worksheet.set_column(0, len(data.columns), width=column_width)

    for i in range(len(data)):
        a = {}
        if i in list(row_colours.keys()):
            a["bg_color"] = row_colours[i]
        if i in row_bold:
            a["bold"] = True
        if i in row_wrap:
            a["text_wrap"] = True
        if len(a) != 0:
            worksheet.set_row(i, cell_format=workbook.add_format(a))

    if autofilter:
        worksheet.autofilter(1, 0, len(data), len(data.columns)-1)

    if freeze_panes:
        worksheet.freeze_panes(2, 0)

    workbook.close()

#%% #@ ODK Class

class ODK():

    def __init__(self, url):
        self.url=url
        self.form = None
        self.project = None
        self.survey = None
        self.choices = None

    def connect(self, email, password):

        self.email = email
        self.password = password

        req = requests.post(self.url+'/v1/sessions', data=json.dumps(
            {"email": self.email, "password": self.password}), headers={'Content-Type': 'application/json'})
    
        self.token = req.json()["token"]
        self.headers = {'Authorization': 'Bearer '+self.token}

    def set_target(self, project_name, form_name):
        self.project_name = project_name
        self.form_name = form_name
        self.project = self.get_project()
        self.form = self.get_form()
        self.survey = self.get_survey()
        self.choiches = self.get_choices()



    def list_projects(self):
        req = requests.get(self.url+'/v1/projects', headers=self.headers)
        projects = [req.json()[i]["name"] for i in range(len(req.json()))]
        return projects

    def get_project(self):
        req = requests.get(self.url+'/v1/projects', headers=self.headers)
        project = [req.json()[i]["id"] for i in range(len(req.json()))
                if req.json()[i]["name"] == self.project_name][0]
    
        return project

    def list_forms(self,project=None):
        req = requests.get(self.url+'/v1/projects', headers=self.headers)
        if project!=None:
            project = [req.json()[i]["id"] for i in range(len(req.json())) if req.json()[i]["name"] == project][0]
        else:
            project = [req.json()[i]["id"] for i in range(
                len(req.json())) if req.json()[i]["name"] == self.project_name][0]
        req = requests.get(self.url+'/v1/projects/' +
                           str(project)+"/forms", headers=self.headers)
        forms = [req.json()[i]["name"] for i in range(len(req.json()))]
        return forms

    def get_form(self):

        req = requests.get(self.url+'/v1/projects/' +
                           str(self.get_project())+"/forms", headers=self.headers)
        form = [req.json()[i]["xmlFormId"] for i in range(len(req.json())) if req.json()[i]["name"] == self.form_name][0]

        return form

    def save_form(self,path="", save_file=True, xml=False):

        if xml:
            extension = '.xml'
        else:
            extension = '.xlsx'
            version = str(pd.read_excel(BytesIO(req),
                    sheet_name="settings")["version"].iloc[0])
        
        req = requests.get(self.url+'/v1/projects/'+str(self.get_project())+"/forms/"+self.get_form()+extension, headers=self.headers).content

        if save_file:
            file = open(path+"form_v"+version+extension, "wb")
            file.write(req)
            file.close()
        else:
            return BytesIO(req)

    def get_submissions(self):
        
        req = (requests.get(self.url+'/v1/projects/' +
                            str(self.project)+"/forms/"+self.form+"/submissions.csv?",
                            headers=self.headers))
        df = pd.read_csv(BytesIO(req.content))
        return df

    def get_survey(self):
        req = requests.get(self.url+'/v1/projects/'+str(self.project)+"/forms/"+self.form+".xlsx", headers=self.headers)
        survey = pd.read_excel(BytesIO(req.content),na_values=[' ',''],keep_default_na=False).dropna(how='all')
        self.survey = survey
        return survey

    def get_choices(self):
        req = requests.get(self.url+'/v1/projects/'+str(self.project)+"/forms/"+self.form+".xlsx", headers=self.headers)
        choices = pd.read_excel(BytesIO(req.content), sheet_name="choices", na_values=[
                                ' ', ''], keep_default_na=False).dropna(how='all')
        self.choices = choices
        return choices
    
    def get_repeats(self):
        
        req = (requests.get(self.url+'/v1/projects/' +
                            str(self.project)+"/forms/"+self.form+"/submissions.csv.zip?attachments=false",
                            headers=self.headers))
        zipfile = zip.ZipFile(BytesIO(req.content))

        repeats = {}

        form_id = str(pd.read_excel(BytesIO(requests.get(self.url+'/v1/projects/'+str(self.project)+"/forms/"+self.form+".xlsx", headers=self.headers).content),
                    sheet_name="settings")["form_id"].iloc[0])
        
        for j in self.survey["name"].loc[self.survey["type"] == "begin_repeat"]:
            repeats[form_id+"-" + j] = pd.read_csv(zipfile.open(
                form_id+"-" + j+".csv"), na_values=[' ', ''], keep_default_na=False).dropna(how='all')

        return repeats

    def get_attachments(self):
        
        req = (requests.get(self.url+'/v1/projects/' +
                            str(self.project)+"/forms/"+self.form+"/attachments",
                            headers=self.headers))

        attachments = {}

        for j in req.json():
            attachments[j["name"]] = pd.read_csv(BytesIO((requests.get(self.url+'/v1/projects/' + str(self.project)+"/forms/"+self.form+"/attachments/"+j["name"], headers=self.headers)).content)) if j["name"].split(
                ".")[-1] == "csv" else BytesIO((requests.get(self.url+'/v1/projects/' + str(self.project)+"/forms/"+self.form+"/attachments/"+j["name"], headers=self.headers)).content)
        return attachments

    def get_media(self):
        
        req = requests.get(self.url+'/v1/projects/'+str(self.project) +
                           "/forms/"+self.form+".xlsx", headers=self.headers).content

        req = (requests.post(self.url+'/v1/projects/' +
                             str(self.project)+"/forms/" +
                             self.form+"/submissions.csv.zip?",
                             headers=self.headers))
        zipfile = zip.ZipFile(BytesIO(req.content))
        media = {}
        for name in zipfile.namelist():
            if (name.split('/')[0] == 'media') & (len(name)>6):
                media[name.split('/')[-1]] = zipfile.read(name)
        return media

    def processing_submission(self,process_datetimes=False):
        
        df = self.get_submissions()

        def remove_tail(list_in):
            a = []
            for j in list_in:
                if j[-2:] == ".0":
                    a.append(j[:-2])
                else:
                    a.append(j)
            return a


        def select_one(select, value):
            x = self.survey["type"].loc[self.survey["name"] == select].iloc[0].split(" ")[1]
            y = self.choices["label::English (en)"].loc[self.choices["list_name"].map(lambda x: x.strip())
                                                   == x].loc[self.choices["name"] == value].iloc[0]
            return y


        def select_multiple(select, value):
            x = self.survey["type"].loc[self.survey["name"] == select].iloc[0].split(" ")[1]
            y = self.choices.loc[self.choices["list_name"].map(lambda x: x.strip()) == x]
            z = []
            for i in range(len(y)):
                if str(y["name"].iloc[i]) in remove_tail(list(str(value).split(" "))):
                    z.append(y["label::English (en)"].iloc[i])
            return " \n".join(z)


        def select_one_from_file(select, value):
            x = self.survey["type"].loc[self.survey["name"] == select].iloc[0].split(" ")[1]
            y = pd.read_csv(x)
            z = y["label"].loc[y["name"] == value].iloc[0]
            return z

        def select_multiple_from_file(select, value):
            x = self.survey["type"].loc[self.survey["name"] == select].iloc[0].split(" ")[
                1]
            y = pd.read_csv(x)
            z = []
            for i in range(len(y)):
                if str(y["name"].iloc[i]) in remove_tail(list(str(value).split(" "))):
                    z.append(y["label"].iloc[i])
            return " \n".join(z)

        func = {"select_one_from_file": select_one_from_file,
                "select_one": select_one, "select_multiple": select_multiple, "select_multiple_from_file": select_multiple_from_file}

        group_names = list(self.survey["name"].loc[self.survey["type"] == "begin_group"])
        group_names = sorted(group_names, key=len, reverse=True)

        column_names = sorted(list(set(self.survey["name"].loc[((self.survey["type"] != "begin_group") & (self.survey["type"] != "end_group") & (
            self.survey["type"] != "begin_repeat") & (self.survey["type"] != "end_repeat"))]).difference(set([np.nan,""]))), key=len, reverse=True)


        df_columns = sorted(list(df.columns), key=len, reverse=True)

        for i in df_columns:
            for j in column_names:
                if i.endswith(j):
                    df = df.rename(columns={i: j})

        for i in df_columns:
            for j in group_names:
                if i.startswith(j):
                    df = df.rename(columns={i: i[len(j):]})

        for i in df.columns:
            # try:
            a = i
            b = self.survey["type"].loc[self.survey["name"] == a]
            if len(b) == 0:
                pass
            else:
                b = b.iloc[0].split(" ")[0]
                if b in list(func.keys()):
                    for j in range(len(df)):
                        if pd.isna(df[i].iloc[j]):
                            pass
                        else:
                            try:
                                df[i].iat[j] = func[b](a, df[i].iat[j])
                            except:
                                pass

        df = df.loc[df["ReviewState"] != "rejected"]

        if process_datetimes:
            df["SubmissionDate"] = pd.to_datetime(
                df["SubmissionDate"], format="%Y-%m-%dT%H:%M:%S.%fZ")
            df["start"] = pd.to_datetime(df["start"], format="%Y-%m-%dT%H:%M:%S.%f%z")

            for j in self.survey["name"].loc[self.survey["type"] == "datetime"]:
                try:
                    df[j] = pd.to_datetime(df[j], format="%Y-%m-%dT%H:%M:%S.%f%z")
                except:
                    df[j] = pd.to_datetime(df[j], format="mixed")

            for j in self.survey["name"].loc[self.survey["type"] == "date"]:
                try:
                    df[j] = pd.to_datetime(df[j], format="%Y-%m-%d").dt.date
                except:
                    pass

            for j in self.survey["name"].loc[self.survey["type"] == "time"]:
                try:
                    df[j] = pd.to_datetime(df[j], format="%H:%M:%S.%f%z").dt.time
                except:
                    pass
        
        return df

    def processing_repeats(self, data=None, process_datetimes=False):
        
        repeats = self.get_repeats()
        df = self.processing_submission() if type(data) == type(None) else data
        set_not_rejected = list(df["KEY"])
        def remove_tail(list_in):
            a = []
            for j in list_in:
                if j[-2:] == ".0":
                    a.append(j[:-2])
                else:
                    a.append(j)
            return a

        def select_one(select, value):
            x = self.survey["type"].loc[self.survey["name"] == select].iloc[0].split(" ")[
                1]
            y = self.choices["label::English (en)"].loc[self.choices["list_name"]
                                                   == x].loc[self.choices["name"] == value].iloc[0]
            return y

        def select_multiple(select, value):
            x = self.survey["type"].loc[self.survey["name"] == select].iloc[0].split(" ")[
                1]
            y = self.choices.loc[self.choices["list_name"] == x]
            z = []
            for i in range(len(y)):
                if str(y["name"].iloc[i]) in remove_tail(list(str(value).split(" "))):
                    z.append(y["label::English (en)"].iloc[i])
            return " \n".join(z)

        def select_one_from_file(select, value):
            x = self.survey["type"].loc[self.survey["name"] == select].iloc[0].split(" ")[
                1]
            y = pd.read_csv(x)
            z = y["label"].loc[y["name"] == value].iloc[0]
            return z

        func = {"select_one_from_file": select_one_from_file,
                "select_one": select_one, "select_multiple": select_multiple}

        group_names = list(self.survey["name"].loc[self.survey["type"] == "begin_group"])
        group_names = sorted(group_names, key=len, reverse=True)

        column_names = sorted(list(set(self.survey["name"].loc[((self.survey["type"] != "begin_group") & (self.survey["type"] != "end_group") & (
            self.survey["type"] != "begin_repeat") & (self.survey["type"] != "end_repeat"))]).difference(set([np.nan]))), key=len, reverse=True)


        for k in repeats.keys():
            for i in repeats[k].columns:
                # try:
                a = i
                b = self.survey["type"].loc[self.survey["name"] == a]
                if len(b) == 0:
                    pass
                else:
                    b = b.iloc[0].split(" ")[0]
                    if b in list(func.keys()):
                        for j in range(len(repeats[k])):
                            if pd.isna(repeats[k][i].iloc[j]):
                                pass
                            else:
                                try:
                                    repeats[k][i].iat[j] = func[b](
                                        a, repeats[k][i].iat[j])
                                except:
                                    pass

        for j in repeats.keys():

            repeats[j] = repeats[j].loc[[True if repeats[j]["PARENT_KEY"].iloc[i].split(
                "/")[0] in set_not_rejected else False for i in range(len(repeats[j]))]]
            
            if process_datetimes:

                for i in self.survey["name"].loc[self.survey["type"] == "datetime"]:
                    if i in repeats[j].columns:
                        try:
                            repeats[j][i] = pd.to_datetime(
                                repeats[j][i], format="%Y-%m-%dT%H:%M:%S.%f%z")
                        except:
                            repeats[j][i] = pd.to_datetime(
                                repeats[j][i], format="mixed")

                for i in self.survey["name"].loc[self.survey["type"] == "date"]:
                    if i in repeats[j].columns:
                        try:
                            repeats[j][i] = pd.to_datetime(
                                repeats[j][i], format="%Y-%m-%d").dt.date
                        except:
                            repeats[j][i] = pd.to_datetime(
                                repeats[j][i], format="mixed").dt.date

                for i in self.survey["name"].loc[self.survey["type"] == "time"]:
                    if i in repeats[j].columns:
                        try:
                            repeats[j][i] = pd.to_datetime(
                                repeats[j][i], format="%H:%M:%S.%f%z").dt.time
                        except:
                            repeats[j][i] = pd.to_datetime(
                                repeats[j][i], format="mixed").dt.time


        return repeats

    def process_all(self, variable='', time_variable='start', process_datetimes=False):
        
        submissions = self.processing_submission(process_datetimes=process_datetimes)
        survey = self.survey.dropna(how='all')
        choices = self.choices
        repeats = self.processing_repeats(process_datetimes=process_datetimes)
        survey_name = self.form_name
        variable = variable
        time_variable = time_variable
        media = self.get_media()
        attachments = self.get_attachments()

        return Form(submissions,survey,choices,repeats,survey_name,variable,time_variable,media,attachments)

    def save_main(self,data=None,path=""):
        

        df = self.processing_submission() if type(data) == type(None) else data

        df_out = copy.deepcopy(df)

        for j in df_out.select_dtypes(include=['datetime64', 'datetimetz']).columns:
            df_out[j] = df_out[j].astype(str)
        df_out['start'] = df_out['start'].astype(str)
        a = []
        for j in df.columns:
            if j in list(self.survey["name"]):
                x = self.survey["label::English (en)"].loc[self.survey["name"] == j].iloc[0]
                a.append(x)
            else:
                a.append(np.nan)

        df_out.loc[-1] = a

        df_out.sort_index(inplace=True)

        save_to_excel(df_out, path+self.form_name+"_submissions.xlsx")

    def save_repeat(self,data=None, path=""):
        
        repeats = self.processing_repeats() if type(data) == type(None) else data

        for k in repeats.keys():

            rep_out = copy.deepcopy(repeats[k])

            for j in rep_out.select_dtypes(include=['datetime64', 'datetimetz']).columns:
                rep_out[j] = rep_out[j].astype(str)

            a = []
            for j in repeats[k].columns:
                if j in list(self.survey["name"]):
                    x = self.survey["label::English (en)"].loc[self.survey["name"] == j].iloc[0]
                    a.append(x)
                else:
                    a.append(np.nan)

            rep_out.loc[-1] = a

            rep_out.sort_index(inplace=True)

            save_to_excel(rep_out, path+k+".xlsx")

    def save_data(self, path=""):
        
        req = requests.get(self.url+'/v1/projects/'+str(self.project) +
                           "/forms/"+self.form+".xlsx", headers=self.headers).content

        version = str(pd.read_excel(BytesIO(req),
                                    sheet_name="settings")["version"].iloc[0])
        req = (requests.post(self.url+'/v1/projects/' +
                             str(self.project)+"/forms/" +
                             self.form+"/submissions.csv.zip?",
                             headers=self.headers))

        file = open(path+self.form_name+"_v"+version+".zip", "wb")
        file.write(req.content)
        file.close()

    def listing_submissions(self):
        
        req = (requests.get(self.url+'/v1/projects/' +
                            str(self.project)+"/forms/"+self.form+"/submissions",
                            headers=self.headers))
        return req.json()

    def get_submission_metadata(self,instance):
        
        req = (requests.get(self.url+'/v1/projects/' +
                            str(self.project)+"/forms/" +
                            self.form+"/submissions/"+instance,
                            headers=self.headers))
        return req.json()
    
    def get_submission_xml(self,instance):
        
        req = (requests.get(self.url+'/v1/projects/' +
                            str(self.project)+"/forms/" +
                            self.form+"/submissions/"+instance+".xml",
                            headers=self.headers))
        return req.content

    def put_submission(self, instance, data):
        
        req = (requests.put(url=self.url+'/v1/projects/' +
                            str(self.project)+"/forms/" +
                            self.form+"/submissions/"+instance,data=data,
                            headers=self.headers))
        return req


    def get_parent_tag(self,tag):

        
        n = self.survey.loc[self.survey['name'] == tag].index[0]
        begin_group = len(
            self.survey.iloc[:n].loc[self.survey['type'] == 'begin_group'])
        end_group = len(
            self.survey.iloc[:n].loc[self.survey['type'] == 'end_group'])
        begin_repeat = len(
            self.survey.iloc[:n].loc[self.survey['type'] == 'begin_repeat'])
        end_repeat = len(
            self.survey.iloc[:n].loc[self.survey['type'] == 'end_repeat'])

        if end_repeat < begin_repeat:
            return (self.survey['name'].iloc[:n].loc[self.survey['type'] == 'begin_repeat']).iloc[-1]
        elif end_group < begin_group:
            return (self.survey['name'].iloc[:n].loc[self.survey['type'] == 'begin_group']).iloc[-1]
        else:
            return None

    def return_element(self,tree, data: str):
        for elem in tree.iter():
            if elem.tag == data:
                return elem
            else:
                pass
        return None

    def modify_variable_xml(self, xml, variable: str, function):
        tree = ET.parse(BytesIO(xml))
        d = self.return_element(tree, variable)
        if d == None:
            print(f"{variable} is not in the xml")
            return xml
        else:
            try:
                k = d.text
                d.text = function(k)
                xml_out = BytesIO()
                tree.write(xml_out, encoding='utf-8')
                return xml_out.getvalue()
            except:
                print('an error occurred while processing for variable ', variable)
                return xml

    def update_xml(self, xml):

        tree = ET.parse(BytesIO(xml))
        root = tree.getroot()
      
        if tree.find('meta').find('deprecatedID') == None:
            old = tree.find('meta').find('instanceID').text
            tree.find('meta').find(
                'instanceID').text = 'uuid:'+str(uuid.uuid4())
            deprecated = ET.Element("deprecatedID")
            deprecated.text = old
            root.find('meta').append(deprecated)

        else:
            if len(tree.find('meta').find('deprecatedID').text)>0:
                old = tree.find('meta').find('instanceID').text
                tree.find('meta').find('instanceID').text = 'uuid:'+str(uuid.uuid4())
                root.find('meta').find('deprecatedID').text = old
        xml_out = BytesIO()
        tree.write(xml_out, encoding='utf-8')
        return xml_out.getvalue()

    def change_submission(self, xml, id):
            self.put_submission(id, self.update_xml(xml))


    def drop_variable_xml(self, xml,variable: str,parent_tag=None):

        tree = ET.parse(BytesIO(xml))
        root = tree.getroot()
        for elem in tree.iter():
            if elem.tag == variable:
                if parent_tag == None:
                    root.remove(elem)
                else:
                    self.return_element(tree, parent_tag).remove(elem)
        xml_out = BytesIO()
        tree.write(xml_out, encoding='utf-8')
        return xml_out.getvalue()

    def add_variable_xml(self, xml, variable: str, parent_tag=None):

        tree = ET.parse(BytesIO(xml))
        root = tree.getroot()
        if type(self.return_element(tree,variable)) == type(None):
            if parent_tag == None:
                child = ET.SubElement(root, variable)
            else:
                child = ET.SubElement(self.return_element(tree, parent_tag),variable)
            xml_out = BytesIO()
            tree.write(xml_out, encoding='utf-8')
            return xml_out.getvalue()

