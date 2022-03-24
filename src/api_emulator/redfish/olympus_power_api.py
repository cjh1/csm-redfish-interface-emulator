# MIT License
#
# (C) Copyright [2022] Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

# Olympus Power Control API File

"""
Dynamic resources:
 - Power Capping
    GET/PATCH /redfish/v1/Chassis/{sys_id}/Controls/{control_id}
    PATCH     /redfish/v1/Chassis/{sys_id}/Controls.Deep
"""

import g

import sys, traceback
import logging
import copy
from flask import Flask, request, make_response, render_template
from flask_restful import reqparse, Api, Resource

from .response import success_response, simple_error_response, error_404_response, error_not_allowed_response

members = {}

# applyControlPatch
#
# Applies 'SetPoint' and/or 'ControlMode' settings.
# 'SetPoint' must be a value between the Control's 'SettingRangeMin' and 'SettingRangeMax'.
# When 'ControlMode' is set to 'Disabled', 'SetPoint' will be set to 0.
# If 'SetPoint' is not specified in the PATCH and 'ControlMode' is being set to
# something other than 'Disabled', 'SetPoint' will be set to 'SettingRangeMax'.
def applyControlPatch(raw_dict, ch_id, ident):
    # Update specific portions of the identified object
    control = members[ch_id][ident]
    if control['ControlMode'] != 'Disabled' or \
       ('ControlMode' in raw_dict and raw_dict['ControlMode'] != 'Disabled'):
        newSetPoint = control['SetPoint']
        newControlMode = control['ControlMode']
        resp = control, 200
        for field, value in raw_dict.items():
            if field == 'SetPoint':
                min = control['SettingRangeMin']
                max = control['SettingRangeMax']
                if value == 0 or (value >= min and value <= max):
                    if 'ControlMode' in raw_dict and raw_dict['ControlMode'] == 'Disabled':
                        newSetPoint = 0
                    else:
                        newSetPoint = value
                else:
                    resp = simple_error_response('SetPoint out of bounds for %s/Controls/%s' % (ch_id, ident), 400)
                    break
            elif field == 'ControlMode':
                newControlMode = value
                if value == 'Disabled':
                    newSetPoint = 0
                elif value != 'Disabled' and 'SetPoint' not in raw_dict:
                    newSetPoint = control['SettingRangeMax']
            elif field == '@odata.id':
                pass
            else:
                resp = simple_error_response('Invalid setting %s for %s/Controls/%s' % (field, ch_id, ident), 400)
                break
        if resp[1] == 200:
            control['SetPoint'] = newSetPoint
            control['ControlMode'] = newControlMode
    else:
        resp = simple_error_response('Control is disabled for %s/Controls/%s' % (ch_id, ident), 400)
    return resp

# PowerAPI
#
# This services GET and PATCH requests for computer system power controls.
#
class PowerAPI(Resource):

    def __init__(self, **kwargs):
        logging.info('PowerAPI init called')
        self.allow = 'GET, PATCH'

    # HTTP GET
    def get(self, ch_id, ident):
        logging.info('PowerAPI GET called')
        try:
            # Find the entry with the correct value for Id
            resp = error_404_response(request.path)
            if ch_id in members and ident in members[ch_id]:
                resp = members[ch_id][ident], 200
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

    # HTTP PUT
    def put(self, ch_id, ident):
        logging.info('PowerAPI PUT called')
        try:
            resp = error_404_response(request.path)
            if ch_id in members and ident in members[ch_id]:
                resp = error_not_allowed_response(request.path, request.method, {'Allow': self.allow})
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

    # HTTP POST
    def post(self, ch_id, ident):
        logging.info('PowerAPI POST called')
        try:
            resp = error_404_response(request.path)
            if ch_id in members and ident in members[ch_id]:
                resp = error_not_allowed_response(request.path, request.method, {'Allow': self.allow})
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

    # HTTP PATCH
    #
    # Apply power limit to the specified Control
    def patch(self, ch_id, ident):
        logging.info('PowerAPI PATCH called')
        raw_dict = request.get_json(force=True)
        try:
            resp = error_404_response(request.path)
            if ch_id in members and ident in members[ch_id]:
                resp = applyControlPatch(raw_dict, ch_id, ident)
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

    # HTTP DELETE
    def delete(self, ch_id, ident):
        logging.info('PowerAPI DELETE called')
        try:
            resp = error_404_response(request.path)
            if ch_id in members and ident in members[ch_id]:
                resp = error_not_allowed_response(request.path, request.method, {'Allow': self.allow})
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

# CreatePower
#
# Called internally to create instances of a ComputerSystem power control.
# These resources are affected by PowerAPI()
#
class CreatePower(Resource):

    def __init__(self, **kwargs):
        logging.info('CreatePower init called')

    # PUT
    # - Create the resource (since URI variables are avaiable)
    def put(self, ch_id, control_id, config):
        logging.info('CreatePower put called')
        try:
            logging.debug('added config for %s/Controls/%s' % (ch_id, control_id))
            if ch_id not in members:
                controls = {control_id: config}
                members[ch_id] = controls
            else:
                members[ch_id][control_id] = config
            resp = config, 200
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

# ControlsDeepAPI
#
# This services Deep PATCH requests for computer system power controls.
#
class ControlsDeepAPI(Resource):

    def __init__(self, **kwargs):
        logging.info('ControlsDeepAPI init called')
        self.allow = 'PATCH'

    # HTTP GET
    def get(self, ch_id):
        logging.info('ControlsDeepAPI GET called')
        try:
            resp = error_404_response(request.path)
            if ch_id in members:
                resp = error_not_allowed_response(request.path, request.method, {'Allow': self.allow})
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

    # HTTP PUT
    def put(self, ch_id):
        logging.info('ControlsDeepAPI PUT called')
        try:
            resp = error_404_response(request.path)
            if ch_id in members:
                resp = error_not_allowed_response(request.path, request.method, {'Allow': self.allow})
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

    # HTTP POST
    def post(self, ch_id):
        logging.info('ControlsDeepAPI POST called')
        try:
            resp = error_404_response(request.path)
            if ch_id in members:
                resp = error_not_allowed_response(request.path, request.method, {'Allow': self.allow})
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

    # HTTP PATCH
    #
    # Apply power limit to the specified Controls
    def patch(self, ch_id):
        logging.info('ControlsDeepAPI PATCH called')
        raw_dict = request.get_json(force=True)
        try:
            resp = error_404_response(request.path)
            if ch_id in members:
                for member in raw_dict['Members']:
                    id = member['@odata.id'].replace('/redfish/v1/Chassis/%s/Controls/' % ch_id, '')
                    if id in members[ch_id]:
                        resp = applyControlPatch(member, ch_id, id)
                        if resp[1] != 200:
                            break
                    else:
                        resp = simple_error_response('Invalid control for PATCH, %s' % member['@odata.id'], 400)
                        break
                if resp[1] == 200:
                    resp = success_response('PATCH was successful', 200)
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp

    # HTTP DELETE
    def delete(self, ch_id):
        logging.info('ControlsDeepAPI DELETE called')
        try:
            resp = error_404_response(request.path)
            if ch_id in members:
                resp = error_not_allowed_response(request.path, request.method, {'Allow': self.allow})
        except Exception:
            traceback.print_exc()
            resp = simple_error_response('Server encountered an unexpected Error', 500)
        return resp
