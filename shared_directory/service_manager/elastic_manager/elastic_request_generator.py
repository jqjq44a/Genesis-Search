# Local Imports
import base64
import json

from Genesis.controllers.constants.constant import CONSTANTS
from Genesis.controllers.view_managers.user_views.search_manager.search_enums import SEARCH_MODEL_TOKENIZATION_COMMANDS
from Genesis.controllers.view_managers.user_views.search_manager.tokenizer import tokenizer
from shared_directory.request_manager.request_handler import request_handler
from shared_directory.service_manager.elastic_manager.elastic_enums import ELASTIC_KEYS, ELASTIC_REQUEST_COMMANDS, \
    ELASTIC_INDEX


class elastic_request_generator(request_handler):

    __m_tokenizer = None

    def __init__(self):
        self.__m_tokenizer = tokenizer()

    def __on_search(self, p_query_model, p_suggested_query):
        m_user_query, m_search_type, m_safe_search, m_page_number = p_query_model.m_search_query, p_query_model.m_search_type, p_query_model.m_safe_search, p_query_model.m_page_number

        m_tokenized_query = self.__m_tokenizer.invoke_trigger(SEARCH_MODEL_TOKENIZATION_COMMANDS.M_NORMALIZE, [m_user_query])
        m_type = m_search_type

        if m_type == "finance":
            m_type = "business"

        m_doc_length_filter = {"range": {"m_doc_size": { "gte": 0 }}}
        if m_type == "doc":
            m_type = "all"
            m_doc_length_filter = {"range": {"m_doc_size": { "gt": 0 }}}

        m_image_length_filter = {"range": {"m_img_size": { "gte": 0 }}}
        if m_type == "images":
            m_type = "all"
            m_doc_length_filter = {"range": {"m_img_size": { "gt": 0 }}}

        m_safe_filter = { "match_none": {}}
        if m_type != "all":
            m_type_filter = {"term": {"m_content_type": m_type[0]}}
        else:
            if m_safe_search == "False":
                m_type_filter = { "match_all": {}}
            else:
                m_type_filter = { "match_all": {}}
                m_safe_filter = {"term": {"m_content_type": 'a'}}

        m_query_statement = {
            "from": (m_page_number-1) * CONSTANTS.S_SETTINGS_SEARCHED_DOCUMENT_SIZE,
            "size": CONSTANTS.S_SETTINGS_FETCHED_DOCUMENT_SIZE+5,
            "query": {
                  "bool": {
                  "must_not": [m_safe_filter],
                  "must": [m_type_filter],
                  "should": [
                    m_doc_length_filter,m_image_length_filter,
                    {
                      "match": {
                        "m_title": {
                            "query": m_user_query,
                            "boost": 4
                        }
                      }
                    },
                    {
                      "match": {
                        "m_meta_description": {
                            "query": m_user_query,
                            "boost": 2
                        }
                      }
                    },
                    {
                      "match": {
                        "m_important_content": {
                            "query": m_user_query,
                            "boost": 1
                        }
                      }
                    },
                    {
                      "match": {
                        "m_content": {
                            "query": m_tokenized_query,
                            "boost": 0
                        }
                      }
                    }
                  ]
                }
            },
              "suggest" : {
                "suggestions" : {
                  "text" : p_suggested_query,
                  "term" : {
                    "field" : "m_content"
                  }
               }
            }
         }

        return {ELASTIC_KEYS.S_DOCUMENT: ELASTIC_INDEX.S_WEB_INDEX, ELASTIC_KEYS.S_FILTER:m_query_statement}

    def __onion_list(self, p_page_number):
        m_query = {
            "from": (p_page_number-1) * 5000,
            "size": 5001,
            "query": {
                "match": {
                    "m_sub_host": 'na'
                }
            },"_source": ["m_host", "m_content_type"]
        }

        return {ELASTIC_KEYS.S_DOCUMENT: ELASTIC_INDEX.S_WEB_INDEX, ELASTIC_KEYS.S_FILTER:m_query}

    def __on_index_user_query(self, p_data):
        m_host, m_sub_host = helper_method.split_host_url(p_data.m_base_url_model.m_url)
        m_data = {
            "script": {
                "source": "ctx._source.m_doc_size = params.m_doc_size;"
                          "ctx._source.m_img_size = params.m_img_size;"
                          "ctx._source.m_host = params.m_host;"
                          "ctx._source.m_sub_host = params.m_sub_host;"
                          "ctx._source.m_title = params.m_title;"
                          "ctx._source.m_meta_description = params.m_meta_description;"
                          "ctx._source.m_title_hidden = params.m_title_hidden;"
                          "ctx._source.m_important_content = params.m_important_content;"
                          "ctx._source.m_important_content_hidden = params.m_important_content_hidden;"
                          "ctx._source.m_total_hits  += params.m_total_hits;"
                          "ctx._source.m_half_month_hits  += params.m_half_month_hits;"
                          "ctx._source.m_monthly_hits  += params.m_monthly_hits;"
                          "ctx._source.m_user_generated  = params.m_user_generated;"
                          "ctx._source.m_date  = params.m_date;"
                          "ctx._source.m_meta_keywords  = params.m_meta_keywords;"
                          "ctx._source.m_content  = params.m_content;"
                          "ctx._source.m_content_type  = params.m_content_type;"
                          "ctx._source.m_crawled_doc_url  = params.m_crawled_doc_url;"
                          "ctx._source.m_crawled_video  = params.m_crawled_video;"
                          "ctx._source.m_crawled_user_images  = params.m_crawled_user_images;"
                ,"lang": "painless",
                "params": {
                    "m_doc_size": len(p_data.m_document),
                    "m_img_size": len(p_data.m_images),
                    "m_host": m_host,
                    "m_sub_host": m_sub_host,
                    "m_title": p_data.m_title,
                    "m_meta_description": p_data.m_meta_description,
                    "m_title_hidden": p_data.m_title_hidden,
                    "m_important_content": p_data.m_important_content,
                    "m_important_content_hidden": p_data.m_important_content_hidden,
                    "m_total_hits": 1,
                    "m_half_month_hits": 1,
                    "m_monthly_hits": 1,
                    "m_user_generated": True,
                    "m_date": helper_method.get_time(),
                    "m_meta_keywords": p_data.m_meta_keywords,
                    "m_content": p_data.m_content,
                    "m_content_type": p_data.m_content_type,
                    "m_crawled_doc_url": p_data.m_document,
                    "m_crawled_video": p_data.m_video,
                    "m_crawled_user_images": json.loads(UrlObjectEncoder().encode(p_data.m_images))
                }
            },
            "upsert": {
                "m_doc_size": len(p_data.m_document),
                "m_img_size": len(p_data.m_images),
                "m_host": m_host,
                "m_sub_host": m_sub_host,
                "m_title": p_data.m_title,
                "m_meta_description": p_data.m_meta_description,
                "m_title_hidden": p_data.m_title_hidden,
                "m_important_content": p_data.m_important_content,
                "m_important_content_hidden": p_data.m_important_content_hidden,
                "m_total_hits": 0,
                "m_half_month_hits": 0,
                "m_monthly_hits": 0,
                "m_user_generated": p_data.m_user_crawled,
                "m_date": helper_method.get_time(),
                "m_meta_keywords": p_data.m_meta_keywords,
                "m_content": p_data.m_content,
                "m_content_type": p_data.m_content_type,
                "m_crawled_doc_url": p_data.m_document,
                "m_crawled_video": p_data.m_video,
                "m_crawled_user_images": json.loads(UrlObjectEncoder().encode(p_data.m_images)),
                "m_doc_url": [],
                "m_video": [],
                "m_images": []
            }
        }

        return {ELASTIC_KEYS.S_DOCUMENT: ELASTIC_INDEX.S_WEB_INDEX, ELASTIC_KEYS.S_ID : base64.b64encode((m_host+m_sub_host).encode('ascii')), ELASTIC_KEYS.S_VALUE:m_data, ELASTIC_KEYS.S_FILTER:(m_host + m_sub_host)}

    def invoke_trigger(self, p_commands, p_data=None):
        if p_commands == ELASTIC_REQUEST_COMMANDS.S_SEARCH:
            return self.__on_search(p_data[0], p_data[1])
        if p_commands == ELASTIC_REQUEST_COMMANDS.S_ONION_LIST:
            return self.__onion_list(p_data[0])
        if p_commands == ELASTIC_REQUEST_COMMANDS.S_INDEX_USER_QUERY:
            return self.__on_index_user_query(p_data[0])
