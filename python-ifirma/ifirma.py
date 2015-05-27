# -*- coding: utf-8 -*-
import binascii
from enum import Enum
import hashlib
import hmac
import json
import datetime

import requests
import six


class VAT(Enum):
    VAT_0 = 0.00
    VAT_5 = 0.05
    VAT_8 = 0.08
    VAT_23 = 0.23
    PERCENTAGE = "PRC"
    EXEMPT = "ZW"


class Client:
    __name = None
    __id = None
    __eu_prefix = None
    __street = None
    __zip_code = None
    __country = None
    __city = None
    __email = None
    __phone_number = None
    __is_private = True

    def __init__(self, name, street, zip_code, country, city, _id=None, eu_prefix=None, email=None, phone_number=None,
                 is_private=True):
        self.__name = name
        self.__street = street
        self.__zip_code = zip_code
        self.__country = country
        self.__city = city
        self.__id = _id
        self.__eu_prefix = eu_prefix
        self.__email = email
        self.__phone_number = phone_number
        self.__is_private = is_private

    def get_dict(self):
        return {
            "Nazwa": self.__name,
            "Identyfikator": self.__id,
            "PrefiksUE": self.__eu_prefix,
            "Ulica": self.__street,
            "KodPocztowy": self.__zip_code,
            "Kraj": self.__country,
            "Miejscowosc": self.__city,
            "Email": self.__email,
            "Telefon": self.__phone_number,
            "OsobaFizyczna": self.__is_private,
        }

    def get_json(self):
        return json.dumps(self.get_dict())


class Position:
    __vat = None
    __quantity = None
    __base_price = None
    __full_name = None
    __unit = None
    __pkwiu = None
    __vat_type = None
    __discount = None

    def __init__(self, vat, quantity, base_price, full_name, unit, pkwiu="", vat_type=VAT.PERCENTAGE, discount=0):
        self.__vat = vat
        self.__quantity = quantity
        self.__base_price = base_price
        self.__full_name = full_name
        self.__unit = unit
        self.__pkwiu = pkwiu
        self.__vat_type = vat_type
        self.__discount = discount

    def get_dict(self):
        return {
            "StawkaVat": self.__vat.value,
            "Ilosc": self.__quantity,
            "CenaJednostkowa": self.__base_price,
            "NazwaPelna": self.__full_name,
            "Jednostka": self.__unit,
            "PKWiU": self.__pkwiu,
            "TypStawkiVat": self.__vat_type.value,
            "Rabat": self.__discount
        }


class Invoice:
    __client = None
    __positions = []

    def set_client(self, client):
        self.__client = client

    def add_position(self, position):
        self.__positions.append(position)

    def clear_positions(self):
        self.__positions.clear()

    def get_dict(self):
        return {
            "LiczOd": "BRT",
            "NumerKontaBankowego": None,
            "TypFakturyKrajowej": "SPRZ",
            "DataWystawienia": today,
            "MiejsceWystawienia": "Warszawa",
            "TerminPlatnosci": None,
            "SposobZaplaty": "PRZ",
            "NazwaSeriiNumeracji": "default",
            "NazwaSzablonu": "logo",
            "RodzajPodpisuOdbiorcy": "BPO",
            "PodpisOdbiorcy": "",
            "PodpisWystawcy": "",
            "Uwagi": "",
            "WidocznyNumerGios": True,
            "Numer": None,
            "Pozycje": [Position(VAT.VAT_23, 1, 1000, "Nazwa pozycji", "szt", discount=10).get_dict()],
            "Kontrahent": Client("Imię Nazwisko", "Ulica", "01-234", "Polska", "Warszawa").get_dict()
        }


