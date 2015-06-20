from unittest.case import TestCase

from python_ifirma.core import Client, iFirmaAPI, NewInvoiceParams, Position, VAT, Address
from python_ifirma import exceptions
from python_ifirma.helpers import Helpers


TEST_IFIRMA_USER = "$DEMO254343"
TEST_IFIRMA_INVOICE_KEY = "C501C88284462384"
TEST_IFIRMA_USER_KEY = "B83E825D4D28BD11"


class TestHelpers(TestCase):
    def test_unhex_good_value(self):
        self.assertEqual(b'\x11\x11\x11', Helpers.unhex_key_value("111111"))

    def test_unhex_non_hex_value(self):
        with self.assertRaises(TypeError):
            Helpers.unhex_key_value("qwerty")

    def test_hmac(self):
        # example from iFirma API documentation
        self.assertEqual("cec153ee6350475f117a307111e2bd7d83034925", Helpers.get_hmac_of_text(
            Helpers.unhex_key_value("111111"), '222222'))


class TestAddress(TestCase):
    def test_create_address(self):
        a = Address("City", "00-000")
        self.assertEqual("City", a.city)
        self.assertEqual("00-000", a.zip_code)
        self.assertIsNone(a.street)
        self.assertIsNone(a.country)

    def test_create_address_with_street(self):
        a = Address("City", "00-000", street="street")
        self.assertEqual("City", a.city)
        self.assertEqual("00-000", a.zip_code)
        self.assertEqual("street", a.street)
        self.assertIsNone(a.country)

    def test_create_address_with_country(self):
        a = Address("City", "00-000", country="country")
        self.assertEqual("City", a.city)
        self.assertEqual("00-000", a.zip_code)
        self.assertIsNone(a.street)
        self.assertEqual("country", a.country)

    def test_create_address_with_street_and_country(self):
        a = Address("City", "00-000", street="street", country="country")
        self.assertEqual("City", a.city)
        self.assertEqual("00-000", a.zip_code)
        self.assertEqual("street", a.street)
        self.assertEqual("country", a.country)


class TestClient(TestCase):
    def setUp(self):
        self.address = Address("City", "00-000", street="street", country="country")

    def test_create_client(self):
        c = Client("Name", "1231231212", self.address)
        self.assertEqual("Name", c.name)
        self.assertEqual("1231231212", c.tax_id)
        self.assertEqual(self.address, c.address)
        self.assertIsNone(c.email)
        self.assertIsNone(c.phone_number)

    def test_create_client_with_email(self):
        c = Client("Name", "1231231212", self.address, email="email@server.com")
        self.assertEqual("Name", c.name)
        self.assertEqual("1231231212", c.tax_id)
        self.assertEqual(self.address, c.address)
        self.assertEqual("email@server.com", c.email)
        self.assertIsNone(c.phone_number)

    def test_create_client_with_phone_number(self):
        c = Client("Name", "1231231212", self.address, phone_number="111-222-333")
        self.assertEqual("Name", c.name)
        self.assertEqual("1231231212", c.tax_id)
        self.assertEqual(self.address, c.address)
        self.assertIsNone(c.email)
        self.assertEqual("111-222-333", c.phone_number)

    def test_create_client_with_email_and_phone_number(self):
        c = Client("Name", "1231231212", self.address, email="email@server.com", phone_number="111-222-333")
        self.assertEqual("Name", c.name)
        self.assertEqual("1231231212", c.tax_id)
        self.assertEqual(self.address, c.address)
        self.assertEqual("email@server.com", c.email)
        self.assertEqual("111-222-333", c.phone_number)


class TestCreateInvoice(TestCase):
    def setUp(self):
        self.ifirma_client = iFirmaAPI(TEST_IFIRMA_USER, TEST_IFIRMA_INVOICE_KEY, TEST_IFIRMA_USER_KEY)

        self.client = Client(
            "Dariusz",
            "1231231212",
            Address("Warszawa", "03-185"),
            email="email@server.com",
        )

        self.position = Position(VAT.VAT_23, 1, 1000, "nazwa", "szt")

    def test_generate_invoice(self):
        invoice = NewInvoiceParams(self.client, [self.position])
        self.assertIsNotNone(self.ifirma_client.generate_invoice(invoice))

    def test_generate_invoice_with_position_with_bad_vat(self):
        bad_position = Position(0.22, 1, 1000, "nazwa", "szt")

        with self.assertRaises(exceptions.BadRequestParameters):
            invoice = NewInvoiceParams(self.client, [bad_position])
            self.ifirma_client.generate_invoice(invoice)

    def test_download_invoice(self):
        invoice = NewInvoiceParams(self.client, [self.position])
        invoice_id, invoice_number = self.ifirma_client.generate_invoice(invoice)

        self.assertIsNotNone(invoice_id)
        self.assertIsNotNone(invoice_number)
        self.assertIsNotNone(self.ifirma_client.get_invoice_pdf(invoice_id))