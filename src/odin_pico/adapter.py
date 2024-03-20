"""Adapter for a PicoScope 5444D."""

import threading
from odin.adapters.adapter import (
    ApiAdapter,
    ApiAdapterResponse,
    request_types,
    response_types,
)
from odin.adapters.parameter_tree import ParameterTreeError
from tornado.escape import json_decode
from odin_pico.pico_controller import PicoController, PicoControllerError

class PicoAdapter(ApiAdapter):
    """Top level Adapter for Odin Control to interface with a PicoScope 5444D."""

    def __init__(self, **kwargs):
        """Initialise the PicoAdapter Object."""
        super(PicoAdapter, self).__init__(**kwargs)

        self.lock = threading.Lock()
        update_loop = True
        data_output_path = self.options.get("data_output_path", "/tmp/")
        max_caps = self.options.get("max_caps", "/tmp/")

        self.pico_controller = PicoController(self.lock, update_loop, data_output_path, int(max_caps))

    @response_types("application/json", default="application/json")
    def get(self, path, request):
        """Handle a HTTP GET request."""
        try:
            # Send the get request to the controller
            response = self.pico_controller.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {"error": str(e)}
            status_code = 400

        content_type = "application/json"

        return ApiAdapterResponse(
            response, content_type=content_type, status_code=status_code
        )

    @request_types("application/json")
    @response_types("application/json", default="application/json")
    def put(self, path, request):
        """Handle a HTTP PUT request."""
        content_type = "application/json"

        try:
            # Send the set request to the controller
            data = json_decode(request.body)
            self.pico_controller.set(path, data)
            response = self.pico_controller.get(path)
            status_code = 200
        except PicoControllerError as e:
            response = {"error": str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {"error": f"Failed to decode PUT request body: {str(e)}"}
            status_code = 400

        return ApiAdapterResponse(
            response, content_type=content_type, status_code=status_code
        )

    def delete(self, path, request):
        """Handle a HTTP DELETE request."""
        response = f"PicoAdapter: DELETE on path {path}"
        status_code = 200

        return ApiAdapterResponse(response, status_code=status_code)

    def cleanup(self):
        """Clean up adapter state at shutdown."""
        self.pico_controller.cleanup()
