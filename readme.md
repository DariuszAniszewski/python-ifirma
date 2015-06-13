python-ifirma (in progress)
======

Extremely simple wrapper for iFirma API.

##Features

**Implemented**

- generating invoice in iFirma service

**Planned**

- downloading invoice PDF
- generating proforma invoice
- generating invoice based on proforma

##Prerequisites

Go to your iFirma account and generate API keys of following types:

- *faktura* (required)
- *abonent* (optional)


**Testing**

iFirma offers [demo account](https://www.ifirma.pl/cgi-bin/WebObjects/ifirma-demo.woa/wa/demo) that can be used for testing and development


##Usage


1. Create instance of iFirmaAPI

```python
ifirma_client = iFirmaAPI(TEST_IFIRMA_USER, TEST_IFIRMA_INVOICE_KEY, TEST_IFIRMA_USER_KEY)
```
2. Create invoice parameters

```python

    client = Client(
        "Dariusz",
        "1231231212",
        Address(
            "Warszawa", 
            "03-185"
        ),
        email="email@server.com",
    )
    
    position = Position(
        VAT.VAT_23, 
        1, 
        1000, 
        "nazwa", 
        "szt"
    )
```
3. Create invoice in iFirma service and get it's id

```python
invoice = NewInvoiceParams(client, [position])
invoice_id = ifirma_client.generate_invoice(invoice)
```

That's all folks