""" Top level Adapter for Odin Control to interface with a picoscope 5444D"""

import logging
import threading

from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTreeError

from odin_pico.pico_controller import PicoController 
from odin_pico.pico_controller import PicoControllerError

class PicoAdapter(ApiAdapter):

    def __init__(self, **kwargs):

        super(PicoAdapter, self).__init__(**kwargs)

        self.lock = threading.Lock()
        update_loop = True #bool(self.options.get('update_loop'))
        #path = '/tmp/pico_captures/' #self.options.get
        data_output_path = self.options.get('data_output_path', '/tmp/')
        self.pico_controller = PicoController(self.lock, update_loop, data_output_path)

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        try:
            response = self.pico_controller.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error' : str(e)}
            status_code = 400

        content_type = 'application/json'

        return ApiAdapterResponse(response, content_type=content_type, 
                                    status_code=status_code)

    @request_types('application/json')
    @response_types('application/json', default='application/json')
    def put(self, path, request):

        content_type = 'application/json'

        try:
            data = json_decode(request.body)
            logging.debug(data)
            self.pico_controller.set(path, data)
            response = self.pico_controller.get(path)
            status_code = 200
        except PicoControllerError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type, 
                                    status_code=status_code)

    def delete(self, path, request):
        response = 'PicoAdapter: DELETE on path {}'.format(path)
        status_code =200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def cleanup(self):
        """Clean up adapter state at shutdown."""

        self.pico_controller.cleanup()