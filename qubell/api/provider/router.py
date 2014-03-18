import os

import requests
from requests.auth import HTTPBasicAuth

from qubell.api.private.exceptions import ApiUnauthorizedError
from qubell.api.provider import route, play_auth, basic_auth


class Router(object):
    def __init__(self, base_url, verify_ssl=False, verify_codes=True):
        self.base_url = base_url
        self.verify_ssl = verify_ssl
        self.verify_codes = verify_codes

        self._cookies = None
        self._auth = None

    @property
    def is_connected(self):
        return self._cookies and 'PLAY_SESSION' in self._cookies

    #todo: add integration test for this
    def connect(self, email, password):
        url = self.base_url + '/signIn'
        data = {
            'email': email,
            'password': password}
        with requests.session() as session:
            session.post(url=url, data=data, verify=self.verify_ssl)
            self._cookies = session.cookies

        if not self.is_connected:
            raise ApiUnauthorizedError("Authentication failed, please check settings")

        self._auth = HTTPBasicAuth(email, password)

class PrivatePath(Router):

    @route("POST /signIn")
    def post_sign_in(self, body): pass

    @route("GET /404")
    def get_404(self): pass

    #Organization
    @play_auth
    @route("POST /organizations{ctype}")
    def post_organization(self, data, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations{ctype}")
    def get_organizations(self, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations/{org_id}{ctype}")
    def get_organization(self, org_id, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/applications{ctype}")
    def post_organization_application(self, org_id, data, files, cookies, ctype=".json"): pass

    @play_auth
    @route("PUT /organizations/{org_id}/defaultEnvironment{ctype}")
    def put_organization_default_environment(self, org_id, env_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/applications/{app_id}/launch{ctype}")
    def post_organization_instance(self, org_id, app_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/environments{ctype}")
    def post_organization_environment(self, org_id, data, cookies, ctype=".json"): pass

    #Application
    @play_auth
    @route("GET /organizations/{org_id}/applications{ctype}")
    def get_applications(self, org_id, cookies, data="{}", ctype=".json"): pass

    @play_auth
    @route("PUT /organizations/{org_id}/applications/{app_id}{ctype}")
    def put_application(self, org_id, app_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations/{org_id}/applications/{app_id}{ctype}")
    def get_application(self, org_id, app_id, cookies, data="{}", ctype=".json"): pass

    @play_auth
    @route("DELETE /organizations/{org_id}/applications/{app_id}{ctype}")
    def delete_application(self, org_id, app_id, cookies, data="{}", ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/applications/{app_id}/refreshManifest{ctype}")
    def post_application_refresh(self, org_id, app_id, cookies, data="{}", ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/applications/{app_id}/manifests{ctype}")
    def post_application_manifest(self, org_id, app_id, data, files, cookies, ctype=".json"): pass

    #Revision
    @play_auth
    @route("POST /organizations/{org_id}/applications/{app_id}/revisions{ctype}")
    def post_revision(self, org_id, app_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations/{org_id}/applications/{app_id}/revisions/{rev_id}{ctype}")
    def get_revision(self, org_id, app_id, rev_id, cookies, ctype=".json"): pass

    @play_auth
    @route("DELETE /organizations/{org_id}/applications/{app_id}/revisions/{rev_id}{ctype}")
    def delete_revision(self, org_id, app_id, rev_id, cookies, data="{}", ctype=".json"): pass

    #Instance
    @play_auth
    @route("GET /organizations/{org_id}/dashboard{ctype}")
    def get_instances(self, org_id, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations/{org_id}/instances/{instance_id}{ctype}")
    def get_instance(self, org_id, instance_id, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/instances/{instance_id}/workflows/{wf_name}{ctype}")
    def post_instance_workflow(self, org_id, instance_id, wf_name, cookies, data="{}", ctype=".json"): pass

    @play_auth
    @route("PUT /organizations/{org_id}/instances/{instance_id}/configuration{ctype}")
    def put_instance_configuration(self, org_id, instance_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/environments/updateServiceEnvs/{instance_id}{ctype}")
    def post_instance_services(self, org_id, instance_id, data, cookies, ctype=".json"): pass

    #Environment
    @play_auth
    @route("GET /organizations/{org_id}/environments{ctype}")
    def get_environments(self, org_id, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations/{org_id}/environments/{env_id}{ctype}")
    def get_environment(self, org_id, env_id, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations/{org_id}/environments/{env_id}/availableServices{ctype}")
    def get_environment_available_services(self, org_id, env_id, cookies, ctype=".json"): pass

    @play_auth
    @route("PUT /organizations/{org_id}/environments/{env_id}{ctype}")
    def put_environment(self, org_id, env_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("DELETE /organizations/{org_id}/environments/{env_id}{ctype}")
    def delete_environment(self, org_id, env_id, cookies, data="{}", ctype=".json"): pass

    #Zone
    @play_auth
    @route("GET /organizations/{org_id}/zones{ctype}")
    def get_zones(self, org_id, cookies, ctype=".json"): pass

    #CloudProvider
    @play_auth
    @route("GET /organizations/{org_id}/providers{ctype}")
    def get_providers(self, org_id, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/providers{ctype}")
    def post_provider(self, org_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("DELETE /organizations/{org_id}/providers/{prov_id}{ctype}")
    def delete_provider(self, org_id, prov_id, cookies, ctype=".json"): pass

    #Service
    @play_auth
    @route("GET /organizations/{org_id}/services{ctype}")
    def get_services(self, org_id, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/services/{instance_id}/keys/generate{ctype}")
    def post_service_generate(self, org_id, instance_id, cookies, data="{}", ctype=".json"): pass

class PublicPath(PrivatePath):
    """
    # Endpoint API
    POST    /api/1/applications/:id/launch                      boot.Boot.application.apiLaunch(id:String)
    PUT     /api/1/applications/:id/manifest                    boot.Boot.application.apiPutManifest(id:String)
    GET     /api/1/applications/:id/revisions                   boot.Boot.application.apiListRevisions(id)
    GET     /api/1/instances/:id                                boot.Boot.instance.apiStatus(id)
    POST    /api/1/instances/:id/:workflow                      boot.Boot.instance.apiRunWorkflow(id, workflow)
    GET     /api/1/environments/:id                             boot.Boot.environment.apiExport(id)
    PUT     /api/1/environments/:id                             boot.Boot.environment.apiImport(id)
    # not sure about the path
    POST    /api/1/organizations/:orgId/serviceTypes                    boot.Boot.services.apiCreateType(orgId)
    GET     /api/1/organizations/:orgId/applications            boot.Boot.application.apiList(orgId)
    GET     /api/1/organizations/:orgId/environments            boot.Boot.environment.apiList(orgId)
    GET     /api/1/organizations                                boot.Boot.organizations.apiList

    GET     /api/1/revisions/:revId/instances                   boot.Boot.instance.apiGetInstancesForRevision(revId)
    GET     /api/1/environments/:envId/instances                boot.Boot.instance.apiGetInstancesForEnvironment(envId)
    GET     /api/1/environments/:envId/markers     boot.Boot.environment.apiGetMarkers(envId)
    PUT     /api/1/environments/:envId/markers     boot.Boot.environment.apiUpdateMarkers(envId)
    GET     /api/1/environments/:envId/properties  boot.Boot.environment.apiGetProperties(envId)
    PUT     /api/1/environments/:envId/properties  boot.Boot.environment.apiUpdateProperties(envId)

    GET     /api/1/services/:serviceId                         boot.Boot.services.apiGet(serviceId)
    PUT     /api/1/services/:serviceId                         boot.Boot.services.apiUpdate(serviceId)
    POST    /api/1/services/:serviceId/:command                boot.Boot.services.apiExecute(serviceId, command)

    GET     /applications/upload                               boot.Boot.application.externalUploadGet(metadataUrl: Option[String] ?= None)
    POST    /applications/upload                               boot.Boot.application.externalUpload

    PUT     /api/1/instances/:id/userData                      boot.Boot.instance.apiSetUserData(id)

    # Utility routes
    GET     /utilities/expression                              boot.Boot.expression.view
    POST    /utilities/expression.json                         boot.Boot.expression.evaluate

    POST    /api/1/migrate/:timeout                            boot.Boot.instance.migrate(timeout: Long)
    POST    /api/1/migrate-envs/:timeout                       boot.Boot.environment.migrate(timeout: Long)
    """

#Organization

    @basic_auth
    @route("GET /api/1/organizations")
    def get_organizations(self, auth): pass

#Application
    @basic_auth
    @route("POST /api/1/applications/{app_id}/launch")
    def post_organization_instance(self, org_id, app_id, data, auth): pass

    # TODO: Error here!!!!
    #@basic_auth
    #@route("PUT /api/1/applications/{app_id}/manifest")
    #def post_application_manifest(self, org_id, app_id, data, files, auth): pass

    @basic_auth
    @route("GET /api/1/organizations/{org_id}/applications")
    def get_applications(self, org_id, auth, data="{}"): pass

    @basic_auth
    @route("GET /api/1/applications/{app_id}/revisions")
    def get_revisions(self, org_id, app_id, rev_id, auth): pass

#Instance
    @basic_auth
    @route("GET /api/1/instances/{instance_id}")
    def get_instance(self, org_id, instance_id, auth): pass

    @basic_auth
    @route("POST /api/1/instances/{instance_id}/{wf_name}")
    def post_instance_workflow(self, org_id, instance_id, wf_name, auth, data="{}"): pass

# Environment
    # It returns policies yaml... Not usable
    #@basic_auth
    #@route("GET /api/1/environments/{env_id}")
    #def get_environment(self, org_id, env_id, auth): pass

    # TODO: Expected Yaml as payload..
    #@basic_auth
    #@route("PUT /api/1/environments/{env_id}")
    #def put_environment(self, org_id, env_id, data, auth): pass

    @basic_auth
    @route("GET /api/1/organizations/{org_id}/environments")
    def get_environments(self, org_id, auth): pass

# Revisions



""" here routes not used
    @play_auth
    @route("POST /organizations/{org_id}/environments{ctype}")
    def post_organization_environment(self, org_id, data, cookies, ctype=".json"): pass

    #Application


    @play_auth
    @route("PUT /organizations/{org_id}/applications/{app_id}{ctype}")
    def put_application(self, org_id, app_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations/{org_id}/applications/{app_id}{ctype}")
    def get_application(self, org_id, app_id, cookies, data="{}", ctype=".json"): pass

    @play_auth
    @route("DELETE /organizations/{org_id}/applications/{app_id}{ctype}")
    def delete_application(self, org_id, app_id, cookies, data="{}", ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/applications/{app_id}/refreshManifest{ctype}")
    def post_application_refresh(self, org_id, app_id, cookies, data="{}", ctype=".json"): pass


    #Revision
    @play_auth
    @route("POST /organizations/{org_id}/applications/{app_id}/revisions{ctype}")
    def post_revision(self, org_id, app_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations/{org_id}/applications/{app_id}/revisions/{rev_id}{ctype}")
    def get_revision(self, org_id, app_id, rev_id, cookies, ctype=".json"): pass

    @play_auth
    @route("DELETE /organizations/{org_id}/applications/{app_id}/revisions/{rev_id}{ctype}")
    def delete_revision(self, org_id, app_id, rev_id, cookies, data="{}", ctype=".json"): pass

    #Instance
    @play_auth
    @route("GET /organizations/{org_id}/dashboard{ctype}")
    def get_instances(self, org_id, cookies, ctype=".json"): pass

    @play_auth
    @route("PUT /organizations/{org_id}/instances/{instance_id}/configuration{ctype}")
    def put_instance_configuration(self, org_id, instance_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/environments/updateServiceEnvs/{instance_id}{ctype}")
    def post_instance_services(self, org_id, instance_id, data, cookies, ctype=".json"): pass

    #Environment

    @play_auth
    @route("GET /organizations/{org_id}/environments/{env_id}/availableServices{ctype}")
    def get_environment_available_services(self, org_id, env_id, cookies, ctype=".json"): pass

    @play_auth
    @route("DELETE /organizations/{org_id}/environments/{env_id}{ctype}")
    def delete_environment(self, org_id, env_id, cookies, data="{}", ctype=".json"): pass

    #Zone
    @play_auth
    @route("GET /organizations/{org_id}/zones{ctype}")
    def get_zones(self, org_id, cookies, ctype=".json"): pass

    #CloudProvider
    @play_auth
    @route("GET /organizations/{org_id}/providers{ctype}")
    def get_providers(self, org_id, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/providers{ctype}")
    def post_provider(self, org_id, data, cookies, ctype=".json"): pass

    @play_auth
    @route("DELETE /organizations/{org_id}/providers/{prov_id}{ctype}")
    def delete_provider(self, org_id, prov_id, cookies, ctype=".json"): pass

    #Service
    @play_auth
    @route("GET /organizations/{org_id}/services{ctype}")
    def get_services(self, org_id, cookies, ctype=".json"): pass

    @play_auth
    @route("POST /organizations/{org_id}/services/{instance_id}/keys/generate{ctype}")
    def post_service_generate(self, org_id, instance_id, cookies, data="{}", ctype=".json"): pass

"""


if os.environ.get('QUBELL_USE_PUBLIC', None):
    ROUTER = PublicPath(os.environ.get('QUBELL_TENANT'))
else:
    ROUTER = PrivatePath(os.environ.get('QUBELL_TENANT'))