# -*- coding: utf-8 -*-
import six
import json
import datetime
from time import strftime

from python_ifirma.exceptions import PythonIfirmaExceptionFactory
from python_ifirma.helpers import Helpers
import requests


class VAT:
    VAT_0 = 0.00
    VAT_5 = 0.05
    VAT_8 = 0.08
    VAT_23 = 0.23


class Address:
    def __init__(self, city, zip_code, street=None, country=None):
        super().__init__()
        self.city = city
        self.zip_code = zip_code
        self.street = street
        self.country = country


class Client:
    def __init__(self, name, tax_id, address, email=None, phone_number=None):
        self.name = name
        self.tax_id = tax_id
        self.address = address
        self.email = email
        self.phone_number = phone_number

    def get_dict(self):
        return {
            "Nazwa": self.name,
            "NIP": self.tax_id,
            "KodPocztowy": self.address.zip_code,
            "Ulica": self.address.street,
            "Miejscowosc": self.address.city,
            "Kraj": self.address.country,
            "Email": self.email,
            "Telefon": self.phone_number,
        }


class Position:
    def __init__(self, vat_rate, quantity, base_price, full_name, unit, pkwiu=None, discount_percent=None):
        self.vat_rate = vat_rate
        self.quantity = quantity
        self.base_price = base_price
        self.full_name = full_name
        self.unit = unit
        self.pkwiu = pkwiu
        self.discount_percent = discount_percent

    def get_dict(self):
        return {
            "StawkaVat": self.vat_rate,
            "Ilosc": self.quantity,
            "CenaJednostkowa": self.base_price,
            "NazwaPelna": self.full_name,
            "Jednostka": self.unit,
            "TypStawkiVat": "PRC",
            "Rabat": self.discount_percent
        }


class NewInvoiceParams:
    def __init__(self, client, positions):
        self.client = client
        self.positions = positions
        self.issue_date = datetime.date.today()

    def __get_issue_date(self):
        return strftime("%Y-%m-%d", self.issue_date.timetuple())

    def __get_total_price(self):
        return sum(
            [
                position.quantity * position.base_price * (
                    (1 - position.discount_percent / 100) if position.discount_percent else 1
                ) for position in self.positions
            ]
        )

    def get_request_data(self):
        return {
            "Zaplacono": self.__get_total_price(),
            "ZaplaconoNaDokumencie": self.__get_total_price(),
            "LiczOd": "BRT",
            "DataWystawienia": self.__get_issue_date(),
            "DataSprzedazy": self.__get_issue_date(),
            "FormatDatySprzedazy": "MSC",
            "SposobZaplaty": "ELE",
            "RodzajPodpisuOdbiorcy": "BPO",
            "WidocznyNumerGios": False,
            "Numer": None,
            "Pozycje": [position.get_dict() for position in self.positions],
            "Kontrahent": self.client.get_dict(),
        }


class iFirmaAPI():
    __username = None
    __invoice_key_name = "faktura"
    __invoice_key_value = None

    __user_key_name = "abonent"
    __user_key_value = None

    def __init__(self, _username, _invoice_key_value, _user_key_value=None):
        self.__username = _username
        self.__invoice_key_value = Helpers.unhex_key_value(_invoice_key_value)
        self.__user_key_value = Helpers.unhex_key_value(_user_key_value)

    @staticmethod
    def __execute_post_request(headers, request_content, url):
        response = requests.post(url, data=request_content, headers=headers)
        response_dict = json.loads(response.content.decode("utf-8"), 'utf-8')
        if "response" not in response_dict:
            raise PythonIfirmaExceptionFactory.throw_exception_by_code(-1)
        real_response_content = response_dict["response"]
        response_code = real_response_content.get("Kod", -1)

        if response_code != 0:
            raise PythonIfirmaExceptionFactory.throw_exception_by_code(response_code)

        return response_dict

    def __create_authentication_header_value(self, request_hash_text):
        return "IAPIS user={}, hmac-sha1={}".format(
            self.__username,
            Helpers.get_hmac_of_text(self.__invoice_key_value, request_hash_text)
        )

    def __create_invoice_and_return_id(self, invoice, url):
        request_content = json.dumps(invoice.get_request_data(), separators=(',', ':'))
        request_hash_text = "{}{}{}{}".format(
            url,
            self.__username,
            self.__invoice_key_name,
            request_content,
        )
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json; charset=UTF-8",
            "Authentication": self.__create_authentication_header_value(request_hash_text)
        }

        response_dict = self.__execute_post_request(headers, request_content, url)

        if response_dict["response"].get("Identyfikator"):
            invoice_id = response_dict["response"]["Identyfikator"]
            return invoice_id
        else:
            return None

    def generate_invoice(self, invoice):
        url = "https://www.ifirma.pl/iapi/fakturakraj.json"
        return self.__create_invoice_and_return_id(invoice, url)

    def get_invoice_pdf(self, invoice_id):
        url = "https://www.ifirma.pl/iapi/fakturakraj/{}.pdf".format(invoice_id)
        return self.__download_pdf(url)

    def __download_pdf(self, url):
        request_hash_text = "{}{}{}".format(
            url,
            self.__username,
            self.__invoice_key_value,
        )
        headers = {
            "Accept": "application/pdf",
            "Content-type": "application/pdf; charset=UTF-8",
            "Authentication": self.__create_authentication_header_value(request_hash_text)
        }
        resp = requests.get(url, headers=headers)

        content = resp.content

        file_obj = six.BytesIO()
        file_obj.write(content)
        file_obj.seek(0)
        return file_obj