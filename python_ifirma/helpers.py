import binascii
import hashlib
import hmac

import six


class Helpers:
    @staticmethod
    def unhex_key_value(text):
        try:
            return binascii.unhexlify(text)
        except binascii.Error:
            raise TypeError

    @staticmethod
    def get_hmac_of_text(key, text):
        return hmac.new(key, six.b(text), hashlib.sha1).hexdigest()