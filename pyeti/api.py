#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Python interface to the Yeti REST API."""

import logging
import os
import time

import requests


class YetiApi(object):
    """Python interface to the Yeti REST API."""

    def __init__(self, url, auth=tuple(), api_key=None, verify_ssl=True):
        super(YetiApi, self).__init__()
        if not url.endswith('/'):
            url += "/"
        self.yeti_url = url
        self.auth = auth
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self._test_connection()

    def entity_search(self, count=50, offset=1, regex=False, **kwargs):
        """Fetches a list of indicators associated with an Entity.
            :param count: How many Entities you want to fetch.
            :type count: int
            :param offset: How many sets of *count* Entities you want to skip
                    (total skipped = offset * count)
            :type offset: int
            :param regex: Use regular expressions to Search.
            :type regex: bool
            :param kwargs: Remaining keyword arguments will be transformed in a JSON
                    object that will act as the filter.
            :type kwargs: dict
          :return: A list of indicators.
        """
        json = {
            "filter": kwargs,
            "params": {
                "page": offset,
                "range": count,
                "regex": regex
            }
        }
        return self._make_post("entitysearch/", json=json)

    def entity_get(self, entity_id):
        """Fetches an entity by ID.
            :param entity_id: ID of the entity
        Returns:
           JSON representation of the requested Entity."""
        return self._make_get("entity/{}".format(entity_id))

    def related_indicators(self, entity, **kwargs):
        """Fetches indicators linked to a given entity.
           :param entity: JSON dict representing the Entity to search indicators for.
           :type entity: str
           :param kwargs: Remaining keyword arguments will be transformed in a JSON
                   object that will act as the filter.
           :return: A list of matching JSON Indicators.
        """
        url = "neighbors/tuples/{0:s}/{1:s}/indicator".format(
            entity['type'], entity['id'])
        json = {"filter": kwargs}
        return self._make_post(url, json=json)

    def analysis_match(self, observables):
        """Matches a list of observables against Yeti indicators.
            :param observables: An array of strings representing observables
            :type observables: list

            :return: JSON representation of match response.
        """
        json = {"observables": observables}
        return self._make_post("analysis/match", json=json)

    def observable_search(self, count=50, offset=1, regex=False, **kwargs):
        """Search for observables.
            :param count: How many Observables you want to fetch.
            :type count: int
            :param offset: How many sets of *count* Observables you want to skip
                    (total skipped = offset * count)
            :type offset: int
            :param regex: Use regular expressions to Search.
            :type regex: bool
            :param kwargs: Remaining keyword arguments will be transformed in a JSON
                    object that will act as the filter.
            :type kwargs: dict
            :return: Array of JSON representations of matching Observables.
        """
        json = {"filter": kwargs, "params": {"page": offset, "range": count, "regex": regex}}
        return self._make_post("observablesearch/", json=json)

    def observable_details(self, objectid):
        """Get details on an Observable.
            :param objectid: A string representing the observable's ObjectID
            :type objectid: str
            :return: JSON representation of the requested Observable.
        """
        return self._make_get("observable/{}".format(objectid))

    def neighbors_observables(self, objectid):
        """
        :param objectid:
        :type objectid: str
        :return: JSON representation of the requested Observable.
        """

        return self._make_post('neighbors/tuples/Observable/%s/Observable' %
                               objectid)

    def entity_to_observables(self, entityid):
        """ Get observables linked to an entity
        :param entityid: id of the entity
        :type entityid: str
        :return: JSON representation of the observables linked to an entity
        """
        return self._make_post('neighbors/tuples/Entity/%s/Observable' %
                               entityid)

    def entity_to_malware(self, entityid):
        return self._entity_to_entities(entityid, 'malware')

    def entity_to_actor(self, entityid):
        return self._entity_to_entities(entityid, 'actor')

    def entity_to_company(self, entityid):
        return self._entity_to_entities(entityid, 'company')

    def entity_to_campaign(self, entityid):
        return self._entity_to_entities(entityid, 'campaign')

    def entity_to_indicator(self, entityid):
        return self._get_observable_to_entities(entityid, 'indicator')

    def entity_to_exploit(self, entityid):
        return self._get_observable_to_entities(entityid, 'exploit')

    def entity_to_exploitkit(self, entityid):
        return self._get_observable_to_entities(entityid, 'exploitkit')

    def _entity_to_entities(self, entityid, entity_name):
        """
        Get entities linked to an entity
        :param entityid: id of the entity
        :type entityid: str
        :return: JSON representation of the entities linked to an entity
        """
        return self._make_post('neighbors/tuples/entity/%s/%s' %
                               (entityid, entity_name))

    def observable_to_malware(self, objectid):
        return self._get_observable_to_entities(objectid, 'malware')

    def observable_to_actor(self, objectid):
        return self._get_observable_to_entities(objectid, 'actor')

    def observable_to_company(self, objectid):
        return self._get_observable_to_entities(objectid, 'company')

    def observable_to_campaign(self, objectid):
        return self._get_observable_to_entities(objectid, 'campaign')

    def observable_to_indicator(self, objectid):
        return self._get_observable_to_entities(objectid, 'indicator')

    def observable_to_exploit(self, objectid):
        return self._get_observable_to_entities(objectid, 'exploit')

    def observable_to_exploitkit(self, objectid):
        return self._get_observable_to_entities(objectid, 'exploitkit')

    def _get_observable_to_entities(self, objectid, entity_name):
        """
        Get entities linked to an observable
        :param objectid: id of the observable
        :type objectid: str
        :return: JSON representation of the entities linked to an observable
        """
        return self._make_post('neighbors/tuples/observable/%s/%s' %
                               (objectid, entity_name))

    def observable_add(self, value, tags=None, context=None, source="API"):
        """Add an observable to the dataset
            :param value: the Observable value
            :type value: str
            :param tags: list of strings representing tags
            :type tags: list
            :param context: A dictionary object with context information
            :type context: dict
            :param source: A string representing the source of the data. Defaults to
                    "API".
            :type source: str
            :return: dict JSON representation of the created observable.
        """
        if tags is None:
            tags = []
        if context is None:
            context = {}
        json = {
            "tags": tags,
            "value": value,
            "source": source,
            "context": context
        }
        return self._make_post('observable/', json=json)

    def observable_change(self, objectid, tags=None, context=None):
        """Add tags to an observable.

            objectid: The observable's ObjectID
            tags: Tags to add
            context: Context to add

        Returns:
            JSON representation of the updated observable
        """
        if tags is None:
            tags = []
        if context is None:
            context = {}
        json = {"id": objectid, "tags": tags, "context": context}
        result = self._make_post('observable/', json=json)
        return result

    def observable_delete(self, objectid):
        """Deletes an observable.


            :param objectid: The observable's ObjectID
            :type objectid:str
            :return: Operation status in JSON.
        """
        self._make_delete('observable/{}'.format(objectid))
        return {'status': 'deleted', 'id': objectid}

    def observable_file_add(self, path, tags=None, context=None):
        """Upload a file to the dataset
            :param path: The path to the file
            :param tags: An array of strings representing tags
            :param context: A dictionary object with context information
            :param source: A string representing the source of the data. Defaults to
                    "API".
            :return:JSON representation of the created observable.
        """
        if tags is None:
            tags = []
        if context is None:
            context = {}
        path = os.path.realpath(os.path.normpath(os.path.expanduser(path)))
        filename = os.path.basename(path)
        files = {'files': (filename, open(path, 'rb'))}
        fileinfos = self._make_post(
            'file/addfile',
            files=files
        )
        if not (tags or context):
            return fileinfos

        updated_fileinfo = []
        for info in fileinfos:
            info = self.observable_change(info['id'], tags, context)
            updated_fileinfo.append(info)

        return updated_fileinfo

    def observable_file_contents(self, objectid=None, filehash=None):
        """Fetches the content of a File observable.
            :param objectid: The observable's ObjectID.
            :param filehash: The observable's hash.
            :return: Binary data containing the file's contents.
        """
        if objectid is not None:
            return self._make_get('file/get/id/{}'.format(objectid))
        elif filehash is not None:
            return self._make_get('file/get/hash/{}'.format(filehash))
        else:
            raise ValueError("You need to pass an id or hash parameter.")

    def observable_bulk_add(self, observables, tags=None):
        """Add an observables in bulk mode to the dataset
           :param observables: list observables to add in yeti
            :return JSON representation of the created observable.
        """
        if tags is None:
            tags = []
        json = {"observables": [{"tags": tags, "value": o} for o in observables]}
        return self._make_post('observable/bulk', json=json)

    def get_analytic_oneshot(self, name_of_oneshot):
        all_analytics = self.analytics_oneshot_list()

        if all_analytics:
            oneshot = [item for item in all_analytics
                       if item['name'] == name_of_oneshot]
            if oneshot:
                return oneshot[0]

    def analytics_oneshot_run(self, oneshot, observable):
        """Launch an oneshot analytics on value of an Observable

            :param oneshot: Name of oneshot analytic
            :type oneshot: dict
            :param observable: Observable
            :type observable: dict

            :return:JSON representation of the results of the oneshot analytic .
        """
        result = {}

        one_shot_inst = self._make_post('analytics/oneshot/%s/run' %
                                        oneshot['id'],
                                        data={
                                            'id': observable['id']})

        status = self.analytics_oneshot_status(one_shot_inst['_id'])
        if status:
            while status['status'] == 'running' or \
                    status['status'] == 'pending':
                status = self.analytics_oneshot_status(
                    one_shot_inst['_id'])
                time.sleep(1)
                continue

            if status['status'] == 'finished':
                result = status['results']
                return result
            else:
                logging.error('Error Oneshot Processing %s with %s'
                              , oneshot['id'], observable['value'])
        return result

    def analytics_oneshot_status(self, id_oneshot):
        """Status of an instance of oneshot analytics

            :param id_oneshot: the oneshot analytics ID
            :type id_oneshot: str

            :return:JSON representation of the status of the oneshot analytic.
        """
        status = {}

        if id_oneshot:
            r = self._make_get('analytics/oneshot/%s/status' % id_oneshot)

            if r:
                status = r
                return status
            else:
                logging.error('Error to check status %s', id_oneshot)
        else:
            logging.error('id_oneshot is empty %s', id_oneshot)

        return status

    def analytics_oneshot_list(self):
        """List of oneshot analytics

          :return: JSON representation of the list of the oneshot analytics available
           on Yeti instance.
        """

        list_analytics = []

        r = self._make_get('analytics/oneshot')

        if r:
            list_analytics = r
            return list_analytics
        else:
            logging.error('Error to list oneshot analytics %s',
                          self.yeti_url + 'analytics/oneshot')

        return list_analytics

    def _test_connection(self):
        if self._make_post("observablesearch/"):  # replace this with a more meaningful URL
            logging.debug("Connection to %s successful", self.yeti_url)
        else:
            logging.debug("Conncetion to %s failed", self.yeti_url)

    def _make_post(self, url, **kwargs):
        return self._make_request(url, method="POST", **kwargs)

    def _make_get(self, url):
        return self._make_request(url)

    def _make_delete(self, url):
        return self._make_request(url, method="DELETE")

    def _make_request(self, url, **kwargs):
        url = "{}{}".format(self.yeti_url, url)

        method = kwargs.pop("method", "GET")

        headers = {'Accept': 'application/json'}
        if self.api_key:
            headers.update({"X-Api-Key": self.api_key})
        if method == "POST":
            resp = requests.post(url, headers=headers, auth=self.auth,
            verify=self.verify_ssl, **kwargs)
        if method == "GET":
            resp = requests.get(url, auth=self.auth, headers=headers,
            verify=self.verify_ssl)
        if method == "DELETE":
            resp = requests.delete(url, auth=self.auth, headers=headers,
            verify=self.verify_ssl)

        if resp.status_code == 200:
            logging.debug("Success (%s)", resp.status_code)
            if "json" in resp.headers.get('content-type'):
                return resp.json()
            return resp.content
        else:
            logging.error("An error occurred (%s): %s", resp.status_code, url)

if __name__ == '__main__':
    pass
