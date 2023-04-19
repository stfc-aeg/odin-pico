""" Adapter for Odin Control to interface with a picoscope 5444D"""

from concurrent.futures import thread

import time
import logging
import threading
from concurrent import futures

from tornado.concurrent import run_on_executor
from tornado.escape import json_decode

from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError

from odin_pico.pico_controller import PicoController

class PicoAdapter(ApiAdapter):

    def __init__(self, **kwargs):

        super(PicoAdapter, self).__init__(**kwargs)

        background_task_enable = True#bool(self.options.get('background_task_enable'))
        self.picomanager = PicoManager(background_task_enable)

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        try:
            response = self.picomanager.get(path)
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
            self.picomanager.set(path, data)
            response = self.picomanager.get(path)
            status_code = 200
        except PicoManagerError as e:
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

        self.picomanager.cleanup()    

class PicoManagerError(Exception):
    pass

class PicoManager():

    executor = futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, background_task_enable):
        logging.debug("Created PicoAdapter and PicoManager successfuly")

        self.lock = threading.Lock()

        self.pico_instance = PicoController(self.lock)

        self.param_tree = ParameterTree({
            'test': (lambda: "test_string", None),
            'device': self.pico_instance.pico_param_tree
        })  
 
        """ Setting inital values for variables"""

        self.background_task_enable = background_task_enable
        
        if self.background_task_enable:
            self.start_background_task()

        ####    END OF INIT    ####    

    def get(self, path):
        """Get the parameter tree. """ 

        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree. """

        try:
            self.param_tree.set(path, data)
        except ParameterTreeError as e:
            raise PicoManagerError(e)

    def cleanup(self):
        """Clean up the Adapter instance. """

        logging.debug("Cleanup function called!")
        self.stop_background_task()
        self.pico_instance.cleanup()
        
    def start_background_task(self):
        """ Changes the value of the enable variable to True and calls the 
        background task function """
        self.background_task_enable = True
        self.background_task()

    def stop_background_task(self):
        """ Disables the background task by altering its control variable """

        self.background_task_enable = False

    @run_on_executor
    def background_task(self):

        while self.background_task_enable:
            self.pico_instance.update_poll()                    

            #Controls the speed of the background task calls
            time.sleep(1)
                