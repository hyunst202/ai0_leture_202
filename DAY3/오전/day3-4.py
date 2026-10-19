from abc import ABC, abstractmethod

class PaymentGateway(ABC)
    @abstractmethod
    def process_payment(self,item:str, amount:int) -> str:

class  CreditCardGateway(PaymentGateway):
    def process_payment(self, item, amount):
        return f'구매품목2 : {item} 수량2 : {amount}'

class BankGateway(PaymentGateway):
    pass

obj = BankGateway()

