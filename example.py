from odk_tools.classes import Form
from odk_tools.odk import ODK
from getpass import getpass

#The following script illustrates the main functionalities of the package.

odk = ODK(input("Type the url of the odk webserver you are connecting to: ")) #The ODK class should be instantiated providing the URL of the webserver

#connecting to the webserver by providing username and password is required before any useful method of the ODK class can be used
odk.connect(email=input('enter your username'),password=input('enter your password'))

#returns a list of the project names the connected user has access to on ODK Central
odk.list_projects()

#returns a list of the forms under the project named 'project name'
odk.list_forms(project='project name')

#connect to a specific form under a project
odk.set_target("project_name","form_name")

#returns the ID corresponding to the project name
odk.get_project()

#returns the ID corresponding to the form name
odk.get_form()

#saves the xlsx form
odk.save_form(xlsx="form",path="")

#saves the whole submissions dataset as a zip file
odk.save_data(path="")

#returns a dataframe of the submissions csv
odk.get_submissions()

#returns a dataframe of the submissions csv
odk.get_submissions()
