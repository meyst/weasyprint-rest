#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import io
import json
import logging

from werkzeug.datastructures import FileStorage
from flask import request, abort, make_response
from flask_restful import Resource

from jinja2 import Environment, FileSystemLoader

from ..util import authenticate
from ...print.weasyprinter import WeasyPrinter
from ...print.template_loader import TemplateLoader
from ...print.template import Template


def _get_request_list_or_value(request_dict, name):
    return request_dict.getlist(name) if name.endswith("[]") else request_dict[name]


def _get_request_argument(name, default=None):
    logging.warn("def _get_request_argument")
    form = request.form
    args = request.args
    files = request.files

    if name in form:
        return _get_request_list_or_value(form, name)
    elif name in args:
        return _get_request_list_or_value(args, name)
    elif name in files:
        return _get_request_list_or_value(files, name)
    return default


def _parse_request_argument(name, default=None, parse_type=None, parse_args=None):
    logging.warn("def _parse_request_argument: name=" + name)
    content = _get_request_argument(name, default)

    if parse_type == "file" and isinstance(content, str):
        logging.warn("Parse type is file.")
        content_type = _may_get_dict_value(parse_args, "content_type")
        file_name = _may_get_dict_value(parse_args, "file_name")
        logging.warn("Filename is " + file_name)
        return FileStorage(
            stream=io.BytesIO(bytes(content, encoding='utf8')),
            filename=file_name,
            content_type=content_type
        )

    if content == default and name.endswith("[]"):
        content = _parse_request_argument(name[:-2], default, parse_type, parse_args)
        if not isinstance(content, list):
            return [content]

    return content


def _may_get_dict_value(dict_values, key, default=None):
    logging.info("def _may_get_dict_value")
    if dict_values is None:
        return default
    if key not in dict_values:
        return default
    return dict_values[key]


def _build_template():
    styles = _parse_request_argument("style[]", [], "file", {
        "content_type": "text/css",
        "file_name": "style.css"
    })
    assets = _parse_request_argument("asset[]", [])
    template_name = _parse_request_argument("template", None)
    base_template = TemplateLoader().get(template_name)

    return Template(styles=styles, assets=assets, base_template=base_template)


class PrintAPI(Resource):
    decorators = [authenticate]

    def __init__(self):
        super(PrintAPI, self).__init__()

    def post(self):
        mode = "pdf"
        disposition = _parse_request_argument("disposition", "inline")
        html = _parse_request_argument("html", None, "file", {
            "content_type": "text/html",
            "file_name": "document.html"
        })

        payload = _parse_request_argument("payload", None, "file", {
            "content_type": "text/json",
            "file_name": "payload.json"
        })

        if html is None:
            return abort(422, description="Required argument 'html' is missing.")

        if payload is not None:
            env = Environment()
            html_template = env.from_string(html.read().decode("utf-8"))
            j= json.load(payload)
            content = html_template.render(j)
            html = FileStorage(
                stream=io.BytesIO(bytes(content, encoding='utf8')),
                filename='document.html', 
                content_type='text/html', 
                content_length=len(content)
            )
        
        template = _build_template()

        printer = WeasyPrinter(html, template=template)
        content = printer.write(mode)

        # build response
        response = make_response(content)
        basename, _ = os.path.splitext(html.filename)
        extension = None
        response.headers['Content-Type'] = 'application/pdf'
        extension = "pdf"


        response.headers['Content-Disposition'] = '%s; name="%s"; filename="%s.%s"' % (
            disposition,
            basename,
            basename,
            extension
        )

        html.close()

        return response
