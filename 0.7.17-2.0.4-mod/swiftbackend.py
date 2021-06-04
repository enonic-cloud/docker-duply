# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2013 Matthieu Huin <mhu@enovance.com>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os

import duplicity.backend
from duplicity import log
from duplicity import util
from duplicity.errors import BackendException


class SwiftBackend(duplicity.backend.Backend):
    """
    Backend for Swift
    """
    def __init__(self, parsed_url):
        duplicity.backend.Backend.__init__(self, parsed_url)

        try:
            from swiftclient import ClientException
            from swiftclient.service import SwiftError, SwiftService, SwiftUploadObject
        except ImportError as e:
            raise BackendException("""\
Swift backend requires the python-swiftclient library.
Exception: %s""" % str(e))

        self.resp_exc = ClientException
        self.err = SwiftError
        self.upload_object = SwiftUploadObject
        options = {}

        # if the user has already authenticated
        if 'SWIFT_PREAUTHURL' in os.environ and 'SWIFT_PREAUTHTOKEN' in os.environ:
            options['os_storage_url'] = os.environ['SWIFT_PREAUTHURL']
            options['auth_token'] = os.environ['SWIFT_PREAUTHTOKEN']

        else:
            if 'SWIFT_USERNAME' not in os.environ:
                raise BackendException('SWIFT_USERNAME environment variable '
                                       'not set.')

            if 'SWIFT_PASSWORD' not in os.environ:
                raise BackendException('SWIFT_PASSWORD environment variable '
                                       'not set.')

            if 'SWIFT_AUTHURL' not in os.environ:
                raise BackendException('SWIFT_AUTHURL environment variable '
                                       'not set.')

            options['os_username'] = os.environ['SWIFT_USERNAME']
            options['os_password'] = os.environ['SWIFT_PASSWORD']
            options['os_auth_url'] = os.environ['SWIFT_AUTHURL']

        if 'SWIFT_SEGMENT_SIZE' in os.environ:
            if int(os.environ['SWIFT_SEGMENT_SIZE']) > 0:
                options['segment_size'] = os.environ['SWIFT_SEGMENT_SIZE']
                options['use_slo'] = True
        else: 
            options['segment_size'] = 1024 * 1024 * 1024
            options['use_slo'] = True

        if 'SWIFT_AUTHVERSION' in os.environ:
            options['auth_version'] = os.environ['SWIFT_AUTHVERSION']
            if os.environ['SWIFT_AUTHVERSION'] == '3':
                if 'SWIFT_USER_DOMAIN_NAME' in os.environ:
                    options['os_user_domain_name'] = os.environ['SWIFT_USER_DOMAIN_NAME']
                if 'SWIFT_USER_DOMAIN_ID' in os.environ:
                    options['os_user_domain_id'] = os.environ['SWIFT_USER_DOMAIN_ID']
                if 'SWIFT_PROJECT_DOMAIN_NAME' in os.environ:
                    options['os_project_domain_name'] = os.environ['SWIFT_PROJECT_DOMAIN_NAME']
                if 'SWIFT_PROJECT_DOMAIN_ID' in os.environ:
                    options['os_project_domain_id'] = os.environ['SWIFT_PROJECT_DOMAIN_ID']
                if 'SWIFT_TENANTNAME' in os.environ:
                    options['os_tenant_name'] = os.environ['SWIFT_TENANTNAME']
                if 'SWIFT_ENDPOINT_TYPE' in os.environ:
                    options['os_endpoint_type'] = os.environ['SWIFT_ENDPOINT_TYPE']
                if 'SWIFT_USERID' in os.environ:
                    options['os_user_id'] = os.environ['SWIFT_USERID']
                if 'SWIFT_TENANTID' in os.environ:
                    options['os_tenant_id'] = os.environ['SWIFT_TENANTID']
                if 'SWIFT_REGIONNAME' in os.environ:
                    options['os_region_name'] = os.environ['SWIFT_REGIONNAME']

        else:
            options['auth_version'] = '1'
        if 'SWIFT_TENANTNAME' in os.environ:
            options['os_tenant_name'] = os.environ['SWIFT_TENANTNAME']
        if 'SWIFT_REGIONNAME' in os.environ:
            options['os_region_name'] = os.environ['SWIFT_REGIONNAME']

        # This folds the null prefix and all null parts, which means that:
        #  //MyContainer/ and //MyContainer are equivalent.
        #  //MyContainer//My/Prefix/ and //MyContainer/My/Prefix are equivalent.
        url_parts = [x for x in parsed_url.path.split('/') if x != '']

        self.container = url_parts.pop(0)
        if url_parts:
            self.prefix = '%s/' % '/'.join(url_parts)
        else:
            self.prefix = ''

        try:
            self.service = SwiftService(options=options)
        except ClientException:
            pass
        except Exception as e:
            log.FatalError("Connection failed: %s %s"
                           % (e.__class__.__name__, str(e)),
                           log.ErrorCode.connection_failed)

    def _error_code(self, operation, e):
        if isinstance(e, self.resp_exc):
            if e.http_status == 404:
                return log.ErrorCode.backend_not_found

    def _put(self, source_path, remote_filename):
        try:
            for r in self.service.upload(self.container, [
                self.upload_object(source_path.name,object_name=self.prefix + remote_filename)
                ]):
                if not r['success']:
                    error = r['error']
                    if r['action'] == "create_container":
                        log.Warn("Warning: failed to create container %s %s" %(self.container, error))
                    elif r['action'] == "upload_object":
                        log.FatalError(
                            "Failed to upload object %s to container %s: %s" %
                            (r['object'], self.container, error)
                        )
                    else:
                        log.FatalError("%s" % error)
        except self.err as e:
            log.FatalError(e.value)

    def _get(self, remote_filename, local_path):
        for down_res in self.service.download(container=self.container, 
            objects=[self.prefix + remote_filename], options={'out_file': local_path.name}):
            if not down_res['success']:
                log.FatalError("Failed to download object %s/%s to file %s: %s" %
                    (self.container, down_res['object'], local_path, down_res['error']))

    def _list(self):
        try:
            objects = []
            for page in self.service.list(container=self.container):
                if page["success"]:
                    for item in page["listing"]:
                       objects.append(item['name'][len(self.prefix):])
            return objects
        except self.err as e:
            log.FatalError(e.value)

    def _delete(self, filename):
        for del_res in self.service.delete(container=self.container, 
            objects=[self.prefix + filename]):
            if not del_res['success']:
                log.FatalError("Failed to delete object %s/%s: %s" %
                    (self.container, filename, del_res['error']))

    def _query(self, filename):
        for stat_res in self.service.stat(container=self.container,objects=[self.prefix + filename]):
            if stat_res['success']:
                return {'size': int(stat_res['headers']['content-length'])}

duplicity.backend.register_backend("swift", SwiftBackend)