class iFirmaAPI():
    username = None
    invoice_key_name = "faktura"
    invoice_key_value = None

    user_key_name = "abonent"
    user_key_value = None

    @classmethod
    def __sanitize_key_value(cls, text):
        try:
            return binascii.unhexlify(text)
        except TypeError:
            return text

    @classmethod
    def __get_hmac_of_text(cls, key, text):
        return hmac.new(key, six.b(text), hashlib.sha1).hexdigest()

    def __init__(self, _username, _invoice_key_value, _user_key_value=None):
        self.username = _username
        self.invoice_key_value = self.__sanitize_key_value(_invoice_key_value)
        self.user_key_value = self.__sanitize_key_value(_user_key_value)

    def __create_invoice_and_return_id(self, data, url):
        request_content = json.dumps(data, separators=(',', ':'))
        request_hash_text = "{}{}{}{}".format(
            url,
            self.username,
            self.invoice_key_name,
            request_content,
        )
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json; charset=UTF-8",
            "Authentication": "IAPIS user={}, hmac-sha1={}".format(
                self.username,
                self.__get_hmac_of_text(self.invoice_key_value, request_hash_text)
            )
        }
        response = requests.post(url, data=request_content, headers=headers)
        response_dict = json.loads(response.content.decode("utf-8"), 'utf-8')
        if response_dict["response"].get("Identyfikator"):
            invoice_id = response_dict["response"]["Identyfikator"]
            return invoice_id
        else:
            code = response_dict["response"]["Kod"]
            info = response_dict["response"]["Informacja"]
            if code == 201 and info.find(u"musi być zgodna z miesiącem i rokiem księgowym") > 0:
                self.change_billing_month_to_next()
                return self.__create_invoice_and_return_id(data, url)
            return None

    def generate_invoice(self, data):
        url = "https://www.ifirma.pl/iapi/fakturakraj.json"
        return self.__create_invoice_and_return_id(data, url)

    def generate_proforma_invoice(self, data):
        url = "https://www.ifirma.pl/iapi/fakturaproformakraj.json"

        return self.__create_invoice_and_return_id(data, url)

    def __download_pdf(self, file_path, url):
        request_hash_text = "{}{}{}".format(
            url,
            self.username,
            self.invoice_key_name,
        )
        headers = {
            "Accept": "application/pdf",
            "Content-type": "application/pdf; charset=UTF-8",
            "Authentication": "IAPIS user={}, hmac-sha1={}".format(
                self.username,
                self.__get_hmac_of_text(self.invoice_key_value, request_hash_text)
            )
        }
        resp = requests.get(url, headers=headers)
        content = resp.content
        print(content)
        file = open(file_path, "wb")
        file.write(content)
        file.close()

    def download_invoice_pdf(self, invoice_id, file_path):
        url = "https://www.ifirma.pl/iapi/fakturakraj/{}.pdf".format(invoice_id)
        self.__download_pdf(file_path, url)

    def download_proforma_invoice_pdf(self, invoice_id, file_path):
        url = "https://www.ifirma.pl/iapi/fakturaproformakraj/{}.pdf".format(invoice_id)
        self.__download_pdf(file_path, url)

    def create_invoice_from_proforma(self, proforma_id):
        url = "https://www.ifirma.pl/iapi/fakturaproformakraj/add/{}.json".format(proforma_id)
        request_hash_text = "{}{}{}".format(
            url,
            self.username,
            self.invoice_key_name,
        )
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json; charset=UTF-8",
            "Authentication": "IAPIS user={}, hmac-sha1={}".format(
                self.username,
                self.__get_hmac_of_text(self.invoice_key_value, request_hash_text)
            )
        }
        resp = requests.get(url, headers=headers)
        response_dict = json.loads(resp.content.decode("utf-8"))
        invoice_id = response_dict["response"]["Identyfikator"]
        return invoice_id

    def change_billing_month_to_next(self):
        data = {
            "MiesiacKsiegowy": "NAST",
            "PrzeniesDaneZPoprzedniegoRoku": False,
        }
        url = "https://www.ifirma.pl/iapi/abonent/miesiacksiegowy.json"
        request_content = json.dumps(data, separators=(',', ':'))

        request_hash_text = "{}{}{}{}".format(
            url,
            self.username,
            self.user_key_name,
            request_content
        )

        headers = {
            "Accept": "application/json",
            "Content-type": "application/json; charset=UTF-8",
            "Authentication": "IAPIS user={}, hmac-sha1={}".format(
                self.username,
                self.__get_hmac_of_text(self.user_key_value, request_hash_text),
            )
        }
        resp = requests.put(url, data=request_content, headers=headers)

    def get_invoice_details(self, invoice_id):
        url = "https://www.ifirma.pl/iapi/fakturakraj/{}.json".format(invoice_id)
        request_hash_text = "{}{}{}".format(
            url,
            self.username,
            self.invoice_key_name,
        )
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json; charset=UTF-8",
            "Authentication": "IAPIS user={}, hmac-sha1={}".format(
                self.username,
                self.__get_hmac_of_text(self.invoice_key_value, request_hash_text),
            )
        }
        resp = requests.get(url, headers=headers)
        return json.loads(resp.content)

    def get_pro_forma_details(self, proforma_id):
        url = "https://www.ifirma.pl/iapi/fakturaproformakraj/{}.json".format(proforma_id)
        request_hash_text = "{}{}{}".format(
            url,
            self.username,
            self.invoice_key_name,
        )
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json; charset=UTF-8",
            "Authentication": "IAPIS user={}, hmac-sha1={}".format(
                self.username,
                self.__get_hmac_of_text(self.invoice_key_value, request_hash_text),
            )
        }
        resp = requests.get(url, headers=headers)
        return json.loads(resp.content)


def main():
    api = iFirmaAPI("$DEMO239002", "B4E1FC1D017C5556", _user_key_value="114D8F7A22BC87F8")


    def change_billing_month():
        api.change_billing_month_to_next()

    def issue_proforma_and_then_invoice_and_download():
        today = "{}".format(datetime.date.today())
        data = {
            "LiczOd": "BRT",
            "NumerKontaBankowego": None,
            "TypFakturyKrajowej": "SPRZ",
            "DataWystawienia": today,
            "MiejsceWystawienia": "Warszawa",
            "TerminPlatnosci": None,
            "SposobZaplaty": "PRZ",
            "NazwaSeriiNumeracji": "default",
            "NazwaSzablonu": "logo",
            "RodzajPodpisuOdbiorcy": "BPO",
            "PodpisOdbiorcy": "",
            "PodpisWystawcy": "",
            "Uwagi": "",
            "WidocznyNumerGios": True,
            "Numer": None,
            "Pozycje": [Position(VAT.VAT_23, 1, 1000, "Nazwa pozycji", "szt", discount=10).get_dict()],
            "Kontrahent": Client("Imię Nazwisko", "Ulica", "01-234", "Polska", "Warszawa").get_dict()
        }
        proforma_invoice_id = api.generate_proforma_invoice(data)
        api.download_proforma_invoice_pdf(proforma_invoice_id, "inv.pdf")
        invoice_id = api.create_invoice_from_proforma(proforma_invoice_id)
        api.download_invoice_pdf(invoice_id, "inv2.pdf")

    # change_billing_month()
    issue_proforma_and_then_invoice_and_download()

    # api.create_invoice_from_proforma(346723)


if __name__ == "__main__":
    main()