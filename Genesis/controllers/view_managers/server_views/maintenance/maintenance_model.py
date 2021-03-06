from Genesis.controllers.view_managers.server_views.maintenance.maintenance_enums import MAINTENANCE_MODEL_CALLBACK, \
    MAINTENANCE_SESSION_COMMANDS
from Genesis.controllers.view_managers.server_views.maintenance.maintenance_session_controller import \
    maintenance_session_controller
from Genesis.controllers.view_managers.user_views.hompage_manager.homepage_enums import HOMEPAGE_SESSION_COMMANDS, \
    HOMEPAGE_MODEL_COMMANDS
from Genesis.controllers.view_managers.user_views.hompage_manager.homepage_session_controller import \
    homepage_session_controller
from shared_directory.request_manager.request_handler import request_handler


class maintenance_model(request_handler):

    # Private Variables
    __instance = None
    __m_session = None

    # Initializations
    def __init__(self):
        self.__m_session = maintenance_session_controller()
        pass

    def __init_page(self, p_data):
        m_context, m_status = self.__m_session.invoke_trigger(MAINTENANCE_SESSION_COMMANDS.M_INIT, p_data)

        return m_context, m_status

    # External Request Handler
    def invoke_trigger(self, p_command, p_data):
        if p_command == MAINTENANCE_MODEL_CALLBACK.M_INIT:
            return self.__init_page(p_data)
