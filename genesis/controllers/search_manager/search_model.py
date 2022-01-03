from genesis.constants.constant import CONSTANTS
from genesis.constants.strings import GENERAL_STRINGS, SEARCH_STRINGS
from genesis.controllers.data_manager.elastic_manager.elastic_enums import ELASTIC_REQUEST_COMMANDS, ELASTIC_CRUD_COMMANDS
from genesis.controllers.data_manager.elastic_manager.elastic_controller import elastic_controller
from genesis.controllers.search_manager.search_enums import SEARCH_MODEL_COMMANDS, SEARCH_CALLBACK, \
    SEARCH_SESSION_COMMANDS, SEARCH_MODEL_TOKENIZATION_COMMANDS
from genesis.controllers.search_manager.search_session_controller import search_session_controller
from genesis.controllers.search_manager.spell_checker import spell_checker
from genesis.controllers.search_manager.tokenizer import tokenizer
from genesis.controllers.shared_model.request_handler import request_handler


class search_model(request_handler):

    # Private Variables
    __instance = None
    __m_session = None
    __m_spell_checker = None
    __m_tokenizer = None

    # Initializations
    def __init__(self):
        self.__m_session = search_session_controller()
        self.__m_tokenizer = tokenizer()
        self.__m_spell_checker = spell_checker()

    def __fetch_filtered_documents(self, p_paged_documents):
        mRelevanceListData = []
        try:
            m_result_final = p_paged_documents['hits']['hits']

            for m_document in m_result_final:
                m_service = m_document['_source']['script']
                if m_service['m_sub_host'] == "na":
                    m_service['m_sub_host'] = "/"
                mRelevanceListData.append(m_document['_source']['script'])
            return mRelevanceListData
        except Exception as ex:
            return mRelevanceListData

    def __query_results(self, p_data):
        m_query_model = self.__m_session.invoke_trigger(SEARCH_SESSION_COMMANDS.INIT_SEARCH_PARAMETER, [p_data])
        if m_query_model.m_search_query == GENERAL_STRINGS.S_GENERAL_EMPTY:
            return False, None
        # m_query_model = p_data

        m_tokenized_query = self.__m_tokenizer.invoke_trigger(SEARCH_MODEL_TOKENIZATION_COMMANDS.M_SPLIT_AND_TOKENIZE, [m_query_model.m_search_query])
        m_user_query = m_query_model.m_search_query
        m_search_type =  m_query_model.m_search_type
        m_safe_search =  m_query_model.m_safe_search

        m_documents = elastic_controller.get_instance().invoke_trigger(ELASTIC_CRUD_COMMANDS.S_READ, [ELASTIC_REQUEST_COMMANDS.S_SEARCH,[m_user_query, m_search_type, m_safe_search, m_query_model.m_page_number],[None]])
        m_parsed_documents = self.__fetch_filtered_documents(m_documents)
        m_query_model.set_total_documents(len(m_parsed_documents))

        m_context, m_status = self.__m_session.invoke_trigger(SEARCH_SESSION_COMMANDS.M_INIT, [m_parsed_documents, m_query_model, m_tokenized_query])
        m_context[SEARCH_CALLBACK.M_QUERY_ERROR] = self.__m_spell_checker.spell_check_query(m_user_query)
        return m_status, m_context

    def __init_page(self, p_data):
        mStatus, mResult = self.__query_results(p_data)
        return mStatus, mResult

    # External Request Callbacks
    def invoke_trigger(self, p_command, p_data):
        if p_command == SEARCH_MODEL_COMMANDS.M_INIT:
            return self.__init_page(p_data)
