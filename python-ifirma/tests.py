from unittest.case import TestCase

from ifirma import Client


class TestClient(TestCase):
    def setUp(self):
        pass

    def __create_basic_client(self):
        self.client = Client(
            "name",
            "street",
            "00-001",
            "Polska",
            "Warszawa"
        )

    def testClient(self):
        self.__create_basic_client()
        get_dict = self.client.get_dict()
        self.assertIn("Nazwa", get_dict)
        self.assertIn("Identyfikator", get_dict)
        self.assertIn("PrefiksUE", get_dict)
        self.assertIn("Ulica", get_dict)
        self.assertIn("KodPocztowy", get_dict)
        self.assertIn("Kraj", get_dict)
        self.assertIn("Miejscowosc", get_dict)
        self.assertIn("Email", get_dict)
        self.assertIn("Telefon", get_dict)
        self.assertIn("OsobaFizyczna", get_dict)

    def testEmail(self):
        self.__create_basic_client()
        self.assertIsNone(self.client.get_dict()["Email"])